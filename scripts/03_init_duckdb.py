"""Create (or migrate) the DuckDB database from the numbered files in sql/.

Usage (Terminal):  python scripts/03_init_duckdb.py
Safe to re-run: every statement in sql/ uses IF NOT EXISTS.
"""
import sys
from pathlib import Path

import duckdb
import yaml

ROOT = Path(__file__).resolve().parents[1]
cfg = yaml.safe_load((ROOT / "config" / "config.yml").read_text(encoding="utf-8"))
db_path = ROOT / cfg["paths"]["duckdb"]
db_path.parent.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(db_path))
for sql_file in sorted((ROOT / "sql").glob("[0-9][0-9][0-9]_*.sql")):
    con.execute(sql_file.read_text(encoding="utf-8"))
    print(f"applied {sql_file.name}")
tables = con.execute("select table_name from information_schema.tables where table_schema='main' order by 1").fetchall()
print("tables:", ", ".join(t[0] for t in tables))
con.close()
print(f"database: {db_path}")
sys.exit(0)
