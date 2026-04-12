"""Stage 3 model adapter."""

from __future__ import annotations

from typing import Any, Callable

from runtime.state.validators import validate_model_proposal


class ModelAdapter:
    """
    Sends only LoopContextFrame.v1 plus evidence refs.
    Model callable must return ModelProposal.v1 dict.
    """

    def __init__(self, model_callable: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self._model_callable = model_callable

    def propose(
        self,
        *,
        loop_context_frame: dict[str, Any],
        evidence_refs: list[str],
    ) -> dict[str, Any]:
        payload = {
            "loop_context_frame": loop_context_frame,
            "evidence_refs": list(evidence_refs),
        }
        proposal = self._model_callable(payload)
        validate_model_proposal(proposal, allowed_evidence_refs=set(evidence_refs))
        return proposal
