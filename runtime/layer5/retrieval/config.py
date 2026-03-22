"""
Retrieval configuration (weights and safety limits).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LexicalRetrievalConfig:
    """
    MVP lexical ranking parameters — keep linear and explainable.

    Scoring (see ``lexical.py``): integer sum of weighted substring counts.
    """

    min_token_len: int = 2
    max_content_bytes: int = 262_144
    """Cap per file when reading content for keyword counts (honest bound)."""
    read_file_contents: bool = True
    weight_path: int = 1
    weight_basename: int = 2
    """Extra weight on matches in the file name segment (basename still appears in path)."""
    weight_content: int = 1
