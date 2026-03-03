"""
Apply injection profile to produce wrapper messages. Messages are origin-tagged "wrapper"
and never mutate governance or seed content.
"""
from __future__ import annotations

from typing import List

from .types import WrapperState, PromptMessage
from .profiles import get_profile


def apply_wrapper(state: WrapperState) -> List[PromptMessage]:
    """
    Generate wrapper messages for the current step.
    Returns list of messages with origin="wrapper".
    Most profiles are emitted as role="user"; constitution_v1 is emitted as role="system".
    Returns [] when injection_profile_id is "none" or profile is disabled/unknown.
    """
    if state.injection_profile_id == "none" or not state.injection_profile_id:
        return []
    profile = get_profile(state.injection_profile_id)
    if profile is None:
        raise ValueError(
            f"Unknown injection profile id: {state.injection_profile_id}"
        )
    contents = profile.generate(
        state.step_index,
        state.step_role,
        state.horizon_N,
        state.shape,
        state.run_id,
    )
    if state.injection_profile_id == "constitution_v1":
        if not any("===CONSTITUTION_V1_START===" in (content or "") for content in contents):
            raise RuntimeError(
                "constitution_v1 wrapper missing constitution marker; refusing run"
            )

    role = "system" if state.injection_profile_id == "constitution_v1" else "user"
    out: List[PromptMessage] = []
    for content in contents:
        if content:
            out.append({
                "role": role,
                "content": content,
                "origin": "wrapper",
            })
    return out
