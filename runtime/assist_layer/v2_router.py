from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import re
from typing import Any, Dict


class AssistV2Mode(str, Enum):
    ASK = "ask"
    DEBUG = "debug"
    MIXED = "mixed"


@dataclass(frozen=True)
class AssistV2RouteDecision:
    mode: AssistV2Mode
    mode_reason: str
    task_type_label: str
    has_selected_file: bool
    has_selection: bool

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["mode"] = self.mode.value
        return d


def decide_assist_v2_mode(
    *,
    task_type_label: str,
    selected_file: str,
    selection_text: str,
) -> AssistV2RouteDecision:
    task = str(task_type_label or "").strip()
    selected = bool(str(selected_file or "").strip())
    selection = bool(str(selection_text or "").strip())

    if task == "EXPLAIN_DEBUG":
        return AssistV2RouteDecision(
            mode=AssistV2Mode.DEBUG,
            mode_reason="task_type_explain_debug",
            task_type_label=task or "general",
            has_selected_file=selected,
            has_selection=selection,
        )
    if selected and selection:
        return AssistV2RouteDecision(
            mode=AssistV2Mode.MIXED,
            mode_reason="selected_file_and_selection_present",
            task_type_label=task or "general",
            has_selected_file=selected,
            has_selection=selection,
        )
    if selected:
        return AssistV2RouteDecision(
            mode=AssistV2Mode.MIXED,
            mode_reason="selected_file_present",
            task_type_label=task or "general",
            has_selected_file=selected,
            has_selection=selection,
        )
    return AssistV2RouteDecision(
        mode=AssistV2Mode.ASK,
        mode_reason="default_ask_mode",
        task_type_label=task or "general",
        has_selected_file=selected,
        has_selection=selection,
    )


def build_assist_v2_response_shell(
    decision: AssistV2RouteDecision,
    *,
    proof_density: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    hooks = proof_density if isinstance(proof_density, dict) else {}
    return {
        "schema_version": "assist_router.v2.skeleton",
        "diagnostics_only": True,
        "behavior_change_applied": False,
        "route_decision": decision.to_dict(),
        "response_shape": {
            "ask": {
                "enabled": decision.mode == AssistV2Mode.ASK,
                "sections": ["direct_answer", "owner_anchor", "supporting_context", "confidence_limits"],
            },
            "debug": {
                "enabled": decision.mode == AssistV2Mode.DEBUG,
                "sections": ["logic_flow", "failure_points", "evidence", "confidence_limits"],
            },
            "mixed": {
                "enabled": decision.mode == AssistV2Mode.MIXED,
                "sections": ["answer", "code_context", "risk_notes", "confidence_limits"],
            },
        },
        "proof_density_hooks": {
            "available": bool(hooks),
            "execution_path_stitched": hooks.get("execution_path_stitched"),
            "call_site_resolution_state": hooks.get("call_site_resolution_state"),
            "method_window_visible_rate": hooks.get("method_window_visible_rate"),
        },
    }


def augment_assist_v2_with_response(
    *,
    skeleton: Dict[str, Any],
    ask_response: Dict[str, Any],
) -> Dict[str, Any]:
    out = dict(skeleton or {})
    decision = out.get("route_decision") if isinstance(out.get("route_decision"), dict) else {}
    mode = str(decision.get("mode") or "")
    meta = ask_response.get("metadata") if isinstance(ask_response.get("metadata"), dict) else {}
    summary = ask_response.get("plan_summary") if isinstance(ask_response.get("plan_summary"), dict) else {}
    plan_steps = [str(s) for s in (summary.get("steps") or []) if str(s).strip()]
    notes = [str(n) for n in (summary.get("notes") or []) if str(n).strip()]
    context_bundle = ask_response.get("context_bundle") if isinstance(ask_response.get("context_bundle"), dict) else {}
    context_files = context_bundle.get("files") if isinstance(context_bundle.get("files"), list) else []

    proof_density = {
        "execution_path_stitched": meta.get("execution_path_stitched"),
        "call_site_resolution_state": meta.get("call_site_resolution_state"),
        "method_window_visible_rate": meta.get("method_window_visible_rate"),
    }
    out["proof_density_hooks"] = {
        "available": any(v is not None for v in proof_density.values()),
        **proof_density,
    }
    if mode == AssistV2Mode.DEBUG.value:
        # Ask-path activation only; preserve debug behavior and avoid forcing ask-shaped sections.
        return out

    owner = _extract_primary_owner(plan_steps)
    out["answer"] = _build_answer_block(plan_steps, owner)
    out["evidence"] = _build_evidence_block(meta, context_files, owner)
    out["gaps"] = _build_gaps_block(meta, plan_steps, notes)
    out["next_steps"] = _build_next_steps_block(meta, owner, context_files)
    return out


def _extract_primary_owner(plan_steps: list[str]) -> Dict[str, str]:
    owner_re = re.compile(
        r"Primary implementation owner:\s*`(?P<symbol>[^`]+)`\s+in\s+`(?P<file>[^`]+)`(?:,\s*method\s*`(?P<method>[^`]+)`)?",
        re.IGNORECASE,
    )
    for step in plan_steps:
        m = owner_re.search(step)
        if not m:
            continue
        return {
            "symbol": str(m.group("symbol") or "").strip(),
            "file": str(m.group("file") or "").strip(),
            "method": str(m.group("method") or "").strip(),
        }
    return {"symbol": "", "file": "", "method": ""}


def _build_answer_block(plan_steps: list[str], owner: Dict[str, str]) -> Dict[str, Any]:
    direct_answer = ""
    execution_summary = ""
    for s in plan_steps:
        low = s.lower()
        if not direct_answer and not any(
            token in low
            for token in (
                "primary implementation owner:",
                "supporting context only",
                "files explicitly marked as not the owner",
                "domain notes:",
                "execution-path stitch:",
            )
        ):
            direct_answer = s
        if not execution_summary and (
            s.startswith("Execution-path stitch:")
            or "partial first-hop trace" in low
            or "downstream call" in low
        ):
            execution_summary = s

    out: Dict[str, Any] = {}
    if direct_answer:
        out["direct_grounded_answer"] = direct_answer
    owner_file = str(owner.get("file") or "")
    owner_symbol = str(owner.get("symbol") or "")
    owner_method = str(owner.get("method") or "")
    if owner_file or owner_symbol or owner_method:
        out["primary_owner_or_locus"] = {
            "symbol": owner_symbol,
            "file": owner_file,
            "method": owner_method,
        }
    if execution_summary:
        out["execution_summary"] = execution_summary
    return out


def _build_evidence_block(
    meta: Dict[str, Any],
    context_files: list[dict[str, Any]],
    owner: Dict[str, str],
) -> Dict[str, Any]:
    owner_anchor = {
        "symbol": str(owner.get("symbol") or ""),
        "file": str(owner.get("file") or ""),
        "method": str(owner.get("method") or ""),
    }
    anchors = []
    for f in context_files[:5]:
        if not isinstance(f, dict):
            continue
        anchors.append(
            {
                "path": str(f.get("path") or ""),
                "selection_reason": str(f.get("selection_reason") or ""),
            }
        )
    cb = meta.get("context_budget") if isinstance(meta.get("context_budget"), dict) else {}
    return {
        "owner_anchor": owner_anchor,
        "context_anchors": anchors,
        "proof_density_summary": {
            "execution_path_stitched": meta.get("execution_path_stitched"),
            "stitched_edge_count": meta.get("stitched_edge_count"),
            "call_site_resolution_state": meta.get("call_site_resolution_state"),
            "method_window_visible_rate": meta.get("method_window_visible_rate"),
            "explicit_method_body_evidence_present": meta.get("explicit_method_body_evidence_present"),
        },
        "context_budget_telemetry_summary": {
            "prompt_input_tokens": cb.get("prompt_input_tokens"),
            "evidence_file_count": cb.get("evidence_file_count", cb.get("evidence_entry_count")),
            "method_snippet_count": cb.get("method_snippet_count"),
            "snippet_total_bytes": cb.get("snippet_total_bytes"),
            "loop_context_bytes": cb.get("loop_context_bytes"),
            "truncation_applied": cb.get("truncation_applied"),
        },
    }


def _build_gaps_block(meta: Dict[str, Any], plan_steps: list[str], notes: list[str]) -> Dict[str, Any]:
    items: list[str] = []
    if str(meta.get("call_site_resolution_state") or "") == "unresolved":
        items.append("Unresolved first-hop: call-site candidates are visible but downstream target is not confirmed.")
    if meta.get("execution_path_stitched") is False:
        items.append("Missing downstream confirmation: execution-path stitch is not resolved in current evidence.")
    mwr = meta.get("method_window_visible_rate")
    if mwr == 0 or meta.get("explicit_method_body_evidence_present") is False:
        items.append("Insufficient branch visibility: selected method window/body evidence is not fully visible.")
    for s in plan_steps + notes:
        low = s.lower()
        if any(tok in low for tok in ("insufficient", "ungrounded", "partial", "not visible", "missing_in_context")):
            items.append(s)
    # Preserve order while deduplicating.
    seen = set()
    deduped = []
    for i in items:
        if i in seen:
            continue
        seen.add(i)
        deduped.append(i)
    return {"explicit_evidence_limits": deduped}


def _build_next_steps_block(
    meta: Dict[str, Any],
    owner: Dict[str, str],
    context_files: list[dict[str, Any]],
) -> Dict[str, Any]:
    owner_file = str(owner.get("file") or "")
    owner_method = str(owner.get("method") or "")
    candidates: list[str] = []
    if owner_file and owner_method:
        candidates.append(f"Inspect `{owner_file}` method `{owner_method}` and verify its immediate downstream call targets.")
    if str(meta.get("call_site_resolution_state") or "") == "unresolved" and owner_file:
        candidates.append(
            f"In `{owner_file}`, confirm the first unresolved call-site candidate and map it to a concrete target method."
        )
    if meta.get("execution_path_stitched") is False and context_files:
        first = context_files[0] if isinstance(context_files[0], dict) else {}
        p = str(first.get("path") or "")
        if p:
            candidates.append(f"Open `{p}` and verify whether current snippet includes downstream method declarations/call edges.")
    # Keep actionable and bounded.
    return {"bounded_verification_steps": candidates[:3]}
