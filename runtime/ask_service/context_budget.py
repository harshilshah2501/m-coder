from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from runtime.context.contracts import ContextBundle


DEFAULT_MAX_CONTEXT_FILES = 40
DEFAULT_MAX_CONTEXT_BYTES = 350_000
CONTEXT_BUDGET_POLICY_VERSION = "context_budget_policy.v1"
CONTEXT_BUDGET_TRUNCATION_ORDER = [
    "bundle_items_order",
    "max_files",
    "max_bytes",
]

_SURFACE_POLICY = {
    "ask": {
        "warn_prompt_input_tokens": 7_500,
        "warn_bundle_context_bytes": 240_000,
        "max_files": DEFAULT_MAX_CONTEXT_FILES,
        "max_bytes": DEFAULT_MAX_CONTEXT_BYTES,
    },
    "debug": {
        "warn_prompt_input_tokens": 9_000,
        "warn_bundle_context_bytes": 280_000,
        "max_files": DEFAULT_MAX_CONTEXT_FILES,
        "max_bytes": DEFAULT_MAX_CONTEXT_BYTES,
    },
    "plan": {
        "warn_prompt_input_tokens": 4_000,
        "warn_bundle_context_bytes": 140_000,
        "max_files": 24,
        "max_bytes": 220_000,
    },
    "code": {
        "warn_prompt_input_tokens": 3_500,
        "warn_bundle_context_bytes": 120_000,
        "max_files": 20,
        "max_bytes": 180_000,
    },
}


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


def _resolve_surface_budget(surface: str) -> Dict[str, int]:
    key = str(surface or "").strip().lower()
    if key in _SURFACE_POLICY:
        return dict(_SURFACE_POLICY[key])
    return dict(_SURFACE_POLICY["ask"])


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


def apply_context_budget_for_surface(
    bundle: ContextBundle,
    *,
    surface: str,
) -> Tuple[ContextBundle, List[str], int, Dict[str, Any]]:
    p = _resolve_surface_budget(surface)
    out_bundle, flags, used_bytes = apply_context_budget(
        bundle,
        max_files=int(p["max_files"]),
        max_bytes=int(p["max_bytes"]),
    )
    return out_bundle, flags, used_bytes, {
        "surface": str(surface or "ask").strip().lower() or "ask",
        "max_files": int(p["max_files"]),
        "max_bytes": int(p["max_bytes"]),
        "warn_prompt_input_tokens": int(p["warn_prompt_input_tokens"]),
        "warn_bundle_context_bytes": int(p["warn_bundle_context_bytes"]),
        "truncation_order": list(CONTEXT_BUDGET_TRUNCATION_ORDER),
    }


def evaluate_context_budget_policy(
    *,
    surface: str,
    telemetry: Dict[str, Any],
    policy_config: Dict[str, Any],
) -> Dict[str, Any]:
    prompt_tokens = int(telemetry.get("prompt_input_tokens") or 0)
    bundle_bytes = int(telemetry.get("bundle_context_bytes") or 0)
    truncation_applied = bool(telemetry.get("truncation_applied"))
    warn_tokens = int(policy_config.get("warn_prompt_input_tokens") or 0)
    warn_bundle = int(policy_config.get("warn_bundle_context_bytes") or 0)
    warnings: List[str] = []
    if warn_tokens > 0 and prompt_tokens >= warn_tokens:
        warnings.append("warn_prompt_input_tokens_exceeded")
    if warn_bundle > 0 and bundle_bytes >= warn_bundle:
        warnings.append("warn_bundle_context_bytes_exceeded")
    if truncation_applied:
        warnings.append("hard_cap_truncation_applied")
    return {
        "policy_version": CONTEXT_BUDGET_POLICY_VERSION,
        "surface": str(surface or "ask").strip().lower() or "ask",
        "warning_thresholds": {
            "prompt_input_tokens": warn_tokens,
            "bundle_context_bytes": warn_bundle,
        },
        "hard_caps": {
            "max_files": int(policy_config.get("max_files") or 0),
            "max_bytes": int(policy_config.get("max_bytes") or 0),
        },
        "truncation_order": list(policy_config.get("truncation_order") or CONTEXT_BUDGET_TRUNCATION_ORDER),
        "warnings": warnings,
    }


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
