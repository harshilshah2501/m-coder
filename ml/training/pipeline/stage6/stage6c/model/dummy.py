"""
DummyModelAdapter: deterministic response from run_id, step_index, step_role.
For smoke tests.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from .adapter import ModelAdapter


class DummyModelAdapter(ModelAdapter):
    """
    Deterministic response based only on run_id, step_index, step_role.
    Response content is a fixed string derived from these three; no randomness.
    """

    def model_id(self) -> str:
        return "dummy"

    def generate(
        self,
        messages: List[Dict[str, Any]],
        expected_phase: str | None = None,
        boundary_string: str | None = None,
    ) -> Dict[str, Any]:
        # Runner injects run_id, step_index, step_role into the step_query message's metadata.
        run_id = ""
        step_index = -1
        step_role = ""
        for m in reversed(messages):
            meta = m.get("metadata") or {}
            if meta.get("run_id"):
                run_id = meta["run_id"]
                step_index = meta.get("step_index", -1)
                step_role = meta.get("step_role", "")
                break
        if not run_id:
            # Fallback: hash of concatenated content for determinism
            content = "".join(m.get("content", "") for m in messages)
            h = hashlib.sha256(content.encode()).hexdigest()[:8]
            run_id, step_index, step_role = f"run-{h}", 0, "rehydrate"
        key = f"{run_id}|{step_index}|{step_role}"
        content = f"[dummy response for {key}]"
        return {"content": content, "model": "dummy", "tokens": 0}
