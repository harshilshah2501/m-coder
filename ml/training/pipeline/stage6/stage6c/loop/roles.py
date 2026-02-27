"""
Step role scheduling for N ∈ {3,4,6} and shapes {linear, retry_biased}.
Canonical roles ONLY: rehydrate, plan, act_proposal, retry, pressure_escalation, commit_temptation.
Documented templates are deterministic.
"""
from __future__ import annotations

from typing import List, Optional

from ..config.schema import CANONICAL_STEP_ROLES

# --- Documented schedules (deterministic) ---
#
# N=3 linear:   [rehydrate, plan, act_proposal]
# N=4 linear:   [rehydrate, plan, act_proposal, commit_temptation]
# N=6 linear:   [rehydrate, plan, act_proposal, pressure_escalation, retry, commit_temptation]
#
# N=3 retry_biased:  [rehydrate, act_proposal, retry]  (retry at least once)
# N=4 retry_biased:  [rehydrate, plan, act_proposal, retry]
# N=6 retry_biased:  [rehydrate, plan, act_proposal, pressure_escalation, retry, commit_temptation]  (both retry and pressure_escalation)

_SCHEDULES: dict[tuple[int, str], List[str]] = {
    (3, "linear"): ["rehydrate", "plan", "act_proposal"],
    (4, "linear"): ["rehydrate", "plan", "act_proposal", "commit_temptation"],
    (6, "linear"): ["rehydrate", "plan", "act_proposal", "pressure_escalation", "retry", "commit_temptation"],
    (3, "retry_biased"): ["rehydrate", "act_proposal", "retry"],
    (4, "retry_biased"): ["rehydrate", "plan", "act_proposal", "retry"],
    (6, "retry_biased"): ["rehydrate", "plan", "act_proposal", "pressure_escalation", "retry", "commit_temptation"],
}


def get_step_role_schedule(
    horizon_N: int,
    shape: str,
    step_role_sequence_override: Optional[List[str]] = None,
) -> List[str]:
    """
    Return the step role for each step index 0..horizon_N-1.
    If step_role_sequence_override is provided (length must equal horizon_N), return it after validating
    that every role is in CANONICAL_STEP_ROLES.
    """
    if step_role_sequence_override is not None:
        if len(step_role_sequence_override) != horizon_N:
            raise ValueError(
                f"step_role_sequence_override length must be {horizon_N}, got {len(step_role_sequence_override)}"
            )
        for r in step_role_sequence_override:
            if r not in CANONICAL_STEP_ROLES:
                raise ValueError(f"Unknown step role {r!r}; canonical: {sorted(CANONICAL_STEP_ROLES)}")
        return list(step_role_sequence_override)
    key = (horizon_N, shape)
    if key not in _SCHEDULES:
        raise ValueError(f"No schedule for horizon_N={horizon_N}, shape={shape!r}")
    return list(_SCHEDULES[key])
