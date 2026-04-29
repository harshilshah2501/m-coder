"""
Bounded, read-only answer composition for general Ask (PLAN_ONLY).

Uses the same deterministic shaping rules as the CLI (`shape_prompt_summary`) but
packs results into a structured, multi-paragraph payload for APIs and richer rendering.
Does not call vLLM and does not change governance posture.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

from runtime.mcoder_cli.answer_shaping import shape_prompt_summary

_SCHEMA = "articulated_answer.v0"
_LEGACY_ENV = "MCODER_LEGACY_ASK_RENDERER"


def _strengthen_phrasing(text: str, evidence_quality: str) -> str:
    """Reduce timid hedging when evidence quality is STRONG (still bounded, not speculative)."""
    if str(evidence_quality or "").upper() != "STRONG":
        return text
    t = text
    repl = (
        ("appears to flow through", "flows through"),
        ("appears to run through", "runs through"),
        ("appears to center on", "centers on"),
        ("appears to follow", "follows"),
        ("The API layer appears to start", "The API layer starts"),
        ("Config stores appear to be organized", "Config stores are organized"),
        ("Mail server configuration appears to flow", "Mail server configuration flows"),
        ("The system appears to follow", "The system follows"),
        ("appears to be the main anchor", "is the primary anchor"),
    )
    for a, b in repl:
        if a in t:
            t = t.replace(a, b)
    return t


def _split_paragraphs(primary: str, secondary: str = "") -> List[str]:
    out: List[str] = []
    for block in (primary, secondary):
        b = (block or "").strip()
        if not b:
            continue
        parts = re.split(r"\n\s*\n+", b)
        for p in parts:
            p = p.strip()
            if p:
                out.append(p)
    # Merge ultra-short fragments into previous
    merged: List[str] = []
    for p in out:
        if merged and len(p) < 80 and not p.endswith("."):
            merged[-1] = merged[-1].rstrip() + " " + p
        else:
            merged.append(p)
    return merged[:6]


def _supporting_bullets_from_steps(plan_steps: List[str], limit: int = 5) -> List[str]:
    skip_prefixes = (
        "primary implementation owner:",
        "execution owner anchor",
        "authority status:",
        "explain/debug analysis completed",
    )
    bullets: List[str] = []
    for s in plan_steps:
        line = str(s).strip()
        if not line:
            continue
        low = line.lower()
        if any(low.startswith(p) for p in skip_prefixes):
            continue
        if "method-window excerpt:" in low or "visible method-window evidence:" in low:
            continue
        if line not in bullets:
            bullets.append(line)
        if len(bullets) >= limit:
            break
    return bullets


def _evidence_limit_note(metadata: Optional[Dict[str, Any]]) -> str:
    meta = metadata if isinstance(metadata, dict) else {}
    q = str(meta.get("evidence_quality") or "").upper()
    reasons = meta.get("quality_reasons") if isinstance(meta.get("quality_reasons"), list) else []
    r0 = str(reasons[0]) if reasons else ""
    if q == "STRONG":
        return "Evidence quality is strong for this ask; interpretation stays within retrieved anchors and plan steps."
    if q == "WEAK":
        return "Evidence quality is weak; expand symbols in the query or use Explain/Debug with a selected method for tighter grounding."
    if q == "NO_MATCH":
        return "Little or no grounded code evidence matched; treat this as exploratory guidance only."
    if r0:
        return f"Bounded by current retrieval ({r0})."
    return "Interpretation is bounded to the evidence bundle and deterministic plan steps (PLAN_ONLY)."


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _component_label(node: Dict[str, Any]) -> str:
    cls = str(node.get("class") or "").strip()
    method = str(node.get("method") or "").strip()
    if cls and method:
        return f"{cls}.{method}"
    return cls


def _collect_components(reasoning_context: Dict[str, Any]) -> Dict[str, List[str]]:
    typed = _as_dict(reasoning_context.get("typed_nodes"))
    groups: Dict[str, List[str]] = {}
    for bucket in ("entrypoints", "abstractions", "handlers", "stores", "collaborators"):
        out: List[str] = []
        for node in _as_list(typed.get(bucket)):
            if not isinstance(node, dict):
                continue
            label = _component_label(node)
            if label and label not in out:
                out.append(label)
        groups[bucket] = out
    return groups


def _render_list(items: List[str], limit: int = 3) -> str:
    shown = [f"`{x}`" for x in items[:limit] if x]
    if not shown:
        return ""
    if len(shown) == 1:
        return shown[0]
    if len(shown) == 2:
        return f"{shown[0]} and {shown[1]}"
    return ", ".join(shown[:-1]) + f", and {shown[-1]}"


def _query_intent(query: str) -> str:
    q = str(query or "").strip().lower()
    if "mail" in q:
        return "mail"
    if "notification" in q and any(k in q for k in ("find", "list", "class", "classes", "handle")):
        return "notification"
    if "config store" in q or "config stores" in q:
        return "config_store"
    return "api"


def _unified_paragraphs(
    *,
    query: str,
    reasoning_context: Dict[str, Any],
    evidence_quality: str,
) -> List[str]:
    groups = _collect_components(reasoning_context)
    owner = _as_dict(reasoning_context.get("primary_owner"))
    anchor = str(reasoning_context.get("anchor_method") or "").strip()
    owner_cls = str(owner.get("class") or "").strip()
    owner_method = str(owner.get("method") or "").strip()
    if not anchor and owner_cls:
        anchor = f"{owner_cls}.{owner_method}" if owner_method else owner_cls

    # Grounded component guard
    all_components: List[str] = []
    for key in ("entrypoints", "abstractions", "handlers", "stores", "collaborators"):
        for c in groups.get(key, []):
            if c not in all_components:
                all_components.append(c)
    if anchor and anchor not in all_components:
        all_components.insert(0, anchor)

    gaps = [str(g).strip() for g in _as_list(reasoning_context.get("coverage_gaps")) if str(g).strip()]
    if len(all_components) < 2:
        base = (
            f"The strongest grounded component is `{anchor}`."
            if anchor
            else "Available context is insufficient to confirm a full architecture flow."
        )
        if gaps:
            return [base + " The exact flow is not fully proven by current evidence."]
        if str(evidence_quality or "").upper() != "STRONG":
            return [base + " Additional grounded evidence is needed for a reliable flow explanation."]
        return [base]

    intent = _query_intent(query)
    abstractions = groups.get("abstractions", [])
    handlers = groups.get("handlers", [])
    stores = groups.get("stores", [])
    collaborators = groups.get("collaborators", [])
    flow_steps = [str(s).strip() for s in _as_list(reasoning_context.get("flow_steps")) if str(s).strip()]

    sentences: List[str] = []
    if intent == "mail":
        sentences.append(
            f"Mail server configuration centers on `{anchor}`, which acts as the update lifecycle entrypoint."
        )
        follow = _render_list(stores or collaborators or handlers, limit=3)
        if follow:
            sentences.append(f"It coordinates supporting components such as {follow} for validation and persistence-related behavior.")
    elif intent == "notification":
        owners = _render_list(([anchor] if anchor else []) + handlers, limit=3)
        collab = _render_list(collaborators or stores, limit=4)
        sentences.append(f"Notification handling is anchored around {owners or '`NotificationEngine`'}.")
        if collab:
            sentences.append(f"Related notification components include {collab}.")
    elif intent == "config_store":
        abs_label = _render_list(abstractions or ([anchor] if anchor else []), limit=2)
        sentences.append(
            f"Config store organization is centered on {abs_label or f'`{anchor}`'} as the shared abstraction for read/write operations."
        )
        concrete = _render_list(stores or collaborators, limit=3)
        if concrete:
            sentences.append(f"Concrete store and manager components include {concrete}.")
    else:
        sentences.append(f"The API architecture starts at `{anchor}` and routes into concrete handlers.")
        mid = _render_list(abstractions, limit=2)
        end = _render_list(handlers or collaborators or stores, limit=3)
        if mid and end:
            sentences.append(f"It relies on shared abstractions like {mid} and implementation components such as {end}.")
        elif end:
            sentences.append(f"Implementation components involved include {end}.")

    if flow_steps:
        step = " -> ".join(flow_steps[:2])
        if step:
            sentences.append(f"Flow evidence indicates: {step}.")

    # Keep 2-4 concise sentences total, with exactly one confidence sentence when gaps exist.
    if gaps:
        sentences = sentences[:3]
        sentences.append("The exact downstream call chain is not fully proven by current evidence.")
    else:
        sentences = sentences[:4]
    return [" ".join(s.strip() for s in sentences if s.strip())]


def _legacy_articulated_answer(
    *,
    query: str,
    plan_steps: List[str],
    context_files: List[Dict[str, Any]],
    graph_traversal: Optional[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    steps = [str(s).strip() for s in (plan_steps or []) if str(s).strip()]
    gt = graph_traversal if isinstance(graph_traversal, dict) else None
    resp: Dict[str, Any] = {"plan_summary": {"steps": steps}}
    if context_files:
        resp["context_bundle"] = {"files": context_files}
    if gt:
        resp["graph_traversal"] = gt

    shaped = shape_prompt_summary(query, resp)
    answer_1 = str(shaped.get("answer_1") or "").strip()
    next_step = str(shaped.get("next_step") or "").strip()

    if not answer_1 and not steps and not gt:
        return None
    eq = str((metadata or {}).get("evidence_quality") or "")
    if answer_1:
        answer_1 = _strengthen_phrasing(answer_1, eq)
    paragraphs = _split_paragraphs(answer_1, next_step if next_step else "")
    if not paragraphs and steps:
        paragraphs = [steps[0][:2000]]

    supporting = _supporting_bullets_from_steps(steps)
    graph_note = ""
    if isinstance(gt, dict) and gt.get("expanded_edges"):
        ee = gt.get("expanded_edges")
        if isinstance(ee, list) and ee:
            graph_note = "Graph context includes related structure edges (e.g. calls, routes, concepts) for this workspace snapshot."
    payload: Dict[str, Any] = {
        "schema_version": _SCHEMA,
        "paragraphs": paragraphs,
        "supporting_plan_bullets": supporting[:5],
        "evidence_limit": _evidence_limit_note(metadata),
        "shape": str(shaped.get("answer_shape") or ""),
    }
    if graph_note:
        payload["graph_context_note"] = graph_note
    if next_step and next_step not in "\n\n".join(paragraphs):
        payload["suggested_next_inspection"] = next_step
    return payload


def build_articulated_answer(
    *,
    query: str,
    plan_steps: List[str],
    context_files: List[Dict[str, Any]],
    graph_traversal: Optional[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Build additive articulated_answer block. Returns None when there is nothing to say
    (e.g. empty plan and no graph).
    """
    if str(os.environ.get(_LEGACY_ENV, "")).strip() in {"1", "true", "TRUE", "yes", "on"}:
        return _legacy_articulated_answer(
            query=query,
            plan_steps=plan_steps,
            context_files=context_files,
            graph_traversal=graph_traversal,
            metadata=metadata,
        )

    steps = [str(s).strip() for s in (plan_steps or []) if str(s).strip()]
    if not steps and not context_files and not isinstance(graph_traversal, dict):
        return None

    md = _as_dict(metadata)
    rc = _as_dict(md.get("reasoning_context"))
    eq = str(md.get("evidence_quality") or "")
    paragraphs = _unified_paragraphs(query=query, reasoning_context=rc, evidence_quality=eq)
    if not paragraphs and steps:
        paragraphs = [steps[0][:300]]
    if not paragraphs:
        return None

    payload: Dict[str, Any] = {
        "schema_version": _SCHEMA,
        "paragraphs": paragraphs[:1],
        "supporting_plan_bullets": _supporting_bullets_from_steps(steps)[:5],
        "evidence_limit": _evidence_limit_note(metadata),
        "shape": "unified_contract",
    }
    return payload
