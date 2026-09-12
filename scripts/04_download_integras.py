"""Step 2.1 — bring the STJ íntegras (metadata + texts) for a publication window into data/raw/stj_integras/.

Usage:  python scripts/04_download_integras.py --from 2022-08-01 --to 2024-08-31 [--resume] [--mirror DIR] [--no-mirror]

Provenance rules (CLAUDE.md, bpb.manifest): every file gets a MANIFEST.csv row with the CKAN URL, sha256 and size.
Two channels, in this order:
  1. local mirror (default: ../STJ-Moral-Damages-Jurimetrics/data/raw/stj_integras, downloaded from the same CKAN
     resources on 2026-09-07/08 with CHECKSUMS.sha256): the file is copied, its sha256 is verified against the mirror
     checksum list, and the manifest row records the original CKAN URL with notes="copied from local mirror";
  2. otherwise bpb.manifest.download (network), resumable.
The CKAN listing (package_show) is fetched once per run and cached in data/raw/stj_integras/package_show.json.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "python"))
from bpb.integras import key_of
from bpb.manifest import ManifestRow, _append_row, already_have, download, sha256_of

CFG = yaml.safe_load((ROOT / "config" / "config.yml").read_text(encoding="utf-8"))
SRC = yaml.safe_load((ROOT / "config" / "sources.yml").read_text(encoding="utf-8"))["stj_integras_decisoes"]
RAW = ROOT / CFG["paths"]["raw"] / "stj_integras"
DEFAULT_MIRROR = ROOT.parent / "STJ-Moral-Damages-Jurimetrics" / "data" / "raw" / "stj_integras"


def key_in_window(key: str, d0: date, d1: date) -> bool:
    """Daily key YYYYMMDD inside [d0, d1]; monthly key YYYYMM if the month overlaps the window."""
    if len(key) == 8:
        return d0 <= date(int(key[:4]), int(key[4:6]), int(key[6:])) <= d1
    y, m = int(key[:4]), int(key[4:])
    return date(y, m, 1) <= d1 and date(y, m, 28) >= d0


def ckan_resources() -> list[dict]:
    RAW.mkdir(parents=True, exist_ok=True)
    cache = RAW / "package_show.json"
    r = requests.get(SRC["ckan_package_show"], headers={"User-Agent": CFG["download"]["user_agent"]}, timeout=120)
    r.raise_for_status()
    cache.write_text(r.text, encoding="utf-8")
    return r.json()["result"]["resources"]


def mirror_checksums(mirror: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for sub in ("metadata", "texts"):
        f = mirror / sub / "CHECKSUMS.sha256"
        if f.exists():
            for ln in f.read_text(encoding="utf-8").splitlines():
                parts = ln.split()
                if len(parts) >= 2:
                    out[parts[-1]] = parts[0]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="d0", required=True)
    ap.add_argument("--to", dest="d1", required=True)
    ap.add_argument("--resume", action="store_true", help="skip files already in the manifest (default behaviour anyway)")
    ap.add_argument("--mirror", default=str(DEFAULT_MIRROR))
    ap.add_argument("--no-mirror", action="store_true")
    a = ap.parse_args()
    d0, d1 = date.fromisoformat(a.d0), date.fromisoformat(a.d1)
    mirror = None if a.no_mirror else Path(a.mirror)
    sums = mirror_checksums(mirror) if mirror and mirror.exists() else {}

    res = ckan_resources()
    wanted = []
    for r in res:
        name = (r.get("name") or "").strip()
        fmt = (r.get("format") or "").upper()
        key = key_of(name)
        if not key or not key_in_window(key, d0, d1):
            continue
        if fmt == "JSON" or name.startswith("metadados"):
            wanted.append(("metadata", key, f"metadados{key}.json", r["url"], r.get("last_modified") or ""))
        elif fmt == "ZIP" or name.endswith(".zip"):  # 202202.zip is published with an empty format
            wanted.append(("texts", key, f"textos{key}.zip", r["url"], r.get("last_modified") or ""))
    # keep the newest resource per (kind, key)
    latest: dict[tuple[str, str], tuple] = {}
    for w in wanted:
        if (w[0], w[1]) not in latest or w[4] > latest[(w[0], w[1])][4]:
            latest[(w[0], w[1])] = w
    wanted = sorted(latest.values(), key=lambda w: (w[1], w[0]))
    print(f"window {d0}..{d1}: {len(wanted)} resources ({sum(w[0] == 'metadata' for w in wanted)} metadata, {sum(w[0] == 'texts' for w in wanted)} zip)")

    n_copied = n_downloaded = n_skipped = n_failed = 0
    for kind, key, fname, url, last_mod in wanted:
        if already_have(url):
            n_skipped += 1
            continue
        target_dir = RAW / kind
        target_dir.mkdir(parents=True, exist_ok=True)
        src = mirror / kind / fname if mirror else None
        if src and src.exists():
            target = target_dir / fname
            shutil.copyfile(src, target)
            digest = sha256_of(target)
            expected = sums.get(fname)
            if expected and expected != digest:
                target.unlink()
                print(f"CHECKSUM MISMATCH for {fname} in mirror; will download", file=sys.stderr)
            else:
                _append_row(ManifestRow(
                    downloaded_at_utc=datetime.now(UTC).isoformat(timespec="seconds"),
                    source_key="stj_integras_decisoes", resource_key=fname, url=url,
                    local_path=str(target.relative_to(ROOT)).replace("\\", "/"), sha256=digest,
                    size_bytes=target.stat().st_size, license=SRC["license"], filters=f"{d0}..{d1}",
                    source_version=last_mod, http_status=0,
                    notes="copied from local mirror (STJ-Moral-Damages-Jurimetrics, CKAN download of 2026-09-07/08; sha256 verified against mirror CHECKSUMS)" if expected else "copied from local mirror (no mirror checksum available)",
                ))
                n_copied += 1
                continue
        try:
            download(url, "stj_integras_decisoes", fname, f"stj_integras/{kind}", fname, SRC["license"], filters=f"{d0}..{d1}", source_version=last_mod)
            n_downloaded += 1
        except Exception as e:  # noqa: BLE001
            n_failed += 1
            print(f"FAILED {fname}: {e}", file=sys.stderr)
    log = {"run_at": datetime.now().isoformat(timespec="seconds"), "window": [str(d0), str(d1)], "resources": len(wanted),
           "copied_from_mirror": n_copied, "downloaded": n_downloaded, "already_in_manifest": n_skipped, "failed": n_failed}
    (ROOT / "logs").mkdir(exist_ok=True)
    (ROOT / "logs" / "04_download_integras.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(json.dumps(log, indent=1))
    return 1 if n_failed else 0


if __name__ == "__main__":
    sys.exit(main())
