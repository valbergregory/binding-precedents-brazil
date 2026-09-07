"""Download files into data/raw and record provenance in data/raw/MANIFEST.csv.

Rules enforced here (see CLAUDE.md):
- a file already present with the same sha256 is never re-downloaded or overwritten;
- a changed upstream file is stored under a new versioned name, and a new manifest row is appended;
- every row records url, download date (UTC), sha256, size, license, filters and source version.
"""
from __future__ import annotations

import csv
import hashlib
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
import yaml

ROOT = Path(__file__).resolve().parents[3]
CONFIG = yaml.safe_load((ROOT / "config" / "config.yml").read_text(encoding="utf-8"))
RAW = ROOT / CONFIG["paths"]["raw"]
MANIFEST = ROOT / CONFIG["paths"]["manifest"]
UA = CONFIG["download"]["user_agent"]

MANIFEST_FIELDS = [
    "downloaded_at_utc", "source_key", "resource_key", "url", "local_path",
    "sha256", "size_bytes", "license", "filters", "source_version", "http_status", "notes",
]


@dataclass
class ManifestRow:
    downloaded_at_utc: str
    source_key: str
    resource_key: str
    url: str
    local_path: str
    sha256: str
    size_bytes: int
    license: str
    filters: str
    source_version: str
    http_status: int
    notes: str = ""


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _append_row(row: ManifestRow) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    new = not MANIFEST.exists()
    with MANIFEST.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        if new:
            w.writeheader()
        w.writerow(asdict(row))


def read_manifest() -> list[dict]:
    if not MANIFEST.exists():
        return []
    with MANIFEST.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def already_have(url: str) -> Optional[dict]:
    """Return the newest manifest row for `url` whose local file still exists and matches its hash."""
    rows = [r for r in read_manifest() if r["url"] == url]
    for r in reversed(rows):
        p = ROOT / r["local_path"]
        if p.exists() and sha256_of(p) == r["sha256"]:
            return r
    return None


def download(
    url: str,
    source_key: str,
    resource_key: str,
    subdir: str,
    filename: str,
    license: str,
    filters: str = "",
    source_version: str = "",
    force: bool = False,
    timeout: int | None = None,
) -> Path:
    """Download `url` into data/raw/<subdir>/<filename>, hash it and append a manifest row.

    Idempotent: if the manifest already has this url with a verified local copy, returns it
    without touching the network (unless force=True). If the upstream bytes differ from the
    stored copy, the new version is saved as <stem>.v<YYYYMMDDTHHMMSS><suffix>; the old file is kept.
    """
    if not force:
        have = already_have(url)
        if have:
            return ROOT / have["local_path"]

    target_dir = RAW / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename
    tmp = target_dir / (filename + ".part")

    timeout = timeout or CONFIG["download"]["timeout_seconds"]
    retries = CONFIG["download"]["max_retries"]
    backoff = CONFIG["download"]["backoff_seconds"]
    status = 0
    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, headers={"User-Agent": UA}, stream=True, timeout=timeout) as r:
                status = r.status_code
                r.raise_for_status()
                with tmp.open("wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            break
        except Exception:
            if attempt == retries:
                if tmp.exists():
                    tmp.unlink()
                raise
            time.sleep(backoff * attempt)

    digest = sha256_of(tmp)
    if target.exists():
        if sha256_of(target) == digest:
            tmp.unlink()
            final = target
        else:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            final = target_dir / f"{target.stem}.v{stamp}{target.suffix}"
            os.replace(tmp, final)
    else:
        os.replace(tmp, target)
        final = target

    _append_row(ManifestRow(
        downloaded_at_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        source_key=source_key,
        resource_key=resource_key,
        url=url,
        local_path=str(final.relative_to(ROOT)).replace("\\", "/"),
        sha256=digest,
        size_bytes=final.stat().st_size,
        license=license,
        filters=filters,
        source_version=source_version,
        http_status=status,
    ))
    return final
