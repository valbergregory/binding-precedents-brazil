"""Step 2.2 — load data/raw/stj_integras/{metadata,texts} into DuckDB (`documents`, `documents_raw_text`).

Usage:  python scripts/05_load_integras.py [--resume] [--from 2022-08-01 --to 2024-08-31]
Idempotent: INSERT ... ON CONFLICT DO NOTHING on seq_documento; a key already fully loaded (per `load_log`) is skipped.
Texts are stored exactly as decoded from the ZIP (no normalisation; that is `documents_text`, later).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime
from pathlib import Path

import duckdb
import polars as pl
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "python"))
from bpb.integras import iter_texts, key_of, load_salt, read_metadata
from bpb.manifest import read_manifest

CFG = yaml.safe_load((ROOT / "config" / "config.yml").read_text(encoding="utf-8"))
RAW = ROOT / CFG["paths"]["raw"] / "stj_integras"
DB = ROOT / CFG["paths"]["duckdb"]
DOC_COLS = ["seq_documento", "publication_date", "document_type", "numero_registro", "case_label", "class_sigla", "class_number",
            "date_received", "date_distributed", "reporter_hash", "internal_appeal", "outcome_label", "monocratic_summary",
            "subject_codes", "source_file", "source_sha256"]
DOC_SCHEMA = {"seq_documento": pl.Int64, "publication_date": pl.Date, "document_type": pl.Utf8, "numero_registro": pl.Utf8, "case_label": pl.Utf8,
              "class_sigla": pl.Utf8, "class_number": pl.Int64, "date_received": pl.Date, "date_distributed": pl.Date, "reporter_hash": pl.Utf8,
              "internal_appeal": pl.Utf8, "outcome_label": pl.Utf8, "monocratic_summary": pl.Utf8, "subject_codes": pl.Utf8, "source_file": pl.Utf8, "source_sha256": pl.Utf8}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--from", dest="d0", default=None)
    ap.add_argument("--to", dest="d1", default=None)
    a = ap.parse_args()
    salt = load_salt()
    sha = {Path(r["local_path"]).name: r["sha256"] for r in read_manifest()}
    con = duckdb.connect(str(DB))
    con.execute("CREATE TABLE IF NOT EXISTS load_log (key VARCHAR PRIMARY KEY, meta_rows INTEGER, text_rows INTEGER, text_without_meta INTEGER, seconds DOUBLE, loaded_at TIMESTAMP)")
    done = {r[0] for r in con.execute("SELECT key FROM load_log").fetchall()}
    metas = {key_of(p.name): p for p in (RAW / "metadata").glob("metadados*.json")}
    zips = {key_of(p.name): p for p in (RAW / "texts").glob("textos*.zip")}
    keys = sorted(set(metas) & set(zips))
    if a.d0 and a.d1:
        d0, d1 = date.fromisoformat(a.d0), date.fromisoformat(a.d1)
        keys = [k for k in keys if (len(k) == 8 and d0 <= date(int(k[:4]), int(k[4:6]), int(k[6:])) <= d1) or (len(k) == 6 and d0.strftime("%Y%m") <= k <= d1.strftime("%Y%m"))]
    todo = [k for k in keys if k not in done]
    print(f"keys with both files: {len(keys)} | already loaded: {len(keys) - len(todo)} | to load: {len(todo)}")
    t_all = time.time()
    for i, k in enumerate(todo, 1):
        t0 = time.time()
        docs = read_metadata(metas[k], salt, sha.get(metas[k].name, ""))
        if docs:
            df_docs = pl.DataFrame(docs, schema=DOC_SCHEMA, orient="row")
            con.register("df_docs", df_docs)
            con.execute(f"INSERT INTO documents ({', '.join(DOC_COLS)}) SELECT {', '.join(DOC_COLS)} FROM df_docs ON CONFLICT DO NOTHING")
            con.unregister("df_docs")
        have = {d["seq_documento"] for d in docs}  # texts belong to the same key's metadata; anything else is an orphan
        rows, orphans = [], 0
        for seq, text, digest in iter_texts(zips[k]):
            if seq in have:
                rows.append([seq, text, digest])
            else:
                orphans += 1  # text without metadata row: cannot satisfy the FK; counted, not loaded
        if rows:
            df_txt = pl.DataFrame(rows, schema={"seq_documento": pl.Int64, "raw_text": pl.Utf8, "raw_sha256": pl.Utf8}, orient="row")
            con.register("df_txt", df_txt)
            con.execute("INSERT INTO documents_raw_text (seq_documento, raw_text, raw_sha256) SELECT seq_documento, raw_text, raw_sha256 FROM df_txt ON CONFLICT DO NOTHING")
            con.unregister("df_txt")
        con.execute("INSERT OR REPLACE INTO load_log VALUES (?, ?, ?, ?, ?, now())", [k, len(docs), len(rows), orphans, round(time.time() - t0, 2)])
        if i % 25 == 0 or i == len(todo):
            print(f"[{i}/{len(todo)}] {k}: {len(docs)} docs, {len(rows)} texts | {(time.time() - t_all) / 60:.1f} min", flush=True)
    tot = con.execute("SELECT (SELECT count(*) FROM documents), (SELECT count(*) FROM documents_raw_text), (SELECT min(publication_date) FROM documents), (SELECT max(publication_date) FROM documents)").fetchone()
    by_month = con.execute("SELECT strftime(publication_date, '%Y-%m') m, count(*) n, sum((t.seq_documento IS NOT NULL)::int) with_text FROM documents d LEFT JOIN documents_raw_text t USING (seq_documento) GROUP BY 1 ORDER BY 1").fetchall()
    con.close()
    log = {"run_at": datetime.now().isoformat(timespec="seconds"), "keys_loaded_this_run": len(todo), "documents": tot[0], "texts": tot[1],
           "publication_range": [str(tot[2]), str(tot[3])], "by_month": [{"month": m, "documents": n, "with_text": w} for m, n, w in by_month],
           "minutes": round((time.time() - t_all) / 60, 1)}
    (ROOT / "logs").mkdir(exist_ok=True)
    (ROOT / "logs" / "05_load_integras.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in log.items() if k != "by_month"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
