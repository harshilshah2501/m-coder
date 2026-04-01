"""
Authority → bounded coding reasoning (post–Phase 4).

Deterministic, no LLM: connects registry owner to debug/fix intent without code generation.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from runtime.context.contracts import ContextBundle


def infer_intent(query: str) -> str:
    """
    Classify user intent from query text.

    Returns one of: ``explore``, ``debug``, ``modify``.
    """
    q = (query or "").strip().lower()
    if not q:
        return "explore"

    # Order matters: more specific signals first
    debug_patterns = (
        r"\bdebug\b",
        r"\bwhy\b",
        r"\berror\b",
        r"\bexception\b",
        r"\bstack\s*trace\b",
        r"\bbug\b",
        r"\bfailure\b",
        r"\bcrash\b",
        r"\bnot\s+working\b",
        r"\bdoesn'?t\s+work\b",
    )
    modify_patterns = (
        r"\bfix\b",
        r"\bchange\b",
        r"\bmodify\b",
        r"\bimplement\b",
        r"\badd\b",
        r"\bupdate\b",
        r"\bpatch\b",
        r"\brefactor\b",
        r"\bedit\b",
        r"\bremove\b",
    )

    for p in debug_patterns:
        if re.search(p, q):
            return "debug"
    for p in modify_patterns:
        if re.search(p, q):
            return "modify"
    return "explore"


def extract_target(authority_resolution: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """
    True owner target from authority only (never from lexical hits).

    Returns keys: file, class, method (method may be empty).
    """
    if not authority_resolution or not isinstance(authority_resolution, dict):
        return None
    po = authority_resolution.get("primary_owner")
    if not isinstance(po, dict):
        return None
    f = str(po.get("file") or "").strip()
    c = str(po.get("class") or "").strip()
    m = str(po.get("method") or "").strip()
    if not f or not c:
        return None
    return {"file": f, "class": c, "method": m}


def _norm(p: str) -> str:
    return p.replace("\\", "/").strip().lower()


def _forbidden_norm_set(authority_resolution: Dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for d in authority_resolution.get("forbidden_distractors") or []:
        if isinstance(d, dict) and d.get("file"):
            out.add(_norm(str(d["file"])))
    return out


def generate_change_reasoning(
    bundle: ContextBundle,
    authority_resolution: Optional[Dict[str, Any]],
    intent: str,
) -> Optional[Dict[str, Any]]:
    """
    Produce bounded fix/debug reasoning tied to the registry owner.

    Rules:
    - ``validated``: strong action guidance
    - ``stale_candidate``: cautious action guidance
    - ``stale``: no actionable fix (verification required)
    - Distractor paths in the bundle never change the target (owner-only).

    Returns None when intent is not debug/modify or when no owner target exists.
    """
    if intent not in ("debug", "modify"):
        return None
    if not authority_resolution:
        return None

    target = extract_target(authority_resolution)
    if not target:
        return None

    status = str(authority_resolution.get("authority_status") or "unverified").lower()
    forbidden = _forbidden_norm_set(authority_resolution)

    # Lexical bundle may rank distractors high; record warning only, never retarget
    distractor_in_bundle = False
    for item in bundle.items[:8]:
        if _norm(item.path) in forbidden:
            distractor_in_bundle = True
            break

    tfile, tclass, tmethod = target["file"], target["class"], target["method"]
    method_clause = f" Start from method {tmethod}." if tmethod else ""

    if status == "stale":
        return {
            "action_level": "none",
            "target_file": tfile,
            "target_class": tclass,
            "target_method": tmethod,
            "reasoning": (
                "Authority for this concept is marked stale relative to the index or verification policy. "
                "Lexical retrieval order must not override the registry owner, but edits should not proceed "
                "until ownership and behavior are re-confirmed."
            ),
            "proposed_action": (
                "Do not apply an automated or assumed code fix from this session. "
                "Manually confirm the class still owns the behavior, then plan changes with a fresh trace."
            ),
            "distractor_in_bundle": distractor_in_bundle,
        }

    if status == "stale_candidate":
        reasoning = (
            f"Owner candidate {tclass} in {tfile} is plausible but not fully validated.{method_clause} "
            "Inspect call paths and tests before changing logic."
        )
        proposed = (
            f"Cautious next step: read {tfile}, trace callers into {tclass}, reproduce the issue locally, "
            f"then apply a minimal change scoped to {tclass}" + (f".{tmethod}" if tmethod else "") + "."
        )
        return {
            "action_level": "cautious",
            "target_file": tfile,
            "target_class": tclass,
            "target_method": tmethod,
            "reasoning": reasoning + (
                " Retrieval may surface distractor files; ignore them for ownership decisions."
                if distractor_in_bundle
                else ""
            ),
            "proposed_action": proposed,
            "distractor_in_bundle": distractor_in_bundle,
        }

    if status == "validated":
        reasoning = (
            f"Registry authority validates {tclass} as the implementation owner in {tfile}.{method_clause} "
            "Debug or modify work should center on this class unless new evidence contradicts the registry."
        )
        if distractor_in_bundle:
            reasoning += (
                " Lexical hits include known distractor paths; those are not alternative owners for this concept."
            )
        proposed = (
            f"Strong focus: open {tfile}, work in {tclass}"
            + (f".{tmethod}" if tmethod else "")
            + ", confirm behavior against domain notes and control flow, then apply a minimal, test-backed change."
        )
        return {
            "action_level": "strong",
            "target_file": tfile,
            "target_class": tclass,
            "target_method": tmethod,
            "reasoning": reasoning,
            "proposed_action": proposed,
            "distractor_in_bundle": distractor_in_bundle,
        }

    # unverified: cautious, not fake-strong fixes
    reasoning = (
        f"Authority is unverified for {tclass} in {tfile}.{method_clause} "
        "Treat the owner as a hint only; confirm with structure and tests before editing."
    )
    proposed = (
        f"Hedge next step: verify {tfile} still contains the active implementation of {tclass}, "
        "then scope any fix narrowly after reproduction."
    )
    if distractor_in_bundle:
        reasoning += " Ignore distractor-ranked files for ownership."
    return {
        "action_level": "cautious",
        "target_file": tfile,
        "target_class": tclass,
        "target_method": tmethod,
        "reasoning": reasoning,
        "proposed_action": proposed,
        "distractor_in_bundle": distractor_in_bundle,
    }


def change_reasoning_to_action_steps(result: Dict[str, Any]) -> List[str]:
    """Turn a change-reasoning dict into plain-text plan lines (no code fences)."""
    lines: List[str] = []
    level = str(result.get("action_level") or "none")
    lines.append(
        f"Action step (bounded reasoning, level={level}): "
        f"target file {result['target_file']}, class {result['target_class']}"
        + (f", method {result['target_method']}" if result.get("target_method") else "")
    )
    lines.append(f"Reasoning: {result['reasoning']}")
    lines.append(f"Proposed action: {result['proposed_action']}")
    return lines
