"""Download the STJ qualified-precedent registry (temas.csv, processos.csv and dictionaries)
into data/raw/stj_precedentes/ with manifest rows. Idempotent; re-run to check for updates
(a changed upstream file is stored as a new version, the old one is kept).

Usage (Terminal or Background Job):  python scripts/02_download_precedent_registry.py
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "python"))
from bpb.manifest import download  # noqa: E402

if __name__ == "__main__":
    src = yaml.safe_load((ROOT / "config" / "sources.yml").read_text(encoding="utf-8"))
    s = src["stj_precedentes_qualificados"]
    for key, url in s["resources"].items():
        p = download(url=url, source_key="stj_precedentes_qualificados", resource_key=key,
                     subdir="stj_precedentes", filename=url.rsplit("/", 1)[-1],
                     license=s["license"], filters="none (full file)",
                     source_version=str(s["observed"].get("last_modified", "")))
        print(f"ok  {key:22s} -> {p.relative_to(ROOT)}  ({p.stat().st_size:,} bytes)")
