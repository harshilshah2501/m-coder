from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from runtime.ask_service.handlers import handle_ask_request
from runtime.assist_layer.assist_contracts import AssistInput
from runtime.assist_layer.service import run_assist_layer_v1

from .comparator import compare_ask_outputs
from .scorer import score_comparison


DEFAULT_ARTIFACT_DIR = Path("docs/validation/artifacts/assist_layer_v2_eval")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_context_meta(ask_request: Dict[str, Any]) -> Dict[str, Any]:
    meta: Dict[str, Any] = {}
    selected_file = ask_request.get("selected_file")
    if isinstance(selected_file, str) and selected_file.strip():
        meta["active_file_path"] = selected_file.strip()

    client_context = ask_request.get("client_context")
    if isinstance(client_context, dict):
        selector_names = client_context.get("selector_names")
        if isinstance(selector_names, list):
            meta["selector_names_used"] = [str(s) for s in selector_names]
        diagnostics_labels = client_context.get("diagnostics_labels")
        if isinstance(diagnostics_labels, list):
            meta["diagnostics_labels"] = [str(s) for s in diagnostics_labels]

    evidence_bundle = ask_request.get("evidence_bundle")
    if isinstance(evidence_bundle, dict):
        entries = evidence_bundle.get("entries")
        if isinstance(entries, list):
            refs: list[str] = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                p = entry.get("path")
                i = entry.get("id")
                if isinstance(p, str) and p.strip():
                    refs.append(p.strip())
                elif isinstance(i, str) and i.strip():
                    refs.append(i.strip())
            meta["evidence_file_paths_or_ids"] = refs
            meta["evidence_presence_or_count"] = len(entries)

    return meta


def _trim_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    files = []
    for item in ((resp.get("context_bundle") or {}).get("files") or []):
        if isinstance(item, dict):
            files.append({
                "path": item.get("path"),
                "selection_reason": item.get("selection_reason"),
            })

    return {
        "schema_version": resp.get("schema_version"),
        "request_id": resp.get("request_id"),
        "governance_posture": resp.get("governance_posture"),
        "execution": resp.get("execution"),
        "routing_mode": resp.get("routing_mode"),
        "context_bundle": {
            "revision": (resp.get("context_bundle") or {}).get("revision"),
            "files": files,
            "selectors_used": (resp.get("context_bundle") or {}).get("selectors_used") or [],
        },
        "plan_summary": {
            "steps": (resp.get("plan_summary") or {}).get("steps") or [],
            "notes": (resp.get("plan_summary") or {}).get("notes") or [],
        },
        "metadata": {
            "evidence_quality": (resp.get("metadata") or {}).get("evidence_quality"),
            "intent_type": (resp.get("metadata") or {}).get("intent_type"),
        },
    }


def evaluate_assist_v2(
    ask_request: Dict[str, Any],
    *,
    output_root: Path | None = None,
    run_id: str | None = None,
    persist_artifact: bool = True,
) -> Dict[str, Any]:
    if str(ask_request.get("schema_version") or "") != "ask_request.v0.1":
        raise ValueError("evaluate_assist_v2 currently supports ask_request.v0.1 only")

    original_query = str(ask_request.get("query") or "")
    request_id = str(ask_request.get("request_id") or "assist-v2-eval")
    trace_id = str(ask_request.get("trace_id") or f"assist-v2-{request_id}")

    assist_input = AssistInput(
        request_id=request_id,
        trace_id=trace_id,
        session_id=str(ask_request.get("session_id") or ""),
        original_query=original_query,
        context_meta=_build_context_meta(ask_request),
        task_type_label=str(ask_request.get("task_type") or "general"),
    )
    assist_output, assist_event = run_assist_layer_v1(assist_input)

    baseline_request = dict(ask_request)
    baseline_request["query"] = assist_output.original_query
    baseline_response = handle_ask_request(baseline_request)

    candidate_request = dict(ask_request)
    candidate_request["query"] = assist_output.augmented_query
    candidate_response = handle_ask_request(candidate_request)

    comparison = compare_ask_outputs(baseline_response, candidate_response)
    verdict, verdict_reasons = score_comparison(comparison)

    rid = run_id or f"{request_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    out = {
        "schema_version": "assist_layer_v2_eval.v1",
        "run_id": rid,
        "timestamp_utc": _now_utc(),
        "request_id": request_id,
        "trace_id": trace_id,
        "query_category": str(ask_request.get("query_category") or "uncategorized"),
        "query_note": str(ask_request.get("query_note") or ""),
        "original_query": assist_output.original_query,
        "augmented_query": assist_output.augmented_query,
        "assist_metadata": {
            "assist_status": assist_output.assist_status.value,
            "confidence_enum": assist_output.confidence_enum.value,
            "transform_codes_applied": list(assist_output.transform_codes_applied),
            "retrieval_drift_validation": dict(assist_output.retrieval_drift_validation),
            "assist_event": assist_event,
        },
        "path_a_baseline_original": _trim_response(baseline_response),
        "path_b_candidate_augmented": _trim_response(candidate_response),
        "comparison": comparison,
        "final_verdict": verdict,
        "verdict_reasons": verdict_reasons,
    }

    if persist_artifact:
        root = output_root or DEFAULT_ARTIFACT_DIR
        root.mkdir(parents=True, exist_ok=True)
        out_path = root / f"{rid}.json"
        out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        out["artifact_path"] = str(out_path)

    return out
