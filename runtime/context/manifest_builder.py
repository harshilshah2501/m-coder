"""
Manifest builder — M3.12 deterministic documentation ingestion.

Builds a RepoManifest for a given root_path and revision by scanning
approved paths only. No embeddings, no external services.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import List

from runtime.context.manifest_models import (
    IngestionConfig,
    ManifestEntry,
    RepoManifest,
    SectionRange,
)


def _collect_paths(root: Path, config: IngestionConfig) -> List[Path]:
    """
    Collect all file paths under root that match config.path_patterns.
    Returns sorted list of Paths (absolute) for determinism.
    """
    seen: set[str] = set()
    for pattern in sorted(config.path_patterns):
        if "**" in pattern:
            parts = pattern.split("**")
            prefix = parts[0].rstrip("/")
            suffix = parts[-1].lstrip("/") if len(parts) > 1 else "*"
            dir_path = root / prefix if prefix else root
            if not dir_path.exists() or not dir_path.is_dir():
                continue
            for p in sorted(dir_path.rglob(suffix)):
                if p.is_file():
                    rel = p.relative_to(root)
                    key = rel.as_posix()
                    if key not in seen:
                        seen.add(key)
        else:
            # e.g. "runtime/context/*.py" or "README.md"
            if "*" in pattern:
                parent_str, glob_part = pattern.rsplit("/", 1)
                parent = root / parent_str if parent_str else root
                if parent.exists() and parent.is_dir():
                    for child in sorted(parent.glob(glob_part)):
                        if child.is_file():
                            rel = child.relative_to(root)
                            key = rel.as_posix()
                            if key not in seen:
                                seen.add(key)
            else:
                p = root / pattern
                if p.is_file():
                    rel = p.relative_to(root)
                    key = rel.as_posix()
                    if key not in seen:
                        seen.add(key)
    return [root / k for k in sorted(seen)]


def _content_hash(content: str) -> str:
    """Deterministic SHA-256 hex of UTF-8 content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _extract_markdown_headings(content: str) -> tuple[str, List[str], List[SectionRange]]:
    """Extract title (first H1), all headings, and section ranges. 1-based lines."""
    title = ""
    headings: List[str] = []
    section_ranges: List[SectionRange] = []
    line_num = 0
    section_start = 1
    for line in content.splitlines():
        line_num += 1
        m = re.match(r"^(#+)\s+(.+)$", line.strip())
        if m:
            level, text = m.group(1), m.group(2).strip()
            headings.append(text)
            if not title and level == "#":
                title = text
            if section_start <= line_num - 1:
                section_ranges.append(SectionRange(start_line=section_start, end_line=line_num - 1))
            section_start = line_num
    if section_start <= line_num:
        section_ranges.append(SectionRange(start_line=section_start, end_line=line_num))
    return title, headings, section_ranges


def _extract_python_symbols(content: str) -> List[str]:
    """Extract def and class names as symbol anchors. Deterministic order."""
    anchors: List[str] = []
    for m in re.finditer(r"^\s*(def|class)\s+(\w+)", content, re.MULTILINE):
        anchors.append(f"{m.group(1)} {m.group(2)}")
    return anchors


def _build_entry(root: Path, file_path: Path, revision: str) -> ManifestEntry:
    """Build a single ManifestEntry. file_path is absolute."""
    rel = file_path.relative_to(root)
    path_posix = rel.as_posix()
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        content = ""
    content_hash = _content_hash(content)
    suffix = file_path.suffix.lower()
    if suffix == ".md":
        file_type = "markdown"
        title, headings, section_ranges = _extract_markdown_headings(content)
        symbol_anchors = []
        if not title:
            title = file_path.name
    elif suffix == ".py":
        file_type = "python"
        title = file_path.name
        headings = []
        section_ranges = []
        symbol_anchors = _extract_python_symbols(content)
    else:
        file_type = "text"
        title = file_path.name
        headings = []
        section_ranges = []
        symbol_anchors = []
    return ManifestEntry(
        path=path_posix,
        content_hash=content_hash,
        file_type=file_type,
        title=title,
        headings=headings,
        section_ranges=section_ranges,
        symbol_anchors=symbol_anchors,
    )


class ManifestBuilder:
    """
    Builds a deterministic RepoManifest for a repo revision.
    """

    def build(self, root_path: str, revision: str, config: IngestionConfig) -> RepoManifest:
        """
        Scan approved paths under root_path and return RepoManifest.
        Same root_path + revision + config -> same manifest (order, hashes, headings).
        """
        root = Path(root_path).resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError(f"root_path does not exist or is not a directory: {root_path}")
        paths = _collect_paths(root, config)
        entries: List[ManifestEntry] = []
        for p in paths:
            if not p.is_file():
                continue
            try:
                entries.append(_build_entry(root, p, revision))
            except OSError:
                continue
        return RepoManifest(revision=revision, entries=entries)
