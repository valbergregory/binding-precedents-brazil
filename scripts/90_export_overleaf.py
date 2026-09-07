"""Export outputs/ to outputs/overleaf/ (booktabs tables, figures, numbers.tex).

Usage (Terminal):  python scripts/90_export_overleaf.py
Reads only what exists; never fabricates a value.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "python"))
from bpb.export_overleaf import export_all  # noqa: E402

if __name__ == "__main__":
    print(json.dumps(export_all(), indent=2, ensure_ascii=False))
