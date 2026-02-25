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
    Generate wrapper messages for the current step. Returns list of messages
    with role="user", content from the profile template, origin="wrapper".
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
    out: List[PromptMessage] = []
    for content in contents:
        if content:
            out.append({
                "role": "user",
                "content": content,
                "origin": "wrapper",
            })
    return out
