"""Step 2.4 — run the regex extractor (bpb.citations) over `documents_raw_text` and fill `citations`.

Usage:  python scripts/07_extract_citations.py [--extractor-version v1] [--resume]
Writes one row per hit: ref_type in {tema, sumula, paradigma, cpc_regime}; ref_court STJ/STF/TST/NULL (bare, ambiguous).
Idempotent per (document, extractor_version): documents already extracted with this version are skipped.
The regexes are a measurement instrument (CLAUDE.md §12): version them, never tune them on the gold set.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import duckdb
import polars as pl
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "python"))
from bpb.citations import RX_CPC_REGIME, RX_PARADIGMA, RX_SUMULA, find_theme_hits

CFG = yaml.safe_load((ROOT / "config" / "config.yml").read_text(encoding="utf-8"))
DB = ROOT / CFG["paths"]["duckdb"]


def hits_for(text: str) -> list[tuple]:
    out = []
    for h in find_theme_hits(text):
        out.append(("tema", h.court, h.number, text[h.start:h.end], h.start, h.end))
    for m in RX_SUMULA.finditer(text):
        out.append(("sumula", (m.group(3) or "").upper() or None, int(m.group(2)), m.group(0), m.start(), m.end()))
    for m in RX_PARADIGMA.finditer(text):
        out.append(("paradigma", None, int(m.group(2).replace(".", "")), m.group(0), m.start(), m.end()))
    for m in RX_CPC_REGIME.finditer(text):
        out.append(("cpc_regime", None, int(m.group(1).replace(".", "")), m.group(0), m.start(), m.end()))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--extractor-version", default="v1")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--batch", type=int, default=2000)
    a = ap.parse_args()
    ver = a.extractor_version
    con = duckdb.connect(str(DB))
    con.execute("CREATE TABLE IF NOT EXISTS citations_done (seq_documento BIGINT, extractor_version VARCHAR, n_hits INTEGER, PRIMARY KEY (seq_documento, extractor_version))")
    next_id = (con.execute("SELECT coalesce(max(citation_id), 0) FROM citations").fetchone()[0] or 0) + 1
    pending = [r[0] for r in con.execute(
        "SELECT t.seq_documento FROM documents_raw_text t LEFT JOIN citations_done d ON d.seq_documento = t.seq_documento AND d.extractor_version = ? WHERE d.seq_documento IS NULL ORDER BY 1", [ver]).fetchall()]
    print(f"extractor {ver}: {len(pending)} documents pending")
    t_all, n_rows, n_docs = time.time(), 0, 0
    for i in range(0, len(pending), a.batch):
        ids = pending[i:i + a.batch]
        rows = con.execute(f"SELECT seq_documento, raw_text FROM documents_raw_text WHERE seq_documento IN ({', '.join(map(str, ids))})").fetchall()
        cit, done = [], []
        for seq, text in rows:
            hs = hits_for(text or "")
            for ref_type, court, num, label, s, e in hs:
                cit.append([next_id, seq, ref_type, court, num, label[:200], s, e, ver])
                next_id += 1
            done.append([seq, ver, len(hs)])
        if cit:
            df_cit = pl.DataFrame(cit, schema={"citation_id": pl.Int64, "seq_documento": pl.Int64, "ref_type": pl.Utf8, "ref_court": pl.Utf8, "ref_number": pl.Int64,
                                               "ref_label": pl.Utf8, "char_start": pl.Int64, "char_end": pl.Int64, "extractor_version": pl.Utf8}, orient="row")
            con.register("df_cit", df_cit)
            con.execute("INSERT INTO citations SELECT * FROM df_cit")
            con.unregister("df_cit")
        df_done = pl.DataFrame(done, schema={"seq_documento": pl.Int64, "extractor_version": pl.Utf8, "n_hits": pl.Int64}, orient="row")
        con.register("df_done", df_done)
        con.execute("INSERT OR REPLACE INTO citations_done SELECT * FROM df_done")
        con.unregister("df_done")
        n_rows += len(cit)
        n_docs += len(done)
        print(f"[{min(i + a.batch, len(pending))}/{len(pending)}] +{len(cit)} citations | {(time.time() - t_all) / 60:.1f} min", flush=True)
    summary = con.execute("SELECT ref_type, coalesce(ref_court, 'NULL') c, count(*) n, count(DISTINCT seq_documento) docs FROM citations WHERE extractor_version = ? GROUP BY 1, 2 ORDER BY 1, 2", [ver]).fetchall()
    con.close()
    log = {"run_at": datetime.now().isoformat(timespec="seconds"), "extractor_version": ver, "documents_processed": n_docs, "citations_added": n_rows,
           "totals_by_type_court": [{"ref_type": t, "ref_court": c, "citations": n, "documents": d} for t, c, n, d in summary], "minutes": round((time.time() - t_all) / 60, 1)}
    (ROOT / "logs").mkdir(exist_ok=True)
    (ROOT / "logs" / "07_extract_citations.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(json.dumps(log, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
