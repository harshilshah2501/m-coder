from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
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
    meta = ask_response.get("metadata") if isinstance(ask_response.get("metadata"), dict) else {}
    proof_density = {
        "execution_path_stitched": meta.get("execution_path_stitched"),
        "call_site_resolution_state": meta.get("call_site_resolution_state"),
        "method_window_visible_rate": meta.get("method_window_visible_rate"),
    }
    out["proof_density_hooks"] = {
        "available": any(v is not None for v in proof_density.values()),
        **proof_density,
    }
    return out
