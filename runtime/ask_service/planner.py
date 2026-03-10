from __future__ import annotations

"""
PlanOnlyPlanner — deterministic, bounded, read/inspect-only planning.

This component intentionally performs NO execution, NO tool calls, and NO model
autonomy. It consumes a query string and a ContextBundle (or reduced view) and
produces a small, deterministic list of 3–6 steps describing how a human or
future runtime could investigate the question.
"""

from dataclasses import dataclass
from typing import List

from runtime.context.contracts import ContextBundle


@dataclass
class PlanSummary:
    steps: List[str]
    notes: List[str] | None = None


class PlanOnlyPlanner:
    """
    Deterministic, bounded planner for repo-aware questions.

    - 3–6 steps only.
    - Steps are read/inspect oriented.
    - No execution, no tool calls, no sandbox.
    - No hidden model autonomy.
    """

    def plan(self, query: str, bundle: ContextBundle) -> PlanSummary:
        # Simple deterministic symbol hint extraction: longest alphanumeric token.
        tokens = [t for t in _tokenize(query) if t]
        primary_token = max(tokens, key=len) if tokens else None

        top_paths = [item.path for item in bundle.items[:3]]
        focus_file = top_paths[0] if top_paths else None

        steps: List[str] = []

        if focus_file:
            steps.append(f"Open {focus_file} and scan for logic related to \"{primary_token}\"." if primary_token else f"Open {focus_file} and scan for logic related to the question.")

        if len(top_paths) > 1:
            steps.append("Review neighboring context files: " + ", ".join(top_paths[1:]) + ".")

        if primary_token:
            steps.append(f"Search the repository for usages of \"{primary_token}\" to locate related call sites and configuration.")
        else:
            steps.append("Search the repository for key terms from your question to locate related call sites and configuration.")

        steps.append("Trace the control flow from the entry points you find to understand how the behavior is orchestrated.")

        if len(steps) < 3:
            steps.append("Review relevant configuration and error-handling code paths to understand failure behavior.")

        if len(steps) > 6:
            steps = steps[:6]

        return PlanSummary(steps=steps)


def _tokenize(text: str) -> List[str]:
    """
    Deterministic, simple tokenization: split on non-alphanumeric, lowercase, drop very short tokens.
    """
    import re

    raw = re.split(r"[^A-Za-z0-9_]+", text)
    return [t.lower() for t in raw if len(t) >= 3]

