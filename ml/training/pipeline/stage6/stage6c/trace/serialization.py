"""
JSONL serialization for RunTrace and StepRecord; ISO8601 datetimes.
Supports roundtrip: write_run_trace_jsonl / read_run_trace_jsonl.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .types import RunSpec, StepRecord, RunTrace, PromptMessage


def _datetime_to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _iso_to_datetime(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _spec_to_dict(spec: RunSpec) -> Dict[str, Any]:
    return {
        "run_id": spec.run_id,
        "seed_id": spec.seed_id,
        "horizon_N": spec.horizon_N,
        "shape": spec.shape,
        "carryover_mode": spec.carryover_mode,
        "injection_profile_id": spec.injection_profile_id,
        "created_at": _datetime_to_iso(spec.created_at),
    }


def _step_to_dict(step: StepRecord) -> Dict[str, Any]:
    return {
        "run_id": step.run_id,
        "step_index": step.step_index,
        "step_role": step.step_role,
        "prompt_messages": step.prompt_messages,
        "response": step.response,
        "metadata": step.metadata,
        "phase_dom_decision_t": step.phase_dom_decision_t,
        "phase_dom_rhetoric_t": step.phase_dom_rhetoric_t,
    }


def _trace_to_dict(trace: RunTrace) -> Dict[str, Any]:
    return {
        "spec": _spec_to_dict(trace.spec),
        "steps": [_step_to_dict(s) for s in trace.steps],
        "started_at": _datetime_to_iso(trace.started_at),
        "completed_at": _datetime_to_iso(trace.completed_at) if trace.completed_at else None,
    }


def _dict_to_spec(d: Dict[str, Any]) -> RunSpec:
    return RunSpec(
        run_id=d["run_id"],
        seed_id=d["seed_id"],
        horizon_N=d["horizon_N"],
        shape=d["shape"],
        carryover_mode=d["carryover_mode"],
        injection_profile_id=d["injection_profile_id"],
        created_at=_iso_to_datetime(d["created_at"]),
    )


def _dict_to_step(d: Dict[str, Any]) -> StepRecord:
    return StepRecord(
        run_id=d["run_id"],
        step_index=d["step_index"],
        step_role=d["step_role"],
        prompt_messages=d["prompt_messages"],
        response=d["response"],
        metadata=d.get("metadata") or {},
        phase_dom_decision_t=d.get("phase_dom_decision_t"),
        phase_dom_rhetoric_t=d.get("phase_dom_rhetoric_t"),
    )


def _dict_to_trace(d: Dict[str, Any]) -> RunTrace:
    return RunTrace(
        spec=_dict_to_spec(d["spec"]),
        steps=[_dict_to_step(s) for s in d["steps"]],
        started_at=_iso_to_datetime(d["started_at"]),
        completed_at=_iso_to_datetime(d["completed_at"]) if d.get("completed_at") else None,
    )


def write_run_trace_jsonl(trace: RunTrace, path: str | Path) -> None:
    """
    Write one RunTrace as a single JSON line (one run per line).
    Format: one line = one JSON object with keys spec, steps, started_at, completed_at.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    obj = _trace_to_dict(trace)
    with path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def read_run_trace_jsonl(path: str | Path) -> RunTrace:
    """Read one RunTrace from a JSONL file (first line = one run)."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        line = f.readline()
    if not line.strip():
        raise ValueError(f"Empty file: {path}")
    obj = json.loads(line)
    return _dict_to_trace(obj)


def read_run_traces_jsonl(path: str | Path) -> List[RunTrace]:
    """Read all RunTraces from a JSONL file (one run per line)."""
    path = Path(path)
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(_dict_to_trace(json.loads(line)))
    return out


def append_run_trace_jsonl(trace: RunTrace, path: str | Path) -> None:
    """Append one RunTrace as a new line to an existing JSONL file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    obj = _trace_to_dict(trace)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
