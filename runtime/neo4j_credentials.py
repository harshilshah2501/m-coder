"""
Neo4j authentication: optional secret file so passwords are not stored in environment variables.

Prefer MOTADATA_NEO4J_PASSWORD_FILE (first line of file, chmod 600 recommended).
Fallback to MOTADATA_NEO4J_PASSWORD when file is unset or missing.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path


def read_neo4j_password_file(path: str) -> str:
    """Return first non-empty line from path; strip BOM and whitespace."""
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise ValueError(f"not a file: {p}")
    mode = p.stat().st_mode
    if mode & 0o077:
        warnings.warn(
            f"MOTADATA_NEO4J_PASSWORD_FILE should be chmod 600 (mode {oct(mode & 0o777)}): {p}",
            stacklevel=2,
        )
    raw = p.read_text(encoding="utf-8")
    for line in raw.splitlines():
        s = line.strip()
        if s:
            return s
    raise ValueError(f"empty password file: {p}")


def neo4j_password_from_env() -> str:
    """
    Password for Bolt client: file env wins over plain env ( Plan-Gate / indexer ).
    """
    fpath = str(os.environ.get("MOTADATA_NEO4J_PASSWORD_FILE", "")).strip()
    if fpath:
        return read_neo4j_password_file(fpath)
    return str(os.environ.get("MOTADATA_NEO4J_PASSWORD", "")).strip()
