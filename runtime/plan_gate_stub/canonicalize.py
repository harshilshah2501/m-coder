"""Canonicalization for deterministic hashing."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonicalize_boundary_phrase(phrase: str) -> bytes:
    """Per boundary_hashing.v0.1: UTF-8, newline normalized."""
    s = phrase.replace("\r\n", "\n").replace("\r", "\n")
    return s.encode("utf-8")


def boundary_phrase_hash(phrase: str) -> str:
    return hashlib.sha256(canonicalize_boundary_phrase(phrase)).hexdigest()


def canonical_json(obj: Any) -> bytes:
    """Stable JSON: sorted keys, UTF-8."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")


def plan_hash(plan: dict) -> str:
    """SHA-256 hex of canonical plan JSON."""
    p = {k: v for k, v in plan.items() if k != "integrity"}
    return hashlib.sha256(canonical_json(p)).hexdigest()


def derive_id(prefix: str, content: bytes) -> str:
    """Deterministic id from content hash."""
    return f"{prefix}-{hashlib.sha256(content).hexdigest()[:32]}"
