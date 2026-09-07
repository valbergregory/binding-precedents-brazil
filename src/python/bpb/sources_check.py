"""Reachability check for every URL declared in config/sources.yml.

Writes logs/source_checks/<UTC timestamp>.csv with url, HTTP status, content type and bytes.
Only HEAD/GET requests without side effects. The DataJud probe is skipped unless the
DATAJUD_API_KEY environment variable is set (the key is public but is not stored in the repo).
"""
from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
import urllib3
import yaml

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT = Path(__file__).resolve().parents[3]
UA = "Mozilla/5.0 (research crawler; binding-precedents-brazil)"


def _walk_urls(node, prefix=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk_urls(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_urls(v, f"{prefix}[{i}]")
    elif isinstance(node, str) and node.startswith("http"):
        yield prefix, node.split("#")[0].strip()


def check_all(timeout: int = 30) -> Path:
    cfg = yaml.safe_load((ROOT / "config" / "sources.yml").read_text(encoding="utf-8"))
    out_dir = ROOT / "logs" / "source_checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = out_dir / f"{stamp}.csv"
    rows = []
    for key, url in _walk_urls(cfg):
        if "download/" in url and url.endswith((".zip", ".gz")):
            method = "HEAD"
        else:
            method = "GET"
        try:
            try:
                r = requests.request(method, url, headers={"User-Agent": UA}, timeout=timeout,
                                     stream=True, allow_redirects=True)
                note = ""
            except requests.exceptions.SSLError:
                # Some .jus.br hosts (STF) serve an incomplete certificate chain. Retry without
                # verification for a read-only reachability probe and record that we did so.
                r = requests.request(method, url, headers={"User-Agent": UA}, timeout=timeout,
                                     stream=True, allow_redirects=True, verify=False)
                note = " [incomplete TLS chain: probed with verify=False]"
            status, ctype = r.status_code, r.headers.get("content-type", "") + note
            size = r.headers.get("content-length", "")
            r.close()
        except Exception as e:  # noqa: BLE001
            status, ctype, size = -1, type(e).__name__, ""
        rows.append({"checked_at_utc": stamp, "key": key, "url": url, "method": method,
                     "http_status": status, "content_type": ctype, "content_length": size})
        print(f"{status:>4}  {key}")

    key = os.environ.get("DATAJUD_API_KEY")
    dj_url = "https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search"
    if key:
        try:
            r = requests.post(dj_url, headers={"Authorization": f"ApiKey {key}",
                                               "Content-Type": "application/json",
                                               "User-Agent": UA},
                              json={"size": 1, "query": {"match_all": {}}}, timeout=timeout)
            total = r.json().get("hits", {}).get("total", {}) if r.ok else {}
            rows.append({"checked_at_utc": stamp, "key": "cnj_datajud_api.probe_stj", "url": dj_url,
                         "method": "POST", "http_status": r.status_code,
                         "content_type": r.headers.get("content-type", ""),
                         "content_length": str(total)})
            print(f"{r.status_code:>4}  cnj_datajud_api.probe_stj  hits={total}")
        except Exception as e:  # noqa: BLE001
            rows.append({"checked_at_utc": stamp, "key": "cnj_datajud_api.probe_stj", "url": dj_url,
                         "method": "POST", "http_status": -1, "content_type": type(e).__name__,
                         "content_length": ""})
    else:
        print("skip  cnj_datajud_api.probe_stj (DATAJUD_API_KEY not set)")

    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return out
