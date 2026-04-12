"""
A6 snippet/evidence configuration (bounded windows only).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SnippetConfig:
    """Deterministic line window around the anchor line (inclusive)."""

    context_lines_before: int = 2
    context_lines_after: int = 2
    max_file_bytes: int = 262_144
    """Must match A5 content cap order-of-magnitude; keeps evidence reads bounded."""
