"""Booktabs and numbers.tex generation on tiny fixtures (no pipeline outputs needed)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "python"))
from bpb.export_overleaf import csv_to_booktabs, format_number, latex_escape, numbers_to_tex  # noqa: E402


def test_csv_to_booktabs(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("court,n_docs,share\nTJSP,1200,0.35\nTRF4,300,0.09\n", encoding="utf-8")
    tex = csv_to_booktabs(p, caption="A & B", label="tab:t")
    assert r"\begin{tabular}{lrr}" in tex
    assert r"\toprule" in tex and r"\bottomrule" in tex
    assert r"TJSP & 1200 & 0.35 \\" in tex
    assert r"\caption{A \& B}" in tex


def test_numbers_to_tex():
    tex = numbers_to_tex({"nDocs": 24056, "shareCiting": {"value": 0.154, "decimals": 3}})
    assert r"\newcommand{\nDocs}{24\,056}" in tex
    assert r"\newcommand{\shareCiting}{0.154}" in tex
    with pytest.raises(ValueError):
        numbers_to_tex({"n_docs": 1})


def test_escape_and_format():
    assert latex_escape("50% of #1") == r"50\% of \#1"
    assert format_number(1234567.891, 1) == r"1\,234\,567.9"
