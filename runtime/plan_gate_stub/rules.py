"""Stub decision logic. NOT a semantic oracle. Safe, non-doctrinal heuristics only."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonicalize import boundary_phrase_hash, plan_hash

RISKY_BOUNDARY_TYPES = {"merge", "deploy", "prod_write", "security_change", "data_delete", "config_rollout"}

ACTION_TO_BOUNDARY: dict[str, tuple[str, str]] = {
    "PR_MERGE": ("merge", "merge to main"),
    "CONFIG_CHANGE": ("config_rollout", "apply config change affecting production"),
    "DEPLOY_INTENT": ("deploy", "deploy to production environment"),
    "PROD_WRITE_INTENT": ("prod_write", "write to production data store"),
    "OTHER": ("other", "execute irreversible operation"),
}


def load_lineage_index(repo_root: Path | None = None, lineage_index_path: str | Path | None = None) -> dict | None:
    """Load lineage index. If lineage_index_path given, load from that; else default path."""
    if lineage_index_path is not None:
        path = Path(lineage_index_path)
    else:
        if repo_root is None:
            repo_root = Path(__file__).resolve().parents[3]
        path = Path(repo_root) / "ml" / "lineage" / "schemas" / "examples" / "lineage_index_valid.json"
    if not path.exists():
        return None
    import json
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve_lineage(
    boundary_phrase_hash_val: str,
    lineage_index: dict | None,
) -> dict:
    """Resolve boundary_phrase_hash via lineage index. Never use 'guessed'."""
    if lineage_index is None:
        return {"resolved_via": "unresolved", "reason": "lineage_index not available"}
    idx = lineage_index.get("boundary_phrase_hash_index", {})
    entry = idx.get(boundary_phrase_hash_val)
    if entry:
        return {
            "resolved_via": "lineage_index",
            "base_id": entry.get("base_id", ""),
            "variant_id": entry.get("variant_id", ""),
        }
    return {"resolved_via": "unresolved", "reason": "hash not in lineage index"}


def stub_decide(
    plan_request: dict,
    mode: str,
    fixed_time: str | None,
    repo_root: Path | None = None,
    lineage_index_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Produce all artifacts: plan, decision_response, ledger_row, shadow_run_record, ingestion_batch.
    Deterministic when fixed_time is set.
    """
    import json
    from .canonicalize import canonical_json, derive_id

    ide_event = plan_request.get("ide_event", {})
    action = ide_event.get("action", {})
    action_type = action.get("action_type", "OTHER")
    boundary_type, boundary_phrase = ACTION_TO_BOUNDARY.get(
        action_type, ACTION_TO_BOUNDARY["OTHER"]
    )
    bp_hash = boundary_phrase_hash(boundary_phrase)

    # Authority heuristic: evidence_refs with ticket/pr -> pass else unknown
    evidence = ide_event.get("evidence_refs") or []
    has_evidence = any(
        e.get("type") in ("ticket", "pr") for e in evidence if isinstance(e, dict)
    )
    authority_verdict = "pass" if has_evidence else "unknown"

    # Phase routing (conservative)
    if authority_verdict != "pass" and boundary_type in RISKY_BOUNDARY_TYPES:
        constitutional_phase = "REF"
        decision = "REFUSAL"
        dominance_source = "REF"
        terminal_posture = "refuse"
        boundary_verdict = "blocked"
        ref_enforced = True
        reason_codes = ["MISSING_AUTHORITY", "REF_ENFORCED"]
    else:
        # Shadow: never safe_execute, use BOUNDING
        constitutional_phase = "CONF" if action_type != "OTHER" else "DES"
        dominance_source = constitutional_phase
        decision = "BOUNDING"
        terminal_posture = "bounded_allow"
        boundary_verdict = "allowed_pre_boundary_only"
        ref_enforced = False
        reason_codes = ["SAFE_PREBOUNDARY_ONLY"]

    ts = fixed_time or plan_request.get("timestamp_utc", "2026-03-01T00:00:00Z")
    req_id = plan_request.get("request_id", "req-stub")
    sess_id = ide_event.get("ide_context", {}).get("project", "m-coder") + "-sess"
    user = ide_event.get("ide_context", {}).get("user", "stub")

    lineage_index = load_lineage_index(repo_root, lineage_index_path)
    prov = resolve_lineage(bp_hash, lineage_index)

    # Build plan
    plan = {
        "schema_version": "plan.v0.1",
        "request": {
            "request_id": req_id,
            "session_id": sess_id,
            "timestamp_utc": ts,
            "actor": {"user_id": user},
            "artifacts": [],
        },
        "constitutional_phase_expected": constitutional_phase,
        "stress_surfaces": ["AuthorityOwnership"],
        "authority": {
            "claimed": {},
            "validation_requirements": [],
            "validated": {"verdict": authority_verdict, "validator": "stub_v1"},
        },
        "boundary": {
            "irreversible_boundary_phrase": boundary_phrase,
            "boundary_type": boundary_type,
            "rollback_unilateral": False,
        },
        "routing_invariants": {
            "legitimacy_state": "legitimate" if authority_verdict == "pass" else "unknown",
            "irreversibility_state": "pre_boundary",
            "ambiguity_state": "resolved",
            "dominance_applied": "REF>CONF>DES",
        },
        "policy_posture": {
            "allowed_pre_boundary_actions": ["read", "review", "run_tests"],
            "blocked_actions": ["merge", "deploy", "apply"] if boundary_type != "other" else [],
            "terminal_posture": terminal_posture,
        },
        "tooling_intent": {
            "tools_may_be_used": ["read"],
            "tools_must_not_be_used": ["deploy", "merge"],
            "execution_mode": mode,
        },
    }
    ph = plan_hash(plan)

    # Build decision_response
    decision_resp = {
        "schema_version": "decision_response.v0.1",
        "request_id": req_id,
        "decision": decision,
        "constitutional_phase_emitted": constitutional_phase,
        "dominance_source": dominance_source,
        "irreversible_boundary_phrase": boundary_phrase,
        "boundary_phrase_hash": bp_hash,
        "boundary_type": boundary_type,
        "authority_verdict": authority_verdict,
        "missing_evidence": [] if authority_verdict == "pass" else ["approval"],
        "allowed_pre_boundary_actions": ["read", "review", "run_tests"],
        "blocked_actions": ["merge", "deploy"] if boundary_type in ("merge", "deploy") else ["apply"],
        "reason_codes": reason_codes,
        "plan_hash": ph,
        "ui": {"title": decision, "message": f"{constitutional_phase} {decision}", "severity": "info"},
        "provenance_resolution": prov,
    }

    # Ledger
    evt_id = derive_id("evt", canonical_json(plan_request))
    ledger = {
        "schema_version": "ledger_row.v0.1",
        "event": {
            "event_id": evt_id,
            "timestamp_utc": ts,
            "request_id": req_id,
            "session_id": sess_id,
            "mode": mode,
            "runtime_version": "0.1",
        },
        "plan_link": {"plan_hash": ph, "plan_schema_version": "plan.v0.1"},
        "verdicts": {
            "phase_emitted": constitutional_phase,
            "terminal_posture": terminal_posture,
            "authority_verdict": authority_verdict,
            "boundary_verdict": boundary_verdict,
            "ref_enforced": ref_enforced,
        },
        "boundary": {
            "irreversible_boundary_phrase": boundary_phrase,
            "boundary_cross_attempted": False,
            "boundary_crossed": False,
        },
        "actions": {"tool_calls_attempted": [], "execution_intents": []},
        "reason_codes": reason_codes,
    }

    # Shadow run record
    run_id = derive_id("run", canonical_json(plan_request))
    shadow_run = {
        "schema_version": "shadow_run_record.v0.1",
        "run_id": run_id,
        "session_id": sess_id,
        "request_id": req_id,
        "plan_hash": ph,
        "transport_status": "ok",
        "decision": decision,
        "boundary_verdict": boundary_verdict,
        "emitted": {"plan_emitted": True, "ledger_emitted": True, "decision_emitted": True},
        "timestamps": {"start_utc": ts, "end_utc": ts},
        "links": {"ledger_event_id": evt_id},
        "reason_codes": reason_codes,
    }

    # Ingestion batch
    batch_id = derive_id("batch", canonical_json(plan_request))
    lineage_refs = {"boundary_phrase_hash": bp_hash}
    if prov.get("resolved_via") == "lineage_index":
        lineage_refs["base_id"] = prov.get("base_id", "")
        lineage_refs["variant_id"] = prov.get("variant_id", "")
    ingestion = {
        "schema_version": "ingestion_batch.v0.1",
        "batch_id": batch_id,
        "created_utc": ts,
        "source": {"component": "runtime_plan_gate", "host": "stub"},
        "items": [{
            "request_id": req_id,
            "plan": plan,
            "ledger_row": ledger,
            "decision_response": decision_resp,
            "lineage_refs": lineage_refs,
        }],
    }

    return {
        "plan": plan,
        "decision_response": decision_resp,
        "ledger_row": ledger,
        "shadow_run_record": shadow_run,
        "ingestion_batch": ingestion,
    }
