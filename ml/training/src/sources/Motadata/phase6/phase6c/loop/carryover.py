"""
Carryover plumbing: cold_start, full_transcript, summary_compressed (stub).
Message ordering: governance → seed → wrappers → carryover → step_query.
"""
from __future__ import annotations

from typing import Any, List, Literal

CarryoverMode = Literal["cold_start", "full_transcript", "summary_compressed"]


def get_carryover_messages(
    mode: CarryoverMode,
    step_index: int,
    step_history: List[dict],  # list of {"prompt_messages": [...], "response": {...}}
    max_chars: int | None = None,
    full_transcript_policy: str = "include_wrappers",
) -> List[dict]:
    """
    Return list of messages to inject as carryover. Each message has "role", "content", "origin": "carryover".
    Carryover module owns origin tags; runner appends as-is.
    step_history contains prior steps' prompt_messages and response (chronological).
    For cold_start: return [].
    For full_transcript:
      - Always include prior step_query messages (origin=="step_query") as user turns.
      - If full_transcript_policy=="include_wrappers": also include prior wrapper messages (origin=="wrapper") as user turns, in chronological order.
      - Always include assistant responses as assistant turns.
      - Never include governance or seed in carryover.
    For summary_compressed: raise NotImplementedError (M2 stub; no summarizer).
    """
    if mode == "cold_start":
        return []
    if mode == "summary_compressed":
        raise NotImplementedError(
            "summary_compressed carryover is not implemented in M2; "
            "no summarizer. Use cold_start or full_transcript."
        )
    if mode != "full_transcript":
        raise ValueError(f"Unknown carryover mode: {mode!r}")

    include_wrappers = full_transcript_policy == "include_wrappers"
    out: List[dict] = []
    total_chars = 0
    for rec in step_history:
        prompt_messages = rec.get("prompt_messages") or []
        response = rec.get("response") or {}
        # User turns from this step: optionally wrapper messages (chronological), then step_query. Never governance/seed.
        if include_wrappers:
            for m in prompt_messages:
                if m.get("origin") == "wrapper" and "content" in m:
                    content = m["content"]
                    role = m.get("role", "user")
                    out.append({"role": role, "content": content, "origin": "carryover"})
                    total_chars += len(content)
                    if max_chars is not None and total_chars >= max_chars:
                        return out
        # step_query as user turn
        for m in prompt_messages:
            if m.get("origin") == "step_query" and "content" in m:
                user_content = m["content"]
                out.append({"role": "user", "content": user_content, "origin": "carryover"})
                total_chars += len(user_content)
                if max_chars is not None and total_chars >= max_chars:
                    return out
                break
        # Assistant response
        resp_content = (response.get("content") or "").strip()
        if resp_content:
            out.append({"role": "assistant", "content": resp_content, "origin": "carryover"})
            total_chars += len(resp_content)
            if max_chars is not None and total_chars >= max_chars:
                return out
    return out


class SummaryCompressedCarryoverStub:
    """
    Stub for summary_compressed mode. get_carryover_messages raises NotImplementedError
    when mode is summary_compressed; this class exists for documentation and future use.
    """

    @staticmethod
    def get_summary(step_history: List[dict]) -> str:
        raise NotImplementedError(
            "SummaryCompressedCarryoverStub: summarizer not implemented in M2. "
            "Use cold_start or full_transcript."
        )
