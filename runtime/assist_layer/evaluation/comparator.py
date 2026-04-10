from __future__ import annotations

from typing import Any, Dict, List, Set


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _normalize_steps(steps: List[Any]) -> List[str]:
    out: List[str] = []
    for step in steps:
        out.append(_normalize_text(str(step)))
    return out


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _file_paths(resp: Dict[str, Any]) -> List[str]:
    files = _safe_list((resp.get("context_bundle") or {}).get("files"))
    out: List[str] = []
    for f in files:
        if isinstance(f, dict):
            p = f.get("path")
            if isinstance(p, str):
                out.append(p)
    return out


def _set_overlap_ratio(a: Set[str], b: Set[str]) -> float:
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def compare_ask_outputs(
    baseline_output: Dict[str, Any],
    candidate_output: Dict[str, Any],
) -> Dict[str, Any]:
    baseline_files = _file_paths(baseline_output)
    candidate_files = _file_paths(candidate_output)
    baseline_file_set = set(baseline_files)
    candidate_file_set = set(candidate_files)

    baseline_selectors = set(_safe_list((baseline_output.get("context_bundle") or {}).get("selectors_used")))
    candidate_selectors = set(_safe_list((candidate_output.get("context_bundle") or {}).get("selectors_used")))

    baseline_steps = _safe_list((baseline_output.get("plan_summary") or {}).get("steps"))
    candidate_steps = _safe_list((candidate_output.get("plan_summary") or {}).get("steps"))
    baseline_steps_norm = _normalize_steps(baseline_steps)
    candidate_steps_norm = _normalize_steps(candidate_steps)

    baseline_quality = str((baseline_output.get("metadata") or {}).get("evidence_quality") or "")
    candidate_quality = str((candidate_output.get("metadata") or {}).get("evidence_quality") or "")

    governance_equal = baseline_output.get("governance_posture") == candidate_output.get("governance_posture")
    execution_equal = baseline_output.get("execution") == candidate_output.get("execution")
    routing_equal = baseline_output.get("routing_mode") == candidate_output.get("routing_mode")

    output_equivalence = {
        "normalized_plan_steps_equal": baseline_steps_norm == candidate_steps_norm,
        "key_fields_equal": governance_equal and execution_equal and routing_equal and baseline_quality == candidate_quality,
        "structural_equal": (
            baseline_files == candidate_files
            and baseline_selectors == candidate_selectors
            and baseline_steps == candidate_steps
            and governance_equal
            and execution_equal
            and routing_equal
            and baseline_quality == candidate_quality
        ),
    }

    return {
        "files": {
            "baseline_count": len(baseline_files),
            "candidate_count": len(candidate_files),
            "overlap_ratio": _set_overlap_ratio(baseline_file_set, candidate_file_set),
            "exact_match": baseline_files == candidate_files,
        },
        "selectors_used": {
            "baseline_count": len(baseline_selectors),
            "candidate_count": len(candidate_selectors),
            "overlap_ratio": _set_overlap_ratio(set(str(s) for s in baseline_selectors), set(str(s) for s in candidate_selectors)),
            "exact_match": baseline_selectors == candidate_selectors,
        },
        "plan_steps": {
            "baseline_count": len(baseline_steps),
            "candidate_count": len(candidate_steps),
            "exact_match": baseline_steps == candidate_steps,
            "normalized_equal": baseline_steps_norm == candidate_steps_norm,
        },
        "evidence_quality": {
            "baseline": baseline_quality,
            "candidate": candidate_quality,
            "exact_match": baseline_quality == candidate_quality,
        },
        "core_flags": {
            "governance_posture_equal": governance_equal,
            "execution_equal": execution_equal,
            "routing_mode_equal": routing_equal,
        },
        "output_equivalence": output_equivalence,
    }
