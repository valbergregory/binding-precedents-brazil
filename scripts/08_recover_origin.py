"""Step 2.5 — recover the court of origin for every case (numero_registro) from the decision texts.

Usage:  python scripts/08_recover_origin.py [--resume]
Channels (bpb.origin.court_from_text): cnj_number_in_text (deterministic J.TR segment), regex_trf, regex_tj.
Rows already filled by a stronger channel (atas / acervo / datajud) are never overwritten. Atas are not loaded yet
(scripts/06 pending authorisation), so coverage here is the text-only lower bound reported in docs/08_poc_report.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import duckdb
import polars as pl
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "python"))
from bpb.origin import _UF_BY_TR_STATE, RX_CNJ, court_from_text

CFG = yaml.safe_load((ROOT / "config" / "config.yml").read_text(encoding="utf-8"))
DB = ROOT / CFG["paths"]["duckdb"]
STRONG = ("atas", "acervo", "datajud")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--batch", type=int, default=5000)
    a = ap.parse_args()
    con = duckdb.connect(str(DB))
    # one text per case: the earliest published document of that numero_registro
    pending = con.execute("""
        SELECT d.numero_registro, min(d.seq_documento) seq, any_value(d.class_sigla) cls, any_value(d.subject_codes) subj
        FROM documents d JOIN documents_raw_text t USING (seq_documento)
        LEFT JOIN cases c ON c.numero_registro = d.numero_registro
        WHERE d.numero_registro IS NOT NULL AND (c.numero_registro IS NULL OR c.origin_channel IS NULL)
        GROUP BY 1 ORDER BY 1""").fetchall()
    print(f"cases pending origin recovery: {len(pending)}")
    # reference list of possible origin courts (state TJs and the six TRFs) so the FK on cases.origin_court_id resolves
    con.executemany("INSERT INTO courts (court_id, name, branch, uf, cnj_j, cnj_tr) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                    [[f"TJ{uf}", f"Tribunal de Justiça ({uf})", "estadual", uf, "8", tr] for tr, uf in _UF_BY_TR_STATE.items()]
                    + [[f"TRF{n}", f"Tribunal Regional Federal da {n}ª Região", "federal", None, "4", f"{n:02d}"] for n in range(1, 7)]
                    + [["STJ", "Superior Tribunal de Justiça", "superior", None, "3", "00"]])
    known = {r[0] for r in con.execute("SELECT court_id FROM courts").fetchall()}
    t_all, stats = time.time(), {"cnj_number_in_text": 0, "regex_trf": 0, "regex_tj": 0, "none": 0}
    for i in range(0, len(pending), a.batch):
        chunk = pending[i:i + a.batch]
        seqs = [r[1] for r in chunk]
        texts = dict(con.execute(f"SELECT seq_documento, raw_text FROM documents_raw_text WHERE seq_documento IN ({', '.join(map(str, seqs))})").fetchall())
        rows = []
        for reg, seq, cls, subj in chunk:
            text = texts.get(seq) or ""
            got = court_from_text(text)
            if got and got["channel"] == "cnj_number_in_text":
                m = RX_CNJ.search(text[:6000])
                got["numero"] = re.sub(r"\D", "", m.group(0)) if m else None
            main_subject = int(subj.split(";")[0]) if subj and subj.split(";")[0].isdigit() else None
            if got:
                court = got.get("court")
                stats[got["channel"]] += 1
                rows.append([reg, got.get("numero"), court if court in known else None, got.get("uf"), got.get("branch"), got["channel"], cls, main_subject])
            else:
                stats["none"] += 1
                rows.append([reg, None, None, None, None, None, cls, main_subject])
        df_cases = pl.DataFrame(rows, schema={"numero_registro": pl.Utf8, "numero_unico_cnj": pl.Utf8, "origin_court_id": pl.Utf8, "origin_uf": pl.Utf8,
                                              "origin_branch": pl.Utf8, "origin_channel": pl.Utf8, "class_sigla": pl.Utf8, "main_subject_code": pl.Int64}, orient="row")  # noqa: F841
        con.register("df_cases", df_cases)
        con.execute("""INSERT INTO cases (numero_registro, numero_unico_cnj, origin_court_id, origin_uf, origin_branch, origin_channel, class_sigla, main_subject_code)
                       SELECT numero_registro, numero_unico_cnj, origin_court_id, origin_uf, origin_branch, origin_channel, class_sigla, main_subject_code FROM df_cases
                       ON CONFLICT (numero_registro) DO UPDATE SET numero_unico_cnj = coalesce(cases.numero_unico_cnj, excluded.numero_unico_cnj),
                         origin_court_id = coalesce(cases.origin_court_id, excluded.origin_court_id), origin_uf = coalesce(cases.origin_uf, excluded.origin_uf),
                         origin_branch = coalesce(cases.origin_branch, excluded.origin_branch), origin_channel = coalesce(cases.origin_channel, excluded.origin_channel),
                         class_sigla = coalesce(cases.class_sigla, excluded.class_sigla), main_subject_code = coalesce(cases.main_subject_code, excluded.main_subject_code)""")
        con.unregister("df_cases")
        print(f"[{min(i + a.batch, len(pending))}/{len(pending)}] {stats} | {(time.time() - t_all) / 60:.1f} min", flush=True)
    cov = con.execute("SELECT coalesce(origin_channel, 'none') ch, count(*) n FROM cases GROUP BY 1 ORDER BY 2 DESC").fetchall()
    con.close()
    log = {"run_at": datetime.now().isoformat(timespec="seconds"), "cases_processed": len(pending), "by_channel_this_run": stats,
           "coverage_all_cases": [{"channel": c, "cases": n} for c, n in cov], "minutes": round((time.time() - t_all) / 60, 1)}
    (ROOT / "logs" / "08_recover_origin.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(json.dumps(log, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
