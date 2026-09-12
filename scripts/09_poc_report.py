"""Step 2.6 — proof-of-concept report for one STJ theme: measured volumes, citation series and origin coverage.

Usage:  python scripts/09_poc_report.py --tema 1132 [--subject 9582] [--extractor-version v1]
Reads DuckDB (documents, documents_raw_text, citations, cases) and data/raw/stj_precedentes/temas.csv (dates).
Writes docs/08_poc_report.md (counts only; no text excerpts), outputs/tables/poc_*.csv and outputs/numbers.json
(merged; one entry per quoted number). The Gate 1 verdict line is left for the author (docs/07_go_no_go_criteria.md).
Every table with a court/UF breakdown is reported only for cells with k >= 5 (docs/ETHICS.md).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

import duckdb
import yaml

ROOT = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load((ROOT / "config" / "config.yml").read_text(encoding="utf-8"))
DB = ROOT / CFG["paths"]["duckdb"]
TAB = ROOT / "outputs" / "tables"
K_MIN = 5


def tema_dates(n: int) -> dict:
    with open(ROOT / "data" / "raw" / "stj_precedentes" / "temas.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("tipoPrecedente") == "Tema" and r.get("numeroPrecedente") == str(n):
                return {"afetacao": r.get("dataPrimeiraAfetacao") or None, "julgamento": r.get("dataJulgamento") or None,
                        "publicacao": r.get("dataPublicacaoAcordao") or None, "situacao": r.get("situacao"), "orgao": r.get("orgaoJulgador"),
                        "assuntos": r.get("Assuntos")}
    raise SystemExit(f"Tema {n} not found in temas.csv")


_DIGITS = {"0": "Zero", "1": "One", "2": "Two", "3": "Three", "4": "Four", "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine"}


def alpha(n: int) -> str:
    """1132 -> 'OneOneThreeTwo' (LaTeX macro names must be letters only)."""
    return "".join(_DIGITS[d] for d in str(n))


def md_table(rows: list[dict]) -> str:
    if not rows:
        return "_(empty)_"
    cols = list(rows[0].keys())
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    out += ["| " + " | ".join("" if r[c] is None else str(r[c]) for c in cols) + " |" for r in rows]
    return "\n".join(out)


def write_csv(name: str, rows: list[dict]) -> None:
    TAB.mkdir(parents=True, exist_ok=True)
    with open(TAB / name, "w", encoding="utf-8", newline="") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)


def q(con, sql: str, params=None) -> list[dict]:
    cur = con.execute(sql, params or [])
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r, strict=True)) for r in cur.fetchall()]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252
    ap = argparse.ArgumentParser()
    ap.add_argument("--tema", type=int, required=True)
    ap.add_argument("--subject", type=int, default=None, help="CNJ subject code used as the recall-proxy denominator (e.g. 9582 alienação fiduciária)")
    ap.add_argument("--extractor-version", default="v1")
    a = ap.parse_args()
    t = tema_dates(a.tema)
    fix = date.fromisoformat(t["julgamento"]) if t["julgamento"] else None
    ver = a.extractor_version
    con = duckdb.connect(str(DB), read_only=True)

    corpus = q(con, "SELECT count(*) AS documents, count(t.seq_documento) AS with_text, min(publication_date) AS first_day, max(publication_date) AS last_day, count(DISTINCT numero_registro) AS cases FROM documents d LEFT JOIN documents_raw_text t USING (seq_documento)")[0]
    by_type = q(con, "SELECT document_type, count(*) AS documents FROM documents GROUP BY 1 ORDER BY 2 DESC")
    cit = q(con, """SELECT strftime(d.publication_date, '%Y-%m') AS month, count(DISTINCT d.seq_documento) AS documents_total,
                  count(DISTINCT CASE WHEN c.ref_type='tema' AND c.ref_number=? AND c.ref_court='STJ' THEN c.seq_documento END) AS citing_stj_attributed,
                  count(DISTINCT CASE WHEN c.ref_type='tema' AND c.ref_number=? AND c.ref_court IS NULL THEN c.seq_documento END) AS citing_bare,
                  count(DISTINCT CASE WHEN c.ref_type='tema' AND c.ref_number=? AND c.ref_court='STF' THEN c.seq_documento END) AS citing_stf_attributed
           FROM documents d LEFT JOIN citations c ON c.seq_documento = d.seq_documento AND c.extractor_version = ?
           GROUP BY 1 ORDER BY 1""", [a.tema, a.tema, a.tema, ver])
    tot_cit = q(con, """SELECT count(DISTINCT seq_documento) AS citing_docs, count(DISTINCT CASE WHEN ref_court='STJ' THEN seq_documento END) AS citing_docs_stj,
                       count(*) AS mentions FROM citations WHERE ref_type='tema' AND ref_number=? AND extractor_version=?""", [a.tema, ver])[0]
    pre_post = q(con, """SELECT CASE WHEN d.publication_date < ? THEN 'pre' ELSE 'post' END AS period, count(DISTINCT d.seq_documento) AS documents,
                      count(DISTINCT CASE WHEN c.ref_court='STJ' THEN c.seq_documento END) AS citing_stj, count(DISTINCT c.seq_documento) AS citing_any
               FROM documents d LEFT JOIN citations c ON c.seq_documento=d.seq_documento AND c.ref_type='tema' AND c.ref_number=? AND c.extractor_version=?
               GROUP BY 1 ORDER BY 1 DESC""", [fix, a.tema, ver]) if fix else []
    subj = []
    if a.subject:
        subj = q(con, """SELECT CASE WHEN d.publication_date < ? THEN 'pre' ELSE 'post' END AS period, count(DISTINCT d.seq_documento) AS subject_documents,
                      count(DISTINCT c.seq_documento) AS citing_theme, round(100.0 * count(DISTINCT c.seq_documento) / nullif(count(DISTINCT d.seq_documento), 0), 1) AS pct
               FROM documents d LEFT JOIN citations c ON c.seq_documento=d.seq_documento AND c.ref_type='tema' AND c.ref_number=? AND c.extractor_version=?
               WHERE d.subject_codes IS NOT NULL AND (';' || d.subject_codes || ';') LIKE ? GROUP BY 1 ORDER BY 1 DESC""",
                 [fix, a.tema, ver, f"%;{a.subject};%"]) if fix else []
    origin_all = q(con, "SELECT coalesce(origin_channel, 'none') AS channel, count(*) AS cases, round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct FROM cases GROUP BY 1 ORDER BY 2 DESC")
    origin_cit = q(con, """SELECT coalesce(k.origin_channel, 'none') AS channel, count(DISTINCT k.numero_registro) AS citing_cases
               FROM citations c JOIN documents d USING (seq_documento) JOIN cases k ON k.numero_registro = d.numero_registro
               WHERE c.ref_type='tema' AND c.ref_number=? AND c.extractor_version=? GROUP BY 1 ORDER BY 2 DESC""", [a.tema, ver])
    by_court = q(con, """SELECT k.origin_court_id AS court, CASE WHEN d.publication_date < ? THEN 'pre' ELSE 'post' END AS period, count(DISTINCT k.numero_registro) AS citing_cases
               FROM citations c JOIN documents d USING (seq_documento) JOIN cases k ON k.numero_registro = d.numero_registro
               WHERE c.ref_type='tema' AND c.ref_number=? AND c.extractor_version=? AND k.origin_court_id IS NOT NULL
               GROUP BY 1, 2 HAVING count(DISTINCT k.numero_registro) >= ? ORDER BY 3 DESC""", [fix, a.tema, ver, K_MIN]) if fix else []
    signals = q(con, "SELECT ref_type, count(*) AS mentions, count(DISTINCT seq_documento) AS documents FROM citations WHERE extractor_version=? GROUP BY 1 ORDER BY 2 DESC", [ver])
    con.close()

    write_csv(f"poc_tema{a.tema}_monthly_citations.csv", cit)
    write_csv(f"poc_tema{a.tema}_pre_post.csv", pre_post)
    write_csv(f"poc_tema{a.tema}_subject_recall_proxy.csv", subj)
    write_csv("poc_origin_coverage.csv", origin_all)
    write_csv(f"poc_tema{a.tema}_origin_by_court.csv", by_court)
    write_csv("poc_signal_totals.csv", signals)

    numbers_path = ROOT / "outputs" / "numbers.json"
    numbers = json.loads(numbers_path.read_text(encoding="utf-8")) if numbers_path.exists() else {}
    numbers.update({
        "pocCorpusDocuments": {"value": corpus["documents"], "decimals": 0},
        "pocCorpusWithText": {"value": corpus["with_text"], "decimals": 0},
        "pocCorpusCases": {"value": corpus["cases"], "decimals": 0},
        f"pocTema{alpha(a.tema)}CitingDocs": {"value": tot_cit["citing_docs"], "decimals": 0},
        f"pocTema{alpha(a.tema)}CitingDocsStj": {"value": tot_cit["citing_docs_stj"], "decimals": 0},
        f"pocTema{alpha(a.tema)}Mentions": {"value": tot_cit["mentions"], "decimals": 0},
        "pocOriginTextCoveragePct": {"value": round(100 - next((r["pct"] for r in origin_all if r["channel"] == "none"), 0), 1), "decimals": 1},
    })
    numbers_path.parent.mkdir(parents=True, exist_ok=True)
    numbers_path.write_text(json.dumps(numbers, indent=1), encoding="utf-8")

    md = [f"# 08 — Proof-of-concept report: STJ Tema {a.tema}", "",
          f"Generated {datetime.now():%Y-%m-%d %H:%M} by `scripts/09_poc_report.py --tema {a.tema}` (extractor `{ver}`). **Theme choice is provisional**: "
          f"Tema {a.tema} is the primary candidate proposed in docs/02_candidate_precedents.md; the author has not yet confirmed it. Re-run with another `--tema` after the choice.", "",
          f"Registry (data/raw/stj_precedentes/temas.csv): first affetação {t['afetacao']}, judgment **{t['julgamento']}**, acórdão published {t['publicacao']}, status {t['situacao']}, organ {t['orgao']}.",
          f"Pre/post split at the judgment date ({fix}). Subject codes (registry): {t['assuntos']}", "",
          "## 1. Corpus loaded (steps 2.1–2.2)", "",
          f"- Documents: **{corpus['documents']:,}** ({corpus['with_text']:,} with text; {corpus['cases']:,} distinct cases) published {corpus['first_day']} → {corpus['last_day']}.",
          md_table(by_type), "",
          f"## 2. Documents citing Tema {a.tema} (step 2.4, regex `bpb.citations`)", "",
          f"- Documents with ≥1 mention: **{tot_cit['citing_docs']}** ({tot_cit['citing_docs_stj']} with explicit STJ attribution; {tot_cit['mentions']} mentions in total). Bare mentions (“Tema 1132” without court) can refer to the STF theme of the same number — treat as ambiguous until annotated.", "",
          "### Pre/post the judgment date", "", md_table(pre_post), "",
          "### Monthly series", "", md_table(cit), ""]
    if subj:
        md += [f"## 3. Recall proxy: documents whose CNJ subject codes include {a.subject}", "",
               "Share of subject-matched documents that cite the theme (a low share after fixation is either non-citation or regex miss — the manual check of step 6 in docs/05 decides).", "", md_table(subj), ""]
    md += ["## 4. Court of origin (step 2.5, text-only channels; atas not loaded yet)", "",
           "All cases in the corpus:", "", md_table(origin_all), "",
           f"Cases citing Tema {a.tema}:", "", md_table(origin_cit), "",
           f"By origin court and period (cells with k ≥ {K_MIN} only):", "", md_table(by_court), "",
           "## 5. Other regex signals in the corpus", "", md_table(signals), "",
           "## 6. Gate 1", "",
           "Criteria in docs/07_go_no_go_criteria.md. Numbers above are measured; the verdict and the manual checks (200 regex hits for precision, 100 subject-matched non-hits for recall) are the author's — `% AUTHOR DECIDES`.", "",
           "Reproduce: `python scripts/04_download_integras.py --from 2022-08-01 --to 2024-08-31` → `05_load_integras.py` → `07_extract_citations.py` → `08_recover_origin.py` → `09_poc_report.py --tema " + str(a.tema) + (f" --subject {a.subject}" if a.subject else "") + "`."]
    (ROOT / "docs" / "08_poc_report.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md[:12]))
    print("... report: docs/08_poc_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
