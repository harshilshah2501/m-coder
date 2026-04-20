from __future__ import annotations

"""
PlanOnlyPlanner — deterministic, bounded, read/inspect-only planning.

This component intentionally performs NO execution, NO tool calls, and NO model
autonomy. It consumes a query string and a ContextBundle (or reduced view) and
produces a small, deterministic list of 3–6 steps describing how a human or
future runtime could investigate the question.
"""

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Optional

from runtime.context.contracts import ContextBundle
from runtime.layer5.retrieval.action_target_selection import select_plan_action_target

from .authority_synthesis import merge_plan_with_authority, synthesize_authority_plan_steps


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

    def plan(
        self,
        query: str,
        bundle: ContextBundle,
        authority_resolution: Optional[Dict[str, Any]] = None,
    ) -> PlanSummary:
        generic = self._plan_generic(query, bundle)
        auth_steps, meta = synthesize_authority_plan_steps(query, bundle, authority_resolution)
        steps = merge_plan_with_authority(generic.steps, auth_steps, authority_resolution)
        notes: List[str] | None = None
        if meta.get("anchor_mode") and meta.get("anchor_mode") != "none":
            notes = [
                f"authority_anchor_mode={meta.get('anchor_mode')}",
                f"authority_uncertainty={meta.get('uncertainty', False)}",
            ]
        return PlanSummary(steps=steps, notes=notes)

    def _plan_generic(self, query: str, bundle: ContextBundle) -> PlanSummary:
        # Deterministic token extraction: prefer repo-meaningful terms over question words.
        tokens = [t for t in _tokenize(query) if t]
        ranked = [item.path for item in bundle.items[:8]]
        primary_token = _select_primary_token(tokens, ranked)
        selected = select_plan_action_target(ranked, query)
        focus_file = selected or (ranked[0] if ranked else None)
        top_paths = ranked[:3]

        steps: List[str] = []

        if _is_class_relationship_query(query):
            steps.append(_class_relationship_answer_step(query, bundle))

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
    toks = [t.lower() for t in raw if len(t) >= 3]
    stop = {
        "which",
        "what",
        "where",
        "when",
        "why",
        "how",
        "this",
        "that",
        "these",
        "those",
        "does",
        "work",
        "works",
        "repo",
        "repository",
    }
    filtered = [t for t in toks if t not in stop]
    return filtered or toks


def _select_primary_token(tokens: List[str], ranked_paths: List[str]) -> Optional[str]:
    """
    Pick a token likely to map to code/search intent:
    - prefer tokens that appear in top-ranked paths (with simple singularization)
    - tie-break by token length then lexical order
    - fallback to longest token
    """
    if not tokens:
        return None
    if not ranked_paths:
        return max(tokens, key=len)

    path_blob = "\n".join(ranked_paths).lower()
    scored: List[tuple[int, int, str]] = []
    for t in tokens:
        stem = t[:-1] if t.endswith("s") and len(t) > 3 else t
        variants = {t, stem}
        hit = 1 if any(v and v in path_blob for v in variants) else 0
        scored.append((hit, len(t), t))
    scored.sort(reverse=True)
    top = scored[0]
    if top[0] > 0:
        return top[2]
    return max(tokens, key=len)


_CLASS_DECL_RE = re.compile(
    r"\bclass\s+([A-Za-z_]\w*)"
    r"(?:\s+extends\s+([A-Za-z_][A-Za-z0-9_\.]*))?"
    r"(?:\s+implements\s+([A-Za-z_][A-Za-z0-9_\.,\s]*))?",
    re.IGNORECASE,
)


def _is_class_relationship_query(query: str) -> bool:
    q = (query or "").lower()
    triggers = (
        "base class",
        "parent class",
        "extends",
        "implements",
        "which class",
    )
    return any(t in q for t in triggers)


def _class_relationship_answer_step(query: str, bundle: ContextBundle) -> str:
    q = (query or "").lower()
    ask_base = "base class" in q or "parent class" in q or "extends" in q
    ask_impl = "implements" in q

    for item in bundle.items:
        text = str(item.content or "")
        m = _CLASS_DECL_RE.search(text)
        if not m:
            continue
        cls = m.group(1)
        base = (m.group(2) or "").strip()
        impl = (m.group(3) or "").strip()
        if ask_base and base:
            return (
                f"Direct answer (grounded): `{cls}` extends `{base}` "
                f"(from snippet in `{item.path}`)."
            )
        if ask_impl and impl:
            return (
                f"Direct answer (grounded): `{cls}` implements `{impl}` "
                f"(from snippet in `{item.path}`)."
            )
        if base or impl:
            rel = f"extends `{base}`" if base else f"implements `{impl}`"
            return f"Direct answer (grounded): `{cls}` {rel} (from `{item.path}`)."

    return (
        "Direct answer (grounded): could not determine the class inheritance/implementation "
        "from retrieved snippets alone; class declaration line is not in top evidence."
    )

