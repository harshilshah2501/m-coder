from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from runtime.context.contracts import ContextBundle


DEFAULT_MAX_CONTEXT_FILES = 40
DEFAULT_MAX_CONTEXT_BYTES = 350_000


def _estimate_tokens(text: str) -> int:
    raw = str(text or "")
    if not raw:
        return 0
    return max(1, (len(raw) + 3) // 4)


def _item_bytes(item: Any) -> int:
    b = int(getattr(item, "byte_size", 0) or 0)
    if b > 0:
        return b
    return len(str(getattr(item, "content", "")).encode("utf-8"))


def _looks_method_like(text: str) -> bool:
    if not text:
        return False
    return bool(
        re.search(r"\b(?:public|private|protected|static|final|def|function)\b[^\n]{0,120}\(", text)
        or re.search(r"\b\w+\s*\([^)]*\)\s*\{", text)
    )


def _snippet_bytes_and_method_count(entries: Sequence[Dict[str, Any]]) -> Tuple[int, int]:
    total = 0
    method_like = 0
    for ent in entries:
        if not isinstance(ent, dict):
            continue
        sn = ent.get("snippet") if isinstance(ent.get("snippet"), dict) else {}
        txt = str(sn.get("text") or "")
        total += len(txt.encode("utf-8"))
        if _looks_method_like(txt):
            method_like += 1
    return total, method_like


def apply_context_budget(
    bundle: ContextBundle,
    *,
    max_files: int = DEFAULT_MAX_CONTEXT_FILES,
    max_bytes: int = DEFAULT_MAX_CONTEXT_BYTES,
) -> Tuple[ContextBundle, List[str], int]:
    flags: List[str] = []
    original_count = len(bundle.items)
    original_bytes = sum(_item_bytes(i) for i in bundle.items)

    kept = []
    used_bytes = 0
    for item in bundle.items[:max_files]:
        b = _item_bytes(item)
        if used_bytes + b > max_bytes:
            flags.append("context_bytes_cap_reached")
            break
        kept.append(item)
        used_bytes += b

    if original_count > max_files:
        flags.append("context_file_cap_reached")
    if len(kept) < original_count and "context_bytes_cap_reached" not in flags and original_bytes > max_bytes:
        flags.append("context_bytes_cap_reached")

    bundle.items = kept
    bundle.limits.max_files = min(int(bundle.limits.max_files), int(max_files))
    bundle.limits.max_bytes = min(int(bundle.limits.max_bytes), int(max_bytes))
    bundle.limits.truncated = bool(flags) or bool(bundle.limits.truncated)
    return bundle, flags, used_bytes


def build_context_budget_metadata(
    *,
    query: str,
    bundle: ContextBundle,
    evidence_entries: Sequence[Dict[str, Any]],
    selected_file: str = "",
    selection: str = "",
    plan_steps: Optional[Sequence[str]] = None,
    explain_debug_payload: Optional[Dict[str, Any]] = None,
    truncation_flags: Optional[Iterable[str]] = None,
    tool_output_bytes: int = 0,
) -> Dict[str, Any]:
    snippet_total_bytes, method_snippet_count = _snippet_bytes_and_method_count(evidence_entries)
    bundle_context_bytes = sum(_item_bytes(i) for i in bundle.items)
    evidence_file_count = len(list(evidence_entries))
    plan_text = "\n".join(str(s) for s in (plan_steps or []))
    explain_text = ""
    if isinstance(explain_debug_payload, dict):
        explain_text = str(explain_debug_payload.get("analysis") or "") + "\n" + str(
            explain_debug_payload.get("summary") or ""
        )
    prompt_payload = "\n".join(
        [
            str(query or ""),
            str(selected_file or ""),
            str(selection or ""),
            "\n".join(str(i.content) for i in bundle.items),
            plan_text,
            explain_text,
        ]
    )
    flags = sorted({str(f) for f in (truncation_flags or []) if str(f).strip()})
    truncation_applied = bool(flags)
    return {
        "prompt_input_tokens": _estimate_tokens(prompt_payload),
        # Keep legacy key for backward compatibility while exposing the canonical alias.
        "evidence_entry_count": evidence_file_count,
        "evidence_file_count": evidence_file_count,
        "method_snippet_count": method_snippet_count,
        "snippet_total_bytes": snippet_total_bytes,
        "tool_output_bytes": int(tool_output_bytes),
        "loop_context_bytes": len((plan_text + "\n" + explain_text).encode("utf-8")),
        "truncation_flags": flags,
        "truncation_applied": truncation_applied,
        "bundle_context_bytes": bundle_context_bytes,
    }
