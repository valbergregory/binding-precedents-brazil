"""Court-of-origin recovery for STJ documents.

Three channels, applied in this order of reliability:
1. CNJ unified number (numeroUnico, from atas de distribuição or acervo em tramitação):
   NNNNNNN-DD.AAAA.J.TR.OOOO -> segment J (branch) and TR (court code).
2. CNJ number found inside the decision text (present in roughly 20% of a sample day).
3. Regex on the opening of the text ("Tribunal de Justiça do Estado de ...",
   "Tribunal Regional Federal da 4ª Região"). Sample coverage in Phase 0: about 36% of
   documents in the first 4,000 characters of a single day; to be re-measured on full texts.

The J.TR -> court map below covers state (J=8) and federal (J=4) courts, which are the
origins relevant to REsp/AREsp. Labour (5), electoral (6), military (7,9) and the STJ's own
originating cases (3.00) are kept as labels for exclusion decisions.
"""
from __future__ import annotations

import re
from typing import Optional

RX_CNJ = re.compile(r"(\d{7})-?(\d{2})\.?(\d{4})\.?(\d)\.?(\d{2})\.?(\d{4})")

_UF_BY_TR_STATE = {
    "01": "AC", "02": "AL", "03": "AP", "04": "AM", "05": "BA", "06": "CE", "07": "DF", "08": "ES",
    "09": "GO", "10": "MA", "11": "MT", "12": "MS", "13": "MG", "14": "PA", "15": "PB", "16": "PR",
    "17": "PE", "18": "PI", "19": "RJ", "20": "RN", "21": "RS", "22": "RO", "23": "RR", "24": "SC",
    "25": "SE", "26": "SP", "27": "TO",
}


def court_from_cnj_number(numero: str) -> Optional[dict]:
    """Map a CNJ unified number to {branch, court, uf}. Returns None if unparsable."""
    m = RX_CNJ.search(numero or "")
    if not m:
        return None
    j, tr = m.group(4), m.group(5)
    if j == "8":
        uf = _UF_BY_TR_STATE.get(tr)
        return {"branch": "estadual", "court": f"TJ{uf}" if uf else None, "uf": uf}
    if j == "4":
        return {"branch": "federal", "court": f"TRF{int(tr)}" if tr.isdigit() else None, "uf": None}
    if j == "3":
        return {"branch": "superior", "court": "STJ" if tr == "00" else None, "uf": None}
    return {"branch": {"1": "stf", "2": "cnj", "5": "trabalho", "6": "eleitoral", "7": "militar_uniao",
                       "9": "militar_estadual"}.get(j, "outro"), "court": None, "uf": None}


RX_TJ = re.compile(
    r"TRIBUNAL DE JUSTI[ÇC]A D[OEA]S?\s+(?:ESTADO\s+D[OEA]\s+)?"
    r"(DISTRITO FEDERAL E DOS TERRIT[ÓO]RIOS|[A-ZÁÉÍÓÚÂÊÔÃÕÇ]+(?:\s+(?:DE|DO|DA|DOS|DAS)?\s*[A-ZÁÉÍÓÚÂÊÔÃÕÇ]+){0,3})",
    re.IGNORECASE,
)
RX_TRF = re.compile(r"TRIBUNAL REGIONAL FEDERAL DA\s+(\d)\s*[ªa°º]?\s*REGI[ÃA]O", re.IGNORECASE)

_STATE_NAME_TO_UF = {
    "ACRE": "AC", "ALAGOAS": "AL", "AMAPA": "AP", "AMAZONAS": "AM", "BAHIA": "BA", "CEARA": "CE",
    "DISTRITO FEDERAL E DOS TERRITORIOS": "DF", "ESPIRITO SANTO": "ES", "GOIAS": "GO",
    "MARANHAO": "MA", "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS", "MINAS GERAIS": "MG",
    "PARA": "PA", "PARAIBA": "PB", "PARANA": "PR", "PERNAMBUCO": "PE", "PIAUI": "PI",
    "RIO DE JANEIRO": "RJ", "RIO GRANDE DO NORTE": "RN", "RIO GRANDE DO SUL": "RS",
    "RONDONIA": "RO", "RORAIMA": "RR", "SANTA CATARINA": "SC", "SAO PAULO": "SP",
    "SERGIPE": "SE", "TOCANTINS": "TO",
}


def _strip_accents(s: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def court_from_text(text: str, window: int = 6000) -> Optional[dict]:
    """Best-effort origin from the opening of an STJ decision. Returns None when nothing matches."""
    head = text[:window]
    m = RX_CNJ.search(head)
    if m:
        got = court_from_cnj_number(m.group(0))
        if got and got.get("court"):
            got["channel"] = "cnj_number_in_text"
            return got
    m = RX_TRF.search(head)
    if m:
        return {"branch": "federal", "court": f"TRF{m.group(1)}", "uf": None, "channel": "regex_trf"}
    m = RX_TJ.search(head)
    if m:
        name = _strip_accents(m.group(1).upper()).strip()
        for state, uf in sorted(_STATE_NAME_TO_UF.items(), key=lambda kv: -len(kv[0])):
            if name.startswith(state):
                return {"branch": "estadual", "court": f"TJ{uf}", "uf": uf, "channel": "regex_tj"}
    return None
