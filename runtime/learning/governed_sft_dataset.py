from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from runtime.learning.governed_reward import score_governed_response


_SCHEMA_VERSION = "governed_sft_event.v1"


@dataclass(frozen=True)
class GovernedSftEvent:
    event_id: str
    request_id: str
    query: str
    source_file: str
    source_variant: str
    assist_delta: str
    reward: Dict[str, Any]
    response: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": _SCHEMA_VERSION,
            "event_id": self.event_id,
            "request_id": self.request_id,
            "query": self.query,
            "source": {
                "file": self.source_file,
                "variant": self.source_variant,
                "assist_delta": self.assist_delta,
            },
            "reward": dict(self.reward),
            "eligibility": self.reward.get("eligibility"),
            "task_type": "ask_plan_only",
            "training_target": {
                "governance_posture": self.response.get("governance_posture"),
                "execution": self.response.get("execution"),
                "ui": self.response.get("ui"),
                "plan_summary": self.response.get("plan_summary"),
                "metadata": self.response.get("metadata"),
            },
            "response": self.response,
        }


def _lc(v: Any) -> str:
    return str(v or "").strip().lower()


def _query_from_payload(payload: Dict[str, Any], resp: Dict[str, Any]) -> str:
    q = str(payload.get("original_query") or payload.get("query") or "").strip()
    if q:
        return q
    eb = resp.get("evidence_bundle") if isinstance(resp.get("evidence_bundle"), dict) else {}
    return str(eb.get("query_raw") or "").strip()


def _stable_event_id(source_file: str, request_id: str, variant: str) -> str:
    raw = f"{source_file}|{request_id}|{variant}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _is_ask_response(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    if "governance_posture" in obj and "plan_summary" in obj:
        return True
    sv = _lc(obj.get("schema_version"))
    return sv.startswith("plan_only_response")


def _infer_assist_delta_from_verdict(payload: Dict[str, Any]) -> str:
    verdict = _lc(payload.get("final_verdict"))
    if verdict == "improved":
        return "improved"
    if verdict == "same":
        return "same"
    if verdict != "degraded":
        return "same"

    comp = payload.get("comparison") if isinstance(payload.get("comparison"), dict) else {}
    core_flags = comp.get("core_flags") if isinstance(comp.get("core_flags"), dict) else {}
    posture_ok = bool(core_flags.get("governance_posture_equal", True))
    exec_ok = bool(core_flags.get("execution_equal", True))
    routing_ok = bool(core_flags.get("routing_mode_equal", True))
    if posture_ok and exec_ok and routing_ok:
        return "degraded_minor"
    return "degraded_major"


def _build_event(
    *,
    source_file: str,
    source_variant: str,
    payload: Dict[str, Any],
    response: Dict[str, Any],
    assist_delta: str,
) -> GovernedSftEvent:
    request_id = str(response.get("request_id") or payload.get("request_id") or "unknown").strip() or "unknown"
    query = _query_from_payload(payload, response)
    reward = score_governed_response(response, assist_delta=assist_delta).to_dict()
    return GovernedSftEvent(
        event_id=_stable_event_id(source_file, request_id, source_variant),
        request_id=request_id,
        query=query,
        source_file=source_file,
        source_variant=source_variant,
        assist_delta=assist_delta,
        reward=reward,
        response=response,
    )


def extract_events_from_payload(
    payload: Dict[str, Any],
    *,
    source_file: str,
    default_assist_delta: str = "same",
) -> List[GovernedSftEvent]:
    events: List[GovernedSftEvent] = []

    # assist v2 eval artifact: pick best candidate deterministically.
    baseline = payload.get("path_a_baseline_original")
    candidate = payload.get("path_b_candidate_augmented")
    if _is_ask_response(baseline) and _is_ask_response(candidate):
        candidate_delta = _infer_assist_delta_from_verdict(payload)
        ev_base = _build_event(
            source_file=source_file,
            source_variant="baseline",
            payload=payload,
            response=baseline,
            assist_delta="same",
        )
        ev_cand = _build_event(
            source_file=source_file,
            source_variant="candidate",
            payload=payload,
            response=candidate,
            assist_delta=candidate_delta,
        )
        # Deterministic selection: higher reward wins; tie-break prefers candidate only when improved.
        rb = int(ev_base.reward.get("total_reward", 0))
        rc = int(ev_cand.reward.get("total_reward", 0))
        if rc > rb:
            events.append(ev_cand)
        elif rb > rc:
            events.append(ev_base)
        else:
            events.append(ev_cand if candidate_delta == "improved" else ev_base)
        return events

    if _is_ask_response(payload):
        events.append(
            _build_event(
                source_file=source_file,
                source_variant="single",
                payload=payload,
                response=payload,
                assist_delta=default_assist_delta,
            )
        )
    return events


def collect_events_from_files(
    files: Sequence[Path],
    *,
    default_assist_delta: str = "same",
) -> Tuple[List[GovernedSftEvent], Dict[str, Any]]:
    events: List[GovernedSftEvent] = []
    skipped = 0
    errors: List[Dict[str, str]] = []
    for p in files:
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                skipped += 1
                continue
            extracted = extract_events_from_payload(
                payload,
                source_file=str(p),
                default_assist_delta=default_assist_delta,
            )
            if not extracted:
                skipped += 1
                continue
            events.extend(extracted)
        except Exception as exc:  # pragma: no cover - defensive
            skipped += 1
            errors.append({"file": str(p), "error": str(exc)})

    stats = {
        "input_files": len(files),
        "events_total": len(events),
        "skipped_files": skipped,
        "errors": errors,
    }
    return events, stats


def filter_events_by_eligibility(
    events: Iterable[GovernedSftEvent], allow: Sequence[str]
) -> List[GovernedSftEvent]:
    allow_set = {_lc(x) for x in allow}
    return [e for e in events if _lc(e.reward.get("eligibility")) in allow_set]

