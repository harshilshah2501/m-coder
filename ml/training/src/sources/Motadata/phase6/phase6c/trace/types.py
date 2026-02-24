"""
Trace types for Phase-6C runs: RunSpec, StepRecord, RunTrace.
Consistent with PHASE6C_DESIGN_SPEC_V1.1; placeholders for phase_dom_decision_t / phase_dom_rhetoric_t (M2: None).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Message dict: role, content, origin (governance | seed | wrappers | carryover | step_query)
PromptMessage = Dict[str, Any]  # {"role": str, "content": str, "origin": str}


@dataclass
class RunSpec:
    """Spec for a single run."""
    run_id: str
    seed_id: str
    horizon_N: int
    shape: str
    carryover_mode: str
    injection_profile_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class StepRecord:
    """Record for one step in a run."""
    run_id: str
    step_index: int
    step_role: str
    prompt_messages: List[PromptMessage]  # ordered; each has origin tag
    response: Dict[str, Any]  # e.g. {"content": str, "model": str, "tokens": int}
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Placeholders (M2: do not compute; keep None)
    phase_dom_decision_t: Optional[str] = None
    phase_dom_rhetoric_t: Optional[str] = None


@dataclass
class RunTrace:
    """Full trace of one run: spec + steps + timestamps."""
    spec: RunSpec
    steps: List[StepRecord]
    started_at: datetime
    completed_at: Optional[datetime] = None
