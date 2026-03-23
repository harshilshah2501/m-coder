"""
Manifest models — M3.12 narrow repo-aware context.

Deterministic structures for documentation ingestion and manifest generation.
No wall-clock or identity-bearing timestamp fields; equality is content/revision based.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class SectionRange:
    """Bounded section (1-based inclusive line range)."""

    start_line: int
    end_line: int


@dataclass
class ManifestEntry:
    """
    Single file entry in a repo manifest.

    All fields are deterministic for the given file content and path.
    """

    path: str  # repo-relative, POSIX-style
    content_hash: str  # e.g. SHA-256 hex of normalized content
    file_type: str  # "markdown", "python", "text", etc.
    title: str = ""  # first H1 or filename
    headings: List[str] = field(default_factory=list)  # ordered heading strings
    section_ranges: List[SectionRange] = field(default_factory=list)
    symbol_anchors: List[str] = field(default_factory=list)  # e.g. "def foo", "class Bar"


@dataclass
class RepoManifest:
    """
    Deterministic manifest for a repo revision.

    Identity and equality are determined by revision and entries only.
    No built_at_utc or other wall-clock fields.
    """

    revision: str
    entries: List[ManifestEntry] = field(default_factory=list)

    def entry_by_path(self, path: str) -> ManifestEntry | None:
        """Return the entry for the given path or None."""
        for e in self.entries:
            if e.path == path:
                return e
        return None

    def paths(self) -> List[str]:
        """Return sorted list of all paths."""
        return sorted(e.path for e in self.entries)


@dataclass
class IngestionConfig:
    """
    Configuration for which paths to ingest.

    path_patterns: list of glob-style patterns relative to repo root, e.g.:
      - "docs/**/*.md"
      - "docs/runtime/**"
      - "runtime/context/*.py"
      - "README.md"
    """

    path_patterns: List[str] = field(default_factory=list)

    @classmethod
    def default_docs_and_runtime(cls) -> IngestionConfig:
        """Default allowlist: docs, runtime context, root README."""
        return cls(
            path_patterns=[
                "docs/**/*.md",
                "docs/runtime/**",
                "runtime/context/*.py",
                "README.md",
            ]
        )
