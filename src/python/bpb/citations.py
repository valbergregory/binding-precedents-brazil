"""Regex extraction of precedent references from Brazilian decision texts.

These patterns were exercised on 24,056 STJ documents from nine publication days
(2023-05-10, four days of 2024 and four days of 2025) during Phase 0. They are a first
version: recall and precision must be measured against the gold standard (Phase 4) and
against the structured `tema` field of the STJ espelhos (Phase 3). Treat every hit as a
candidate, not as a fact.

Disambiguation rule: a bare "Tema 1199" is ambiguous because STJ and STF theme numbers
overlap. A hit is attributed to a court only when the surrounding context names it
(STJ / repetitivo / REsp vs STF / repercussão geral / RG). Bare hits are kept with court=None.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator, Optional

_NUM = r"(?:n[º°.o]?\s*)?"

# "Tema 1.076" or "Tema 1076"; the dot is a thousands separator in legal writing.
_TEMA_CORE = rf"Tema\s*(?:Repetitivo\s*)?{_NUM}(\d{{1,2}}\.?\d{{3}}|\d{{1,4}})"

RX_TEMA_STJ = re.compile(
    _TEMA_CORE + r"\s*(?:/|do|da|-|–)?\s*(?:STJ|Superior\s+Tribunal\s+de\s+Justi[çc]a|REsp|"
    r"Repetitiv|dos?\s+Recursos?\s+Repetitivos?)",
    re.IGNORECASE,
)
RX_TEMA_STF = re.compile(
    _TEMA_CORE + r"\s*(?:/|do|da|de|-|–)?\s*(?:STF|Supremo|Repercuss[ãa]o\s+Geral|RG\b)",
    re.IGNORECASE,
)
RX_TEMA_ANY = re.compile(_TEMA_CORE + r"\b", re.IGNORECASE)

# Súmulas: "Súmula 7/STJ", "Súmula n. 83 do STJ", "Súmula Vinculante 10"
RX_SUMULA = re.compile(
    r"S[úu]mula\s*(Vinculante\s*)?" + _NUM + r"(\d{1,3})\s*(?:/|do|da|-)?\s*(STJ|STF|TST)?",
    re.IGNORECASE,
)
# Paradigm appeals: "REsp 1.234.567/SP", "REsp n. 1234567 / RS", "RE 574.706/PR"
RX_PARADIGMA = re.compile(
    r"\b(REsp|AREsp|EREsp|RE|ARE|IAC|PUIL)\s*" + _NUM + r"((?:\d{1,3}\.)*\d{3,7})\s*/?\s*([A-Z]{2})?\b"
)
# CPC provisions that govern the repetitive-appeal and general-repercussion regime.
RX_CPC_REGIME = re.compile(r"art(?:igo|\.)?\s*(1\.?03[6-9]|1\.?040|92[67]|932)\b", re.IGNORECASE)
# Explicit doctrinal moves.
RX_DISTINCAO = re.compile(r"\b(distin[çc][ãa]o|distinguishing|distingu[ei])\b", re.IGNORECASE)
RX_SUPERACAO = re.compile(r"\b(overruling|supera[çc][ãa]o\s+do\s+(?:precedente|entendimento))\b", re.IGNORECASE)


@dataclass(frozen=True)
class ThemeHit:
    number: int
    court: Optional[str]  # "STJ", "STF" or None (bare, ambiguous)
    start: int
    end: int


def _to_int(s: str) -> int:
    return int(s.replace(".", ""))


def find_theme_hits(text: str) -> Iterator[ThemeHit]:
    """Yield every theme mention with its court attribution when the context allows it."""
    attributed: set[tuple[int, int]] = set()
    for court, rx in (("STJ", RX_TEMA_STJ), ("STF", RX_TEMA_STF)):
        for m in rx.finditer(text):
            attributed.add((m.start(), m.end()))
            yield ThemeHit(_to_int(m.group(1)), court, m.start(), m.end())
    for m in RX_TEMA_ANY.finditer(text):
        # skip bare hits that are the prefix of an attributed hit
        if any(a <= m.start() < b for a, b in attributed):
            continue
        yield ThemeHit(_to_int(m.group(1)), None, m.start(), m.end())


def cites_theme(text: str, number: int, court: Optional[str] = None) -> bool:
    """True if `text` mentions theme `number` (optionally requiring court attribution)."""
    for h in find_theme_hits(text):
        if h.number == number and (court is None or h.court == court):
            return True
    return False


def signal_summary(text: str) -> dict:
    """Coarse per-document indicators used for corpus screening (not for classification)."""
    return {
        "n_tema_stj": sum(1 for _ in RX_TEMA_STJ.finditer(text)),
        "n_tema_stf": sum(1 for _ in RX_TEMA_STF.finditer(text)),
        "n_tema_any": sum(1 for _ in RX_TEMA_ANY.finditer(text)),
        "n_sumula": sum(1 for _ in RX_SUMULA.finditer(text)),
        "n_paradigma": sum(1 for _ in RX_PARADIGMA.finditer(text)),
        "cpc_regime": bool(RX_CPC_REGIME.search(text)),
        "distincao": bool(RX_DISTINCAO.search(text)),
        "superacao": bool(RX_SUPERACAO.search(text)),
    }
