from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import re
from typing import Any, Dict, List


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
    explain_debug = ask_response.get("explain_debug") if isinstance(ask_response.get("explain_debug"), dict) else {}

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
        owner = _extract_primary_owner(plan_steps)
        out["debug_v2"] = _build_debug_v2_block(
            explain_debug=explain_debug,
            meta=meta,
            context_files=context_files,
            owner=owner,
        )
        return out

    owner = _extract_primary_owner(plan_steps)
    out["answer"] = _build_answer_block(plan_steps, owner)
    articulated = ask_response.get("articulated_answer")
    if isinstance(articulated, dict) and mode != AssistV2Mode.DEBUG.value:
        paras = articulated.get("paragraphs")
        if isinstance(paras, list) and paras:
            ans = out.get("answer") if isinstance(out.get("answer"), dict) else {}
            text_join = "\n\n".join(str(p).strip() for p in paras if str(p).strip())
            if text_join:
                ans["narrative_paragraphs"] = [str(p).strip() for p in paras if str(p).strip()]
                prev_direct = str(ans.get("direct_grounded_answer") or "").strip()
                if len(text_join) > len(prev_direct):
                    ans["direct_grounded_answer"] = text_join
                bullets = articulated.get("supporting_plan_bullets")
                if isinstance(bullets, list) and bullets:
                    ans["supporting_plan_bullets"] = [str(b).strip() for b in bullets if str(b).strip()][:5]
                el = articulated.get("evidence_limit")
                if isinstance(el, str) and el.strip():
                    ans["evidence_limit"] = el.strip()
                ns = meta.get("ask_narration_source")
                if isinstance(ns, str) and ns.strip():
                    ans["narration_source"] = ns.strip()
                out["answer"] = ans
    out["evidence"] = _build_evidence_block(meta, context_files, owner)
    out["gaps"] = _build_gaps_block(meta, plan_steps, notes)
    out["next_steps"] = _build_next_steps_block(meta, owner, context_files)
    if mode == AssistV2Mode.ASK.value:
        investigate = _build_investigate_bridge(
            ask_response=ask_response,
            owner=owner,
            meta=meta,
        )
        if investigate:
            out["investigate"] = investigate
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


def _build_investigate_bridge(
    *,
    ask_response: Dict[str, Any],
    owner: Dict[str, str],
    meta: Dict[str, Any],
) -> Dict[str, Any] | None:
    # Omit by default unless eligibility is explicitly grounded.
    evidence_first = ask_response.get("evidence_first_meta")
    ask_path = ""
    if isinstance(evidence_first, dict):
        ask_path = str(evidence_first.get("ask_path") or "").strip()
    governance_posture = str(ask_response.get("governance_posture") or "").strip()
    execution = ask_response.get("execution")
    owner_file = str(owner.get("file") or "").strip()
    owner_method = str(owner.get("method") or "").strip()
    owner_symbol = str(owner.get("symbol") or "").strip()
    quality = str(meta.get("evidence_quality") or "").strip().upper()
    method_visible, grounding_tier = _resolve_owner_method_visibility(meta)

    eligible = (
        ask_path == "v1_evidence"
        and governance_posture == "PLAN_ONLY"
        and execution is False
        and quality == "STRONG"
        and bool(owner_file)
        and bool(owner_method)
        and bool(method_visible)
    )
    if not eligible:
        return None

    reason = "owner_method_grounded" if grounding_tier == "executable" else "owner_method_visible"
    return {
        "available": True,
        "reason": reason,
        "target": {
            "file": owner_file,
            "method": owner_method,
            "symbol_hints": _symbol_hints(owner_symbol, owner_method),
        },
        "handoff_context": {
            "source_mode": "ask",
            "ask_path": ask_path,
            "governance_posture": governance_posture,
            "execution": False,
        },
        "evidence_anchor": {
            "owner_file": owner_file,
            "owner_method_visible": True,
            "grounding_tier": grounding_tier,
            "proof_density": {
                "method_window_visible_rate": meta.get("method_window_visible_rate"),
                "execution_path_stitched": meta.get("execution_path_stitched"),
                "call_site_resolution_state": meta.get("call_site_resolution_state"),
            },
        },
        "suggested_prompt": "Investigate this owner method and trace visible failure points.",
    }


def _resolve_owner_method_visibility(meta: Dict[str, Any]) -> tuple[bool, str]:
    explicit = meta.get("explicit_method_body_evidence_present") is True
    mwr = meta.get("method_window_visible_rate")
    stitched = meta.get("execution_path_stitched")
    if explicit and isinstance(mwr, (int, float)) and float(mwr) >= 1.0:
        return True, "executable"
    if explicit or (isinstance(mwr, (int, float)) and float(mwr) > 0.0):
        return True, "partial" if stitched is False else "executable"
    return False, "declarative"


def _symbol_hints(owner_symbol: str, owner_method: str) -> list[str]:
    hints = []
    for raw in (owner_symbol, owner_method):
        tok = str(raw or "").strip()
        if tok and tok not in hints:
            hints.append(tok)
    return hints


def _build_debug_v2_block(
    *,
    explain_debug: Dict[str, Any],
    meta: Dict[str, Any],
    context_files: list[dict[str, Any]],
    owner: Dict[str, str],
) -> Dict[str, Any]:
    evidence_list = [str(x).strip() for x in (explain_debug.get("evidence") or []) if str(x).strip()]
    selected_file = _extract_selected_file(evidence_list, context_files, owner)
    selected_method = _extract_selected_method(evidence_list, selected_file, owner)
    line_refs = _extract_line_refs(evidence_list)
    grounding_tier = _resolve_grounding_tier(
        evidence=evidence_list,
        meta=meta,
        selected_file=selected_file,
        selected_method=selected_method,
    )
    confidence_limits = _build_debug_confidence_limits(
        explain_debug=explain_debug,
        meta=meta,
        selected_file=selected_file,
        selected_method=selected_method,
    )
    return {
        "summary": str(explain_debug.get("summary") or ""),
        "execution_flow": str(explain_debug.get("logic_flow") or ""),
        "likely_failure_points": _as_string_list(str(explain_debug.get("likely_bug_risk") or "")),
        "evidence": {
            "selected_file": selected_file,
            "selected_method": selected_method,
            "line_refs": line_refs,
            "grounding_tier": grounding_tier,
        },
        "confidence_limits": confidence_limits,
        "next_inspection_targets": _build_next_inspection_targets(
            selected_file=selected_file,
            selected_method=selected_method,
            evidence=evidence_list,
            owner=owner,
        ),
    }


def _extract_selected_file(
    evidence: List[str],
    context_files: list[dict[str, Any]],
    owner: Dict[str, str],
) -> str:
    missing = _extract_missing_in_context_path(evidence)
    if missing:
        return missing
    for entry in evidence:
        path = _extract_evidence_path(entry)
        if path:
            return path
    owner_file = str(owner.get("file") or "").strip()
    if owner_file:
        return owner_file
    for item in context_files:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        if path:
            return path
    return ""


def _extract_selected_method(evidence: List[str], selected_file: str, owner: Dict[str, str]) -> str:
    for entry in evidence:
        path = _extract_evidence_path(entry)
        if not path:
            continue
        if selected_file and path.lower() != selected_file.lower():
            continue
        anchor = _extract_evidence_anchor(entry)
        if not anchor:
            continue
        if anchor == "analysis_anchor":
            continue
        if re.match(r"^\d+(-\d+)?$", anchor):
            continue
        return anchor
    owner_file = str(owner.get("file") or "").strip()
    owner_method = str(owner.get("method") or "").strip()
    if owner_file and owner_method and selected_file and owner_file.lower() == selected_file.lower():
        return owner_method
    return ""


def _extract_line_refs(evidence: List[str]) -> list[str]:
    refs: list[str] = []
    seen = set()
    for entry in evidence:
        path = _extract_evidence_path(entry)
        anchor = _extract_evidence_anchor(entry)
        if not path or not anchor:
            continue
        if not re.match(r"^\d+(-\d+)?$", anchor):
            continue
        ref = f"{path}:{anchor}"
        if ref in seen:
            continue
        seen.add(ref)
        refs.append(ref)
    return refs


def _extract_evidence_path(entry: str) -> str:
    text = str(entry or "").strip().strip("`")
    if text.startswith("missing_in_context:"):
        return text.split(":", 1)[1].strip()
    if ":" not in text:
        return ""
    path, _ = text.split(":", 1)
    path = path.strip()
    if "/" not in path and "." not in path:
        return ""
    return path


def _extract_evidence_anchor(entry: str) -> str:
    text = str(entry or "").strip().strip("`")
    if text.startswith("missing_in_context:") or ":" not in text:
        return ""
    _, anchor = text.split(":", 1)
    return anchor.strip()


def _extract_missing_in_context_path(evidence: List[str]) -> str:
    for entry in evidence:
        text = str(entry or "").strip()
        if text.startswith("missing_in_context:"):
            return text.split(":", 1)[1].strip()
    return ""


def _resolve_grounding_tier(
    *,
    evidence: List[str],
    meta: Dict[str, Any],
    selected_file: str,
    selected_method: str,
) -> str:
    if _extract_missing_in_context_path(evidence):
        return "none"
    mwr = meta.get("method_window_visible_rate")
    explicit = meta.get("explicit_method_body_evidence_present")
    stitched = meta.get("execution_path_stitched")
    if (
        selected_file
        and selected_method
        and explicit is True
        and isinstance(mwr, (int, float))
        and float(mwr) >= 1.0
        and stitched is not False
    ):
        return "executable"
    if selected_file and (selected_method or explicit is True or (isinstance(mwr, (int, float)) and float(mwr) > 0.0)):
        return "partial"
    if evidence:
        return "declarative"
    return "none"


def _build_debug_confidence_limits(
    *,
    explain_debug: Dict[str, Any],
    meta: Dict[str, Any],
    selected_file: str,
    selected_method: str,
) -> Dict[str, list[str]]:
    visible: list[str] = []
    not_visible: list[str] = []
    requires_next: list[str] = []

    confidence = str(explain_debug.get("confidence_limits") or "").strip()
    if confidence:
        requires_next.append(confidence)
    missing = _extract_missing_in_context_path(
        [str(x).strip() for x in (explain_debug.get("evidence") or []) if str(x).strip()]
    )
    if missing:
        not_visible.append(f"Selected file `{missing}` is not present in retrieved evidence.")
    elif selected_file:
        visible.append(f"Selected file `{selected_file}` is present in current debug evidence.")
    if selected_method:
        visible.append(f"Selected method anchor `{selected_method}` is visible in selected-file evidence.")

    if meta.get("execution_path_stitched") is False:
        requires_next.append("Execution-path stitch is unresolved for downstream confirmation.")
    if str(meta.get("call_site_resolution_state") or "") == "unresolved":
        requires_next.append("Call-site resolution remains unresolved in currently visible evidence.")
    mwr = meta.get("method_window_visible_rate")
    if mwr == 0 or meta.get("explicit_method_body_evidence_present") is False:
        not_visible.append("Full method-window/body evidence is not visible in current context.")
    return {
        "visible": _dedupe_preserve(visible),
        "not_visible": _dedupe_preserve(not_visible),
        "requires_next_inspection": _dedupe_preserve(requires_next),
    }


def _build_next_inspection_targets(
    *,
    selected_file: str,
    selected_method: str,
    evidence: List[str],
    owner: Dict[str, str],
) -> list[dict[str, str]]:
    targets: list[dict[str, str]] = []
    if selected_file:
        targets.append(
            {
                "file": selected_file,
                "method": selected_method or "",
                "reason": "selected_file_adjacent_method_hint",
            }
        )

    collaborator = _extract_explicit_collaborator(evidence=evidence, selected_file=selected_file)
    if collaborator:
        targets.append(
            {
                "file": collaborator["file"],
                "method": collaborator["method"],
                "reason": "explicit_collaborator_in_evidence",
            }
        )

    owner_file = str(owner.get("file") or "").strip()
    owner_method = str(owner.get("method") or "").strip()
    if owner_file and not any(t.get("file", "").lower() == owner_file.lower() for t in targets):
        targets.append(
            {
                "file": owner_file,
                "method": owner_method,
                "reason": "owner_anchor_from_existing_metadata",
            }
        )
    return targets[:3]


def _extract_explicit_collaborator(*, evidence: List[str], selected_file: str) -> Dict[str, str]:
    for entry in evidence:
        path = _extract_evidence_path(entry)
        if not path:
            continue
        if selected_file and path.lower() == selected_file.lower():
            continue
        method = _extract_evidence_anchor(entry)
        if re.match(r"^\d+(-\d+)?$", method or ""):
            method = ""
        return {"file": path, "method": method}
    return {}


def _as_string_list(value: str) -> list[str]:
    v = str(value or "").strip()
    if not v:
        return []
    return [v]


def _dedupe_preserve(items: list[str]) -> list[str]:
    out: list[str] = []
    seen = set()
    for item in items:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out
