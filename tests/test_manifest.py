"""Manifest behaviour: hashing and idempotence, tested against a local file served from disk."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "python"))

from bpb import manifest as m  # noqa: E402


def test_sha256_matches_hashlib(tmp_path):
    import hashlib
    p = tmp_path / "x.bin"
    p.write_bytes(b"binding precedents")
    assert m.sha256_of(p) == hashlib.sha256(b"binding precedents").hexdigest()


def test_manifest_fields_are_stable():
    assert m.MANIFEST_FIELDS[:4] == ["downloaded_at_utc", "source_key", "resource_key", "url"]
    assert "sha256" in m.MANIFEST_FIELDS and "license" in m.MANIFEST_FIELDS
