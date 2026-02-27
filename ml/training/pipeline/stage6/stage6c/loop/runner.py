"""
LoopRunner: builds messages in order governance → seed → wrappers(empty) → carryover → step_query,
calls model adapter, records StepRecord per step.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..seeds.registry import SeedRegistry, SeedView
from ..trace.types import RunSpec, StepRecord, RunTrace, PromptMessage
from ..model.adapter import ModelAdapter
from ..injections.wrapper import apply_wrapper
from ..injections.types import WrapperState
from .roles import get_step_role_schedule
from .carryover import get_carryover_messages, CarryoverMode


def build_step_messages(
    seed: SeedView,
    step_index: int,
    step_role: str,
    step_query_text: str,
    carryover_messages: List[Dict[str, Any]],
    run_id: str,
    injection_profile_id: str,
    horizon_N: int,
    shape: str,
) -> List[PromptMessage]:
    """
    Build the ordered message list for one step.
    Order: governance → seed → wrappers → carryover → step_query.
    Wrappers are empty when injection_profile_id == "none". Each message has "origin" for verification.
    """
    messages: List[PromptMessage] = []

    # 1) Governance
    for content in seed.governance_system_messages:
        messages.append({"role": "system", "content": content, "origin": "governance"})

    # 2) Seed (system + user)
    for content in seed.seed_system_messages:
        messages.append({"role": "system", "content": content, "origin": "seed"})
    for content in seed.seed_user_messages:
        messages.append({"role": "user", "content": content, "origin": "seed"})

    # 3) Wrappers (injection profile; origin="wrapper")
    wrapper_state = WrapperState(
        run_id=run_id,
        horizon_N=horizon_N,
        shape=shape,
        step_index=step_index,
        step_role=step_role,
        injection_profile_id=injection_profile_id,
    )
    for m in apply_wrapper(wrapper_state):
        messages.append(m)

    # 4) Carryover (append as-is; carryover module owns origin tags)
    for m in carryover_messages:
        messages.append(m)

    # 5) Step query (user); inject metadata for DummyModelAdapter
    step_query_msg: PromptMessage = {
        "role": "user",
        "content": step_query_text,
        "origin": "step_query",
        "metadata": {"run_id": run_id, "step_index": step_index, "step_role": step_role},
    }
    messages.append(step_query_msg)

    return messages


def step_query_text_for_role(step_role: str, step_index: int) -> str:
    """Generate a minimal step query string for the given role (M2: no injection)."""
    return f"Step {step_index + 1} ({step_role}): Proceed according to the scenario."


class LoopRunner:
    """
    Runs one loop: load seed, iterate steps with correct message ordering and carryover,
    record StepRecords, return RunTrace.
    """

    def __init__(
        self,
        seed_registry: SeedRegistry,
        model: ModelAdapter,
        max_transcript_chars: Optional[int] = None,
        full_transcript_policy: str = "include_wrappers",
    ) -> None:
        self._registry = seed_registry
        self._model = model
        self._max_transcript_chars = max_transcript_chars
        self._full_transcript_policy = full_transcript_policy

    def run_loop(
        self,
        spec: RunSpec,
        step_role_sequence_override: Optional[List[str]] = None,
    ) -> RunTrace:
        seed = self._registry.get(spec.seed_id)
        if seed is None:
            raise ValueError(f"Seed not found: {spec.seed_id}")

        schedule = get_step_role_schedule(
            spec.horizon_N,
            spec.shape,
            step_role_sequence_override,
        )
        steps: List[StepRecord] = []
        step_history: List[dict] = []
        started_at = datetime.now(timezone.utc)

        for step_index in range(spec.horizon_N):
            step_role = schedule[step_index]
            carryover_msgs = get_carryover_messages(
                spec.carryover_mode,  # type: ignore[arg-type]
                step_index,
                step_history,
                self._max_transcript_chars,
                full_transcript_policy=self._full_transcript_policy,
            )
            step_query_text = step_query_text_for_role(step_role, step_index)
            prompt_messages = build_step_messages(
                seed,
                step_index,
                step_role,
                step_query_text,
                carryover_msgs,
                spec.run_id,
                spec.injection_profile_id,
                spec.horizon_N,
                spec.shape,
            )
            response = self._model.generate(prompt_messages)
            record = StepRecord(
                run_id=spec.run_id,
                step_index=step_index,
                step_role=step_role,
                prompt_messages=prompt_messages,
                response=response,
                metadata={},
                phase_dom_decision_t=None,
                phase_dom_rhetoric_t=None,
            )
            steps.append(record)
            step_history.append({"prompt_messages": prompt_messages, "response": response})

        completed_at = datetime.now(timezone.utc)
        return RunTrace(spec=spec, steps=steps, started_at=started_at, completed_at=completed_at)
