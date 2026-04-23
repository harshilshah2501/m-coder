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
from collections import Counter
from typing import Any, Dict, List, Optional

from runtime.context.contracts import ContextBundle
from runtime.layer5.retrieval.action_target_selection import select_plan_action_target

from .authority_synthesis import merge_plan_with_authority, synthesize_authority_plan_steps


@dataclass
class PlanSummary:
    steps: List[str]
    notes: List[str] | None = None
    meta: Dict[str, Any] | None = None


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
        return PlanSummary(steps=steps, notes=notes, meta=meta if meta else None)

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
            steps.append(
                (
                    f"Open {focus_file} and inspect the control flow relevant to \"{primary_token}\"."
                    if primary_token
                    else f"Open {focus_file} and inspect the control flow relevant to the question."
                )
            )

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
    query_mentions_api = (" api" in f" {q} ") or (" apis" in f" {q} ")
    universal_api_base_query = _is_universal_api_base_query(q)

    candidates: List[tuple[str, str, str, str]] = []
    for item in bundle.items:
        text = str(item.content or "")
        for m in _CLASS_DECL_RE.finditer(text):
            cls = m.group(1)
            base = (m.group(2) or "").strip()
            impl = (m.group(3) or "").strip()
            candidates.append((str(item.path), cls, base, impl))

    if not candidates:
        return (
            "Direct answer (grounded): inheritance/implementation could not be asserted from "
            "the current top evidence snippets; class declaration lines are missing."
        )

    # If query explicitly targets APIs, do not answer from non-API declarations.
    if query_mentions_api:
        api_candidates = [
            c
            for c in candidates
            if ("api" in c[0].lower()) or ("api" in c[1].lower())
        ]
        if not api_candidates:
            return (
                "Direct answer (grounded): query asks about APIs, but no API class declaration "
                "is present in top evidence snippets."
            )
        candidates = api_candidates

    if ask_base and universal_api_base_query and query_mentions_api:
        common = _resolve_common_api_base(candidates)
        if common is None:
            preferred = _prefer_api_base_from_evidence(candidates)
            if preferred:
                return (
                    f"Direct answer (grounded): strongest API base-class signal in current evidence "
                    f"is `{preferred}` (limited declaration coverage in top snippets)."
                )
            return (
                "Direct answer (grounded): no single common API base class can be confirmed from "
                "current top snippets; additional API declarations are needed."
            )
        base, count = common
        return (
            f"Direct answer (grounded): common API base class appears to be `{base}` "
            f"(observed across {count} API class declarations in top evidence snippets)."
        )

    for path, cls, base, impl in candidates:
        if ask_base and base:
            return (
                f"Direct answer (grounded): `{cls}` extends `{base}` "
                f"(from snippet in `{path}`)."
            )
        if ask_impl and impl:
            return (
                f"Direct answer (grounded): `{cls}` implements `{impl}` "
                f"(from snippet in `{path}`)."
            )
        if base or impl:
            rel = f"extends `{base}`" if base else f"implements `{impl}`"
            return f"Direct answer (grounded): `{cls}` {rel} (from `{path}`)."

    return (
        "Direct answer (grounded): inheritance/implementation could not be asserted from "
        "the current top evidence snippets; class declaration lines are missing."
    )


def _is_universal_api_base_query(query_lower: str) -> bool:
    q = f" {query_lower} "
    phrases = (
        " base class for all ",
        " parent class for all ",
        " all apis ",
        " all api ",
        " every api ",
    )
    return any(p in q for p in phrases)


def _resolve_common_api_base(
    candidates: List[tuple[str, str, str, str]],
) -> tuple[str, int] | None:
    # Exclude obvious API infrastructure wrappers from "all APIs" common-base voting.
    infra_tokens = ("server", "router", "util", "constant", "handler", "proxy")
    filtered = [
        c
        for c in candidates
        if c[2]
        and not any(t in c[1].lower() for t in infra_tokens)
        and "apiserver" not in c[1].lower()
    ]
    base_pool = filtered if filtered else [c for c in candidates if c[2]]
    if len(base_pool) < 2:
        return None
    counter = Counter(c[2] for c in base_pool)
    base, count = counter.most_common(1)[0]
    # Require at least 2 declarations and majority signal.
    if count < 2:
        return None
    if count * 2 < len(base_pool):
        return None
    return (base, count)


def _prefer_api_base_from_evidence(candidates: List[tuple[str, str, str, str]]) -> str | None:
    """
    Deterministic fallback for universal API-base asks when top snippets are sparse.
    Prefer explicit Abstract* API bases first; otherwise return the most frequent base.
    """
    bases = [c[2] for c in candidates if c[2]]
    if not bases:
        return None
    for b in bases:
        bl = b.lower()
        if "abstractapi" in bl or (bl.startswith("abstract") and "api" in bl):
            return b
    counter = Counter(bases)
    return counter.most_common(1)[0][0]

