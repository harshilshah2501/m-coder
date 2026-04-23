"""
Bounded snippet extraction — deterministic, no rescoring of A5 results.

Anchor selection (deterministic quality-aware)
---------------------------------------------
Scan physical lines; collect every line where any ``query_tokens`` token appears as
a **substring** of the lowercased line body. Among those candidates, pick the
line with highest **anchor quality score** (domain tokens, code shape, penalties
for copyright/legal/import-only/header zone) — see ``snippet_anchor_quality``.
Tie-break: higher score, then **larger line index** (prefer implementation body
below file banners). If no line matches and ``query_tokens`` is non-empty: anchor at line 1 with
``selection_reason=no_query_token_in_body_file_start`` and a window starting at
the first line.

If ``query_tokens`` is empty: ``selection_reason=no_query_tokens_file_start``,
anchor line 1.

All rules are fixed; there is no ML or secondary ranking.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from runtime.layer5.evidence.config import SnippetConfig
from runtime.layer5.evidence.executable_snippet_signals import text_has_executable_control_flow
from runtime.layer5.evidence.selection_reason import SelectionReason
from runtime.layer5.evidence.snippet_anchor_quality import pick_best_anchor_line


@dataclass(frozen=True)
class SnippetSpan:
    """Bounded excerpt from a source file (traceable span)."""

    text: str
    start_line: int
    end_line: int
    start_byte_utf8: int
    end_byte_utf8: int
    anchor_line: int
    matched_tokens: Tuple[str, ...]
    selection_reason: SelectionReason
    truncated_by_max_bytes: bool


def _utf8_byte_offset(full_text: str, char_index: int) -> int:
    return len(full_text[:char_index].encode("utf-8"))


def extract_snippet(
    *,
    canonical_root: Path,
    relative_path: str,
    query_tokens: Tuple[str, ...],
    config: SnippetConfig,
) -> SnippetSpan:
    """
    Load ``canonical_root / relative_path`` (capped) and compute a snippet window.

    Line numbers are **1-based**, inclusive ``start_line`` / ``end_line``.

    **Normative byte offsets (v1):** ``start_byte_utf8`` and ``end_byte_utf8`` count
    UTF-8 bytes in the **logical evidence text** ``T`` defined as:
    ``T = decode(read_bytes(path)[:max_file_bytes], utf-8, errors="replace")``.
    They are **not** offsets into raw on-disk bytes if decoding replaces bytes.
    ``start_byte_utf8`` is inclusive; ``end_byte_utf8`` is **exclusive**, so the
    snippet’s UTF-8 substring is ``T.encode("utf-8")[start_byte_utf8:end_byte_utf8]``
    (equivalently: prefix length in UTF-8 to snippet start/end character indices
    in ``T``). Offsets are always within the capped text length.
    """
    path = canonical_root / relative_path
    try:
        raw = path.read_bytes()[: config.max_file_bytes]
    except FileNotFoundError:
        return SnippetSpan(
            text="",
            start_line=0,
            end_line=0,
            start_byte_utf8=0,
            end_byte_utf8=0,
            anchor_line=0,
            matched_tokens=(),
            selection_reason=SelectionReason.FILE_MISSING,
            truncated_by_max_bytes=False,
        )
    except (OSError, PermissionError):
        return SnippetSpan(
            text="",
            start_line=0,
            end_line=0,
            start_byte_utf8=0,
            end_byte_utf8=0,
            anchor_line=0,
            matched_tokens=(),
            selection_reason=SelectionReason.FILE_UNREADABLE,
            truncated_by_max_bytes=False,
        )

    truncated = path.is_file() and path.stat().st_size > config.max_file_bytes
    text = raw.decode("utf-8", errors="replace")
    if not text:
        return SnippetSpan(
            text="",
            start_line=1,
            end_line=1,
            start_byte_utf8=0,
            end_byte_utf8=0,
            anchor_line=1,
            matched_tokens=(),
            selection_reason=SelectionReason.EMPTY_FILE,
            truncated_by_max_bytes=truncated,
        )

    segments = text.splitlines(True)
    if not segments:
        return SnippetSpan(
            text="",
            start_line=1,
            end_line=1,
            start_byte_utf8=0,
            end_byte_utf8=0,
            anchor_line=1,
            matched_tokens=(),
            selection_reason=SelectionReason.EMPTY_FILE,
            truncated_by_max_bytes=truncated,
        )

    starts_char: list[int] = []
    pos = 0
    for seg in segments:
        starts_char.append(pos)
        pos += len(seg)

    bodies = [s.rstrip("\r\n") for s in segments]
    n = len(bodies)

    if not query_tokens:
        reason = SelectionReason.NO_QUERY_TOKENS_FILE_START
        anchor_idx = 0
        matched = ()
    else:
        anchor_idx, matched = pick_best_anchor_line(bodies, query_tokens)
        if not matched:
            anchor_idx = 0
            matched = ()
            reason = SelectionReason.NO_QUERY_TOKEN_IN_BODY_FILE_START
        else:
            reason = SelectionReason.QUERY_TOKEN_SUBSTRING_ANCHOR

    before = max(0, anchor_idx - config.context_lines_before)
    after = min(n - 1, anchor_idx + config.context_lines_after)
    snippet_text = "".join(segments[before : after + 1])

    start_char = starts_char[before]
    end_char = starts_char[after] + len(segments[after])
    start_b = _utf8_byte_offset(text, start_char)
    end_b = _utf8_byte_offset(text, end_char)

    return SnippetSpan(
        text=snippet_text,
        start_line=before + 1,
        end_line=after + 1,
        start_byte_utf8=start_b,
        end_byte_utf8=end_b,
        anchor_line=anchor_idx + 1,
        matched_tokens=matched,
        selection_reason=reason,
        truncated_by_max_bytes=truncated,
    )


def extract_snippet_executable_rescue(
    *,
    canonical_root: Path,
    relative_path: str,
    config: SnippetConfig,
) -> Optional[SnippetSpan]:
    """
    Re-anchor on the first physical line that contains executable control-flow signals.

    Used when the primary query-token anchor lands in declaration/header zones for
    EXPLAIN_DEBUG selected files. Deterministic: top-to-bottom first matching line.
    """
    path = canonical_root / relative_path
    try:
        raw = path.read_bytes()[: config.max_file_bytes]
    except FileNotFoundError:
        return None
    except (OSError, PermissionError):
        return None

    truncated = path.is_file() and path.stat().st_size > config.max_file_bytes
    text = raw.decode("utf-8", errors="replace")
    if not text:
        return None

    segments = text.splitlines(True)
    if not segments:
        return None

    starts_char: list[int] = []
    pos = 0
    for seg in segments:
        starts_char.append(pos)
        pos += len(seg)

    bodies = [s.rstrip("\r\n") for s in segments]
    n = len(bodies)
    anchor_idx: Optional[int] = None
    for i, line in enumerate(bodies):
        if text_has_executable_control_flow(line):
            anchor_idx = i
            break
    if anchor_idx is None:
        return None

    before = max(0, anchor_idx - config.context_lines_before)
    after = min(n - 1, anchor_idx + config.context_lines_after)
    snippet_text = "".join(segments[before : after + 1])

    start_char = starts_char[before]
    end_char = starts_char[after] + len(segments[after])
    start_b = _utf8_byte_offset(text, start_char)
    end_b = _utf8_byte_offset(text, end_char)

    return SnippetSpan(
        text=snippet_text,
        start_line=before + 1,
        end_line=after + 1,
        start_byte_utf8=start_b,
        end_byte_utf8=end_b,
        anchor_line=anchor_idx + 1,
        matched_tokens=(),
        selection_reason=SelectionReason.EXECUTABLE_CONTROL_FLOW_RESCUE_ANCHOR,
        truncated_by_max_bytes=truncated,
    )
