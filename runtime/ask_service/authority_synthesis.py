"""
Deterministic answer / plan anchoring from ``authority_resolution`` (Phase 4).

No LLM: produces bounded plan steps for Plan-Gate when evidence carries authority.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from runtime.context.contracts import ContextBundle

from runtime.layer5.authority.authority_code_reasoning import (
    change_reasoning_to_action_steps,
    generate_change_reasoning,
    infer_intent,
)


def _norm_path(p: str) -> str:
    return p.replace("\\", "/").strip().lower()


def _forbidden_paths(authority_resolution: Dict[str, Any]) -> Set[str]:
    out: Set[str] = set()
    for d in authority_resolution.get("forbidden_distractors") or []:
        if isinstance(d, dict) and d.get("file"):
            out.add(_norm_path(str(d["file"])))
    return out


def _collaborator_paths(authority_resolution: Dict[str, Any]) -> Set[str]:
    """Registry collaborator paths (supporting context, not co-owners)."""
    out: Set[str] = set()
    for c in authority_resolution.get("collaborators") or []:
        if isinstance(c, dict) and c.get("file"):
            out.add(_norm_path(str(c["file"])))
    return out


def _stale_uncertainty(status: str, confidence: str) -> bool:
    s = (status or "").lower()
    if s in ("stale", "stale_candidate", "unverified"):
        return True
    return confidence in ("weak", "none")


def synthesize_authority_plan_steps(
    query: str,
    bundle: ContextBundle,
    authority_resolution: Optional[Dict[str, Any]],
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Build plan steps anchored to registry authority.

    Returns:
        steps: ordered strings (deterministic)
        meta: flags for tests / logging (e.g. anchor_mode, distractor_suppressed)
    """
    meta: Dict[str, Any] = {"anchor_mode": "none", "distractor_suppressed": False}

    if not authority_resolution:
        return [], meta

    ar = authority_resolution
    status = str(ar.get("authority_status") or "unverified")
    conf = str(ar.get("authority_confidence") or "none")
    primary = ar.get("primary_owner") or {}
    if not isinstance(primary, dict):
        return [], meta

    p_file = str(primary.get("file") or "").strip()
    p_class = str(primary.get("class") or "").strip()
    p_method = str(primary.get("method") or "").strip()
    if not p_file or not p_class:
        return [], meta

    meta["anchor_mode"] = "anchored" if status == "validated" and conf in ("high", "medium") else "weak_or_stale"

    forbidden = _forbidden_paths(ar)
    steps: List[str] = []

    if _stale_uncertainty(status, conf):
        meta["uncertainty"] = True
        steps.append(
            f"Authority status is {status} (confidence: {conf}). "
            "Treat the following as provisional; verify against the current codebase."
        )
    else:
        meta["uncertainty"] = False

    # Primary owner block (never omit file + class when authority exists)
    role_line = ""
    cf = ar.get("control_flow") or []
    if isinstance(cf, list) and cf:
        role_line = " Control flow trace: " + " → ".join(str(x) for x in cf[:6]) + "."
    method_bit = f", method `{p_method}`" if p_method else ""
    steps.append(
        f"Primary implementation owner: `{p_class}` in `{p_file}`{method_bit}.{role_line}"
    )

    # Collaborators as supporting only
    collab = _collaborator_paths(ar)
    if collab:
        preview = ", ".join(sorted(collab))[:400]
        steps.append(
            f"Supporting context only (collaborators; not alternative owners): related paths include {preview}."
        )

    # Explicit non-owners (distractors) — never as peers
    distr_lines: List[str] = []
    for d in ar.get("forbidden_distractors") or []:
        if not isinstance(d, dict):
            continue
        df = str(d.get("file") or "").strip()
        reason = str(d.get("reason") or "").strip()
        if not df:
            continue
        distr_lines.append(f"`{df}` — excluded as distractor (not owner): {reason}")
        meta["distractor_suppressed"] = True
    if distr_lines:
        steps.append(
            "Files explicitly marked as NOT the owner (do not treat as alternative owners): "
            + " ".join(distr_lines[:4])
        )

    # Notes
    notes = ar.get("notes") or []
    if isinstance(notes, list) and notes:
        steps.append("Domain notes: " + " | ".join(str(n) for n in notes[:5]))

    # Entry trace when present
    et = ar.get("entry_trace")
    if isinstance(et, dict) and et.get("path"):
        steps.append("Entry / path trace: " + " → ".join(str(x) for x in et["path"][:8]))

    # Compound: separate blocks per matched concept
    if ar.get("compound") and isinstance(ar.get("matched_concepts"), list):
        extra: List[str] = []
        for mc in ar["matched_concepts"][1:]:
            if not isinstance(mc, dict):
                continue
            po2 = mc.get("primary_owner") or {}
            if not isinstance(po2, dict):
                continue
            cname = str(mc.get("concept_id") or "concept")
            f2 = str(po2.get("file") or "")
            cl2 = str(po2.get("class") or "")
            if f2 and cl2:
                extra.append(f"Additional concept `{cname}`: owner `{cl2}` in `{f2}`.")
        steps.extend(extra[:6])

    # Guard: do not echo generic “check these files” without anchor when we have authority
    # (steps above already anchor; bundle top paths may include distractors — warn once)
    top_paths = [_norm_path(item.path) for item in bundle.items[:5]]
    for tp in top_paths:
        if tp in forbidden:
            meta["distractor_in_lexical_topk"] = True
            steps.append(
                "Lexical retrieval still ranks a known distractor file highly; "
                "do not treat it as an owner — follow primary_owner above."
            )
            break

    intent = infer_intent(query)
    meta["intent"] = intent
    cr = generate_change_reasoning(bundle, authority_resolution, intent)
    if cr:
        meta["change_reasoning"] = cr
        steps.extend(change_reasoning_to_action_steps(cr))

    return steps, meta


def merge_plan_with_authority(
    generic_steps: List[str],
    authority_steps: List[str],
    authority_resolution: Optional[Dict[str, Any]],
) -> List[str]:
    """Prefer authority-first steps when resolution exists; otherwise generic."""
    if authority_resolution and authority_steps:
        return authority_steps
    return generic_steps
