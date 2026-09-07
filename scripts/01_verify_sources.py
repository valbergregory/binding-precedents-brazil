"""Verify every source URL in config/sources.yml and log the result.

Usage (Terminal):  python scripts/01_verify_sources.py
Optional: set DATAJUD_API_KEY (public key from the DataJud wiki) to include the API probe.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "python"))
from bpb.sources_check import check_all  # noqa: E402

if __name__ == "__main__":
    out = check_all()
    print(f"\nlog written: {out}")
