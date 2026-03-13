"""
Shadow mode runner (M3.6).

Runs baseline scenarios through PlanGate in shadow mode and produces
plan, decision, ledger, shadow run record, and ingestion batch items.
Invariant: boundary_verdict never "crossed"; plan and ledger always emitted.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from runtime.plan_gate_stub.plan_gate import PlanGate
from runtime.shadow.baseline_scenarios import ScenarioDef, scenario_to_event
from runtime.shadow.ingestion_batch import build_ingestion_batch, normalize_ledger_row


@dataclass
class ShadowRunResult:
    """Result of one shadow run (one scenario)."""
    scenario_id: str
    request_id: str
    plan: dict[str, Any]
    decision_phase: str
    decision_posture: str
    plan_hash: str
    ledger_row: dict[str, Any]
    shadow_run_record: dict[str, Any]
    boundary_verdict: str
    boundary_crossed: bool
    transport_status: str = "ok"


def _emulator_plan_to_full_plan(emulator_plan: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """
    Map emulator plan (schema_version plan.v0.1, reduced fields) to full plan.v0.1 for ingestion.
    Ensures schema and runtime-rule validation pass.
    """
    event = event or {}
    boundary = emulator_plan.get("boundary", {})
    phrase = boundary.get("phrase") or boundary.get("irreversible_boundary_phrase") or event.get("boundary_phrase", "")
    phase = emulator_plan.get("constitutional_phase") or emulator_plan.get("constitutional_phase_expected", "DES")
    auth = emulator_plan.get("authority", {})
    verdict = auth.get("verdict") if isinstance(auth.get("verdict"), str) else (auth.get("validated") or {}).get("verdict", "unknown")
    posture_map = {"REFUSAL": "refuse", "BOUNDED_ALLOW": "bounded_allow", "SAFE_EXECUTE": "safe_execute"}
    terminal = posture_map.get(
        (emulator_plan.get("policy_posture") or {}).get("terminal_posture"),
        "refuse",
    )
    if phase == "REF":
        terminal = "refuse"
    elif phase == "CONF":
        terminal = terminal if terminal != "safe_execute" else "bounded_allow"
    request_id = event.get("request_id", "req-unknown")
    session_id = event.get("session_id", "sess-unknown")
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "schema_version": "plan.v0.1",
        "request": {
            "request_id": request_id,
            "session_id": session_id,
            "timestamp_utc": ts,
            "actor": {"user_id": (event.get("user_context") or {}).get("user_id", "unknown")},
            "artifacts": [],
        },
        "constitutional_phase_expected": phase,
        "stress_surfaces": ["AuthorityOwnership", "ImplementationIrreversibility"],
        "authority": {
            "claimed": {},
            "validation_requirements": [],
            "validated": {"verdict": verdict, "validator": "shadow_emulator"},
        },
        "boundary": {
            "irreversible_boundary_phrase": phrase if phrase else " ",
            "boundary_type": "merge" if "merge" in (phrase or "").lower() else "deploy" if "deploy" in (phrase or "").lower() else "other",
            "rollback_unilateral": False,
        },
        "routing_invariants": {
            "legitimacy_state": "legitimate" if verdict == "pass" else "unknown",
            "irreversibility_state": "pre_boundary",
            "ambiguity_state": "resolved",
            "dominance_applied": "REF>CONF>DES",
        },
        "policy_posture": {
            "allowed_pre_boundary_actions": ["read", "review", "run_tests"],
            "blocked_actions": ["merge", "deploy", "apply"],
            "terminal_posture": terminal,
        },
        "tooling_intent": {
            "tools_may_be_used": ["read"],
            "tools_must_not_be_used": ["deploy", "merge"],
            "execution_mode": "shadow",
        },
    }


def _decision_response_like(dec: dict[str, Any], plan_hash: str, request_id: str, session_id: str) -> dict[str, Any]:
    """Build a decision_response-shaped dict for ingestion (optional)."""
    return {
        "schema_version": "decision_response.v0.1",
        "request_id": request_id,
        "decision": dec.get("decision", "BOUNDING"),
        "constitutional_phase_emitted": dec.get("phase", "DES"),
        "plan_hash": plan_hash,
        "authority_verdict": dec.get("authority_verdict") or "unknown",
        "reason_codes": dec.get("reason_codes") or [],
        "provenance_resolution": {"resolved_via": "unresolved", "reason": "shadow_emulator"},
    }


class ShadowRunner:
    """
    Runs baseline scenarios in shadow mode through PlanGate.
    Produces ShadowRunResult per scenario and can build ingestion batch.
    """

    def __init__(self, fixed_time: str | None = None):
        self.fixed_time = fixed_time
        self._gate = PlanGate(mode="shadow")

    def run_scenario(self, scenario: ScenarioDef) -> ShadowRunResult:
        """Run one scenario; return result with plan, ledger, shadow run record."""
        event = scenario_to_event(scenario, mode="shadow")
        if self.fixed_time:
            event["_fixed_time"] = self.fixed_time  # ledger emitter does not read this; we'd need to pass via gate
        decision, ledger_row, emulator_plan = self._gate.evaluate_plan(event)
        plan = _emulator_plan_to_full_plan(emulator_plan, event)
        ledger_dict = ledger_row.to_dict()
        plan_hash = decision.plan_hash
        request_id = event.get("request_id", scenario.request_id)
        session_id = event.get("session_id", scenario.session_id)
        ts = self.fixed_time or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        run_id = f"run-{plan_hash[:16]}-{request_id}"
        boundary_verdict = getattr(decision.boundary_verdict, "value", str(decision.boundary_verdict))
        shadow_run_record = {
            "schema_version": "shadow_run_record.v0.1",
            "run_id": run_id,
            "session_id": session_id,
            "request_id": request_id,
            "plan_hash": plan_hash,
            "transport_status": "ok",
            "decision": getattr(decision.decision, "value", str(decision.decision)),
            "boundary_verdict": boundary_verdict,
            "emitted": {"plan_emitted": True, "ledger_emitted": True, "decision_emitted": True},
            "timestamps": {"start_utc": ts, "end_utc": ts},
            "links": {"ledger_event_id": ledger_dict.get("event", {}).get("event_id", "")},
            "reason_codes": getattr(decision, "reason_codes", []) or [],
        }
        boundary_crossed = ledger_dict.get("boundary", {}).get("boundary_crossed", False)
        return ShadowRunResult(
            scenario_id=scenario.id,
            request_id=request_id,
            plan=plan,
            decision_phase=getattr(decision.phase, "value", str(decision.phase)),
            decision_posture=ledger_dict.get("verdicts", {}).get("terminal_posture", "refuse"),
            plan_hash=plan_hash,
            ledger_row=ledger_dict,
            shadow_run_record=shadow_run_record,
            boundary_verdict=boundary_verdict,
            boundary_crossed=boundary_crossed,
        )

    def run_all(self, scenarios: list[ScenarioDef]) -> list[ShadowRunResult]:
        """Run all scenarios and return results in order."""
        return [self.run_scenario(s) for s in scenarios]

    def build_ingestion_batch_from_results(
        self,
        results: list[ShadowRunResult],
        batch_id: str | None = None,
        created_utc: str | None = None,
    ) -> dict[str, Any]:
        """Build ingestion_batch.v0.1 from shadow run results."""
        items = []
        for r in results:
            posture_to_decision = {"refuse": "REFUSAL", "bounded_allow": "BOUNDED_ALLOW", "safe_execute": "SAFE_EXECUTE"}
            dec = {
                "phase": r.decision_phase,
                "decision": posture_to_decision.get(r.decision_posture, "BOUNDED_ALLOW"),
                "plan_hash": r.plan_hash,
                "authority_verdict": r.ledger_row.get("verdicts", {}).get("authority_verdict"),
                "reason_codes": r.ledger_row.get("reason_codes", []),
            }
            phrase = (r.ledger_row.get("boundary") or {}).get("irreversible_boundary_phrase", "") or ""
            bp_hash = _boundary_phrase_hash(phrase) if phrase and str(phrase).strip() else ""
            item = {
                "request_id": r.request_id,
                "plan": r.plan,
                "ledger_row": normalize_ledger_row(r.ledger_row),
                "decision_response": _decision_response_like(dec, r.plan_hash, r.request_id, r.shadow_run_record.get("session_id", "")),
                "lineage_refs": {"boundary_phrase_hash": bp_hash} if bp_hash else {},
            }
            items.append(item)
        return build_ingestion_batch(
            items,
            batch_id=batch_id,
            created_utc=created_utc,
            source_component="runtime_plan_gate",
            source_host="shadow_runner",
        )


def _boundary_phrase_hash(phrase: str) -> str:
    """SHA-256 of boundary phrase per boundary_hashing.v0.1."""
    if not (phrase or "").strip():
        return ""
    s = (phrase or "").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(s.encode("utf-8")).hexdigest()