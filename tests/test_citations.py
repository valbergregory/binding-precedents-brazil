"""Unit tests for the regex extractors on synthetic strings (no real data required)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "python"))

from bpb.citations import cites_theme, find_theme_hits, signal_summary  # noqa: E402
from bpb.origin import court_from_cnj_number, court_from_text  # noqa: E402


def test_theme_with_stj_context():
    t = "conforme decidido no Tema 1.076/STJ, e ainda o Tema Repetitivo n. 905 do STJ"
    hits = list(find_theme_hits(t))
    assert {(h.number, h.court) for h in hits} == {(1076, "STJ"), (905, "STJ")}


def test_theme_with_stf_context_and_bare():
    t = "aplicando o Tema 1234 de repercussão geral do STF; ver também Tema 339."
    hits = {(h.number, h.court) for h in find_theme_hits(t)}
    assert (1234, "STF") in hits
    assert (339, None) in hits


def test_cites_theme_requires_court_when_asked():
    t = "Tema 1199 (STF)."  # parenthesis breaks the STF context pattern on purpose
    assert cites_theme(t, 1199)            # bare hit
    assert not cites_theme(t, 1199, "STJ")


def test_signal_summary_flags():
    t = "Súmula 7/STJ. REsp 1.234.567/SP. art. 1.036 do CPC. Impõe-se a distinção do caso."
    s = signal_summary(t)
    assert s["n_sumula"] == 1 and s["n_paradigma"] == 1 and s["cpc_regime"] and s["distincao"]


def test_origin_from_cnj_number():
    assert court_from_cnj_number("6917935-02.2009.8.13.0024")["court"] == "TJMG"
    assert court_from_cnj_number("00008323520184013202")["court"] == "TRF1"
    assert court_from_cnj_number("02721312420263000000")["court"] == "STJ"


def test_origin_from_text():
    t = "DECISÃO<br>Trata-se de agravo contra decisão do TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO, que não admitiu"
    assert court_from_text(t)["court"] == "TJSP"
    t2 = "acórdão do Tribunal Regional Federal da 4ª Região assim ementado"
    assert court_from_text(t2)["court"] == "TRF4"
    assert court_from_text("nada aqui") is None
