"""
Bounded, read-only answer composition for general Ask (PLAN_ONLY).

Uses the same deterministic shaping rules as the CLI (`shape_prompt_summary`) but
packs results into a structured, multi-paragraph payload for APIs and richer rendering.
Does not call vLLM and does not change governance posture.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from runtime.mcoder_cli.answer_shaping import shape_prompt_summary

_SCHEMA = "articulated_answer.v0"


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
