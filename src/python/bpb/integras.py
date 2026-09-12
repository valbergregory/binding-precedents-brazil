"""Readers for the STJ open-data *íntegras* files (metadados<key>.json + textos<key>.zip).

Metadata schema drifts across years (documented in the STJ-Moral-Damages sibling project and re-verified here on
2026-09-12): 2021 and 2024+ use `SeqDocumento`, `NM_MINISTRO`, ISO dates (`dataDistribuição` with accent from 2025);
2022–2023 use `seqDocumento`, `ministro` and epoch-millisecond dates; `assuntos` comes as dotted paths
("00899.07681.09580.09596., ..."; 2021 and 2026), ';'-separated leaves (2022–2023) or ', '-separated leaves
(2024–2025). Everything is normalised to the `documents` table layout of sql/001_schema.sql.

Privacy (docs/ETHICS.md §3): the rapporteur's name is never stored — `reporter_hash` is a salted SHA-256 whose salt
lives in `.secrets/salt` (git-ignored, created on first use). Raw texts are stored exactly as decoded from the ZIP.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
import zipfile
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SALT_FILE = ROOT / ".secrets" / "salt"
KEY_RE = re.compile(r"(\d{6,8})")
_LEAF_SPLIT = re.compile(r"[;,]")


def load_salt() -> bytes:
    SALT_FILE.parent.mkdir(exist_ok=True)
    if not SALT_FILE.exists():
        SALT_FILE.write_bytes(os.urandom(32))
    return SALT_FILE.read_bytes()


def strip_accents(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def key_of(name: str) -> str | None:
    m = KEY_RE.search(Path(name).name)
    return m.group(1) if m else None


def _clean(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return None if s in ("", "None", "null") else s


def parse_date(v) -> date | None:
    """ISO 'YYYY-MM-DD[...]' or epoch milliseconds → date in Brasília local time."""
    s = _clean(v)
    if s is None:
        return None
    if s.isdigit() and len(s) >= 11:
        return (datetime.fromtimestamp(int(s) / 1000, UTC) - timedelta(hours=3)).date()
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def parse_subject_codes(raw) -> str | None:
    """Leaf CNJ subject codes as 'a;b;c' (unique, order kept)."""
    s = _clean(raw)
    if s is None:
        return None
    leaves: list[str] = []
    if "." in s:
        for path in s.split(","):
            segs = [x for x in path.strip().split(".") if x]
            if segs:
                leaves.append(segs[-1])
    else:
        leaves = [x.strip() for x in _LEAF_SPLIT.split(s)]
    out: list[str] = []
    for x in leaves:
        if x.isdigit() and str(int(x)) not in out:
            out.append(str(int(x)))
    return ";".join(out) or None


def hash_name(name, salt: bytes) -> str | None:
    s = _clean(name)
    if s is None:
        return None
    return hashlib.sha256(salt + strip_accents(s).upper().encode()).hexdigest()[:24]


def _norm_key(k: str) -> str:
    k = strip_accents(k).lower()
    return {"nm_ministro": "ministro"}.get(k, k)


def read_metadata(path: Path, salt: bytes, source_sha256: str = "") -> list[dict]:
    """One dict per document, keys = columns of the `documents` table."""
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for r in rows:
        r = {_norm_key(k): v for k, v in r.items()}
        seq = _clean(r.get("seqdocumento"))
        if not (seq and seq.isdigit()):
            continue
        processo = _clean(r.get("processo"))
        m = re.match(r"([A-Za-z]+)\s*(\d+)?", processo or "")
        out.append({
            "seq_documento": int(seq),
            "publication_date": parse_date(r.get("datapublicacao")),
            "document_type": strip_accents(_clean(r.get("tipodocumento")) or "").upper() or None,
            "numero_registro": _clean(r.get("numeroregistro")),
            "case_label": processo,
            "class_sigla": m.group(1) if m else None,
            "class_number": int(m.group(2)) if m and m.group(2) else None,
            "date_received": parse_date(r.get("datarecebimento")),
            "date_distributed": parse_date(r.get("datadistribuicao")),
            "reporter_hash": hash_name(r.get("ministro"), salt),
            "internal_appeal": _clean(r.get("recurso")),
            "outcome_label": _clean(r.get("teor")),
            "monocratic_summary": _clean(r.get("descricaomonocratica")),
            "subject_codes": parse_subject_codes(r.get("assuntos")),
            "source_file": Path(path).name,
            "source_sha256": source_sha256,
        })
    return out


def iter_texts(zip_path: Path) -> Iterator[tuple[int, str, str]]:
    """Yield (seq_documento, raw_text, raw_sha256) for every TXT member, text unmodified (UTF-8 decode only)."""
    try:
        z = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile:  # damaged at the source (e.g. textos20260126.zip): counted as zero texts by the loader
        return
    with z:
        for info in z.infolist():
            if info.is_dir() or not info.filename.lower().endswith(".txt"):
                continue
            m = re.search(r"(\d+)", Path(info.filename).name)
            if not m:
                continue
            raw = z.read(info)
            yield int(m.group(1)), raw.decode("utf-8", "replace"), hashlib.sha256(raw).hexdigest()
