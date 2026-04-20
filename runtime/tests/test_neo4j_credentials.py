from __future__ import annotations

from pathlib import Path

import pytest

from runtime.neo4j_credentials import neo4j_password_from_env, read_neo4j_password_file


def test_read_neo4j_password_file_first_line(tmp_path):
    p = tmp_path / "neo4j.secret"
    p.write_text("line-one\nignored\n", encoding="utf-8")
    p.chmod(0o600)
    assert read_neo4j_password_file(str(p)) == "line-one"


def test_neo4j_password_from_env_prefers_file(monkeypatch, tmp_path):
    p = tmp_path / "f"
    p.write_text("from-file\n", encoding="utf-8")
    p.chmod(0o600)
    monkeypatch.setenv("MOTADATA_NEO4J_PASSWORD_FILE", str(p))
    monkeypatch.setenv("MOTADATA_NEO4J_PASSWORD", "from-env")
    assert neo4j_password_from_env() == "from-file"


def test_neo4j_password_from_env_plain_fallback(monkeypatch):
    monkeypatch.delenv("MOTADATA_NEO4J_PASSWORD_FILE", raising=False)
    monkeypatch.setenv("MOTADATA_NEO4J_PASSWORD", "plain")
    assert neo4j_password_from_env() == "plain"


def test_read_empty_file_raises(tmp_path):
    p = tmp_path / "empty"
    p.write_text("\n\n", encoding="utf-8")
    p.chmod(0o600)
    with pytest.raises(ValueError):
        read_neo4j_password_file(str(p))
