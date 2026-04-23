"""
Deterministic answer / plan anchoring from ``authority_resolution`` (Phase 4).

No LLM: produces bounded plan steps for Plan-Gate when evidence carries authority.
"""

from __future__ import annotations

import re
from pathlib import Path
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


def _status_message(status: str, confidence: str) -> str:
    """Human-readable lifecycle wording without changing runtime semantics."""
    s = (status or "unverified").lower()
    conf = (confidence or "none").lower()
    if s == "validated":
        return f"Authority status: validated. Confidence: {conf}."
    if s == "stale_candidate":
        return (
            f"Authority status: stale_candidate. Confidence: {conf}. "
            "Structural owner mapping exists, but freshness/secondary checks are not fully strong."
        )
    if s == "stale":
        return (
            f"Authority status: stale. Confidence: {conf}. "
            "Owner mapping may still resolve, but verification metadata is out of date."
        )
    return (
        f"Authority status: unverified. Confidence: {conf}. "
        "Owner mapping was not validated strongly enough for high-trust actioning."
    )


def _is_how_it_works_query(query: str) -> bool:
    q = (query or "").lower()
    return "how" in q and ("work" in q or "flow" in q or "architecture" in q)


def _primary_owner_snippet(bundle: ContextBundle, owner_file: str) -> str:
    """
    Best-effort snippet lookup for the authority owner in a ContextBundle.
    Matches by normalized suffix so `src/...` and `motadata/src/...` both work.
    """
    owner_norm = _norm_path(owner_file)
    if not owner_norm:
        return ""
    for item in bundle.items:
        p = _norm_path(item.path)
        if p == owner_norm or p.endswith("/" + owner_norm):
            txt = " ".join(str(item.content or "").split())
            return txt[:220].rstrip()
    return ""


def _owner_item_content(bundle: ContextBundle, owner_file: str) -> str:
    owner_norm = _norm_path(owner_file)
    if not owner_norm:
        return ""
    for item in bundle.items:
        p = _norm_path(item.path)
        if p == owner_norm or p.endswith("/" + owner_norm):
            return str(item.content or "")
    return ""


def _snippet_mentions_method(snippet: str, method: str) -> bool:
    m = str(method or "").strip()
    if not m:
        return True
    hay = str(snippet or "")
    if not hay:
        return False
    esc = re.escape(m)
    # declaration or invocation
    if re.search(rf"\b{esc}\s*\(", hay):
        return True
    # registry method can also be a lifecycle token in comments / docs
    if re.search(rf"\b{esc}\b", hay):
        return True
    return False


def _extract_method_window(content: str, method: str, cap_chars: int = 260) -> str:
    """
    Best-effort extract around a method declaration/invocation in owner snippet content.

    Returns a compact single-line window or empty string when method anchor is missing.
    """
    txt = str(content or "")
    m = str(method or "").strip()
    if not txt or not m:
        return ""
    esc = re.escape(m)
    # Prefer declaration-like pattern, fallback to any mention.
    pat = re.compile(
        rf"(?:public|private|protected|static|final|\s)+[^\n\r{{;]*?\b{esc}\s*\([^;\n\r]*\)\s*\{{?",
        flags=re.IGNORECASE,
    )
    hit = pat.search(txt)
    if hit is None:
        hit = re.search(rf"\b{esc}\s*\(", txt)
    if hit is None:
        return ""
    start = max(0, hit.start() - 80)
    end = min(len(txt), hit.end() + 160)
    win = " ".join(txt[start:end].split())
    return win[:cap_chars].rstrip()


def _load_owner_source_from_root(bundle: ContextBundle, owner_file: str, cap_bytes: int = 262_144) -> str:
    """Best-effort bounded owner-file read from provenance root for proof-density enrichment."""
    root = str(getattr(bundle.provenance, "root_path", "") or "").strip()
    rel = str(owner_file or "").strip()
    if not root or not rel:
        return ""
    root_p = Path(root)
    candidates = [root_p / rel, root_p / f"motadata/{rel}"]
    for p in candidates:
        try:
            if p.exists() and p.is_file():
                raw = p.read_bytes()[:cap_bytes]
                return raw.decode("utf-8", errors="replace")
        except Exception:
            continue
    return ""


def _stitch_execution_path(authority_resolution: Dict[str, Any], owner_class: str, owner_method: str) -> str:
    """
    Deterministic execution-path stitch for Ask explanations.

    Uses entry_trace path + control_flow when present to produce an explicit call/flow chain.
    """
    hops: List[str] = []
    et = authority_resolution.get("entry_trace")
    if isinstance(et, dict):
        p = et.get("path")
        if isinstance(p, list):
            for x in p[:3]:
                sx = str(x).strip()
                if sx:
                    hops.append(sx)
    owner_hop = owner_class + (f".{owner_method}" if owner_method else "")
    if owner_hop and owner_hop not in hops:
        hops.append(owner_hop)

    cf = authority_resolution.get("control_flow")
    if isinstance(cf, list):
        for x in cf[:3]:
            sx = str(x).strip()
            if sx and sx not in hops:
                hops.append(sx)
    if len(hops) < 2:
        return ""
    return "Execution-path stitch: " + " -> ".join(hops[:6]) + "."


def _owner_domain_key(path: str) -> str:
    norm = _norm_path(path)
    i = norm.find("com/mindarray/")
    if i == -1:
        return ""
    tail = norm[i + len("com/mindarray/") :]
    seg = tail.split("/", 1)[0]
    return seg


def _shape_collaborators(
    collab: Set[str],
    *,
    owner_file: str,
    bundle: ContextBundle,
    cap: int = 4,
) -> List[str]:
    """Prefer collaborators close to owner domain and currently in context bundle."""
    if not collab:
        return []
    owner_norm = _norm_path(owner_file)
    owner_dir = owner_norm.rsplit("/", 1)[0] if "/" in owner_norm else owner_norm
    owner_domain = _owner_domain_key(owner_norm)
    bundle_paths = {_norm_path(it.path) for it in bundle.items}

    ordered = sorted(collab)
    bucket_in_bundle: List[str] = []
    bucket_same_dir: List[str] = []
    bucket_same_domain: List[str] = []
    bucket_other: List[str] = []

    for p in ordered:
        pn = _norm_path(p)
        if pn in bundle_paths or any(bp.endswith("/" + pn) for bp in bundle_paths):
            bucket_in_bundle.append(p)
            continue
        pdir = pn.rsplit("/", 1)[0] if "/" in pn else pn
        if owner_dir and pdir == owner_dir:
            bucket_same_dir.append(p)
            continue
        if owner_domain and _owner_domain_key(pn) == owner_domain:
            bucket_same_domain.append(p)
            continue
        bucket_other.append(p)

    shaped = bucket_in_bundle + bucket_same_dir + bucket_same_domain + bucket_other
    return shaped[:cap]


def prioritize_owner_in_bundle(
    bundle: ContextBundle,
    authority_resolution: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Soft owner top1 bias for Ask context shaping only (no retrieval/ranking rewrite).
    """
    meta: Dict[str, Any] = {
        "owner_promoted_for_context": False,
        "owner_original_rank_in_bundle": None,
        "owner_rank_after_bias": None,
    }
    if not authority_resolution:
        return meta
    po = authority_resolution.get("primary_owner")
    po = po if isinstance(po, dict) else {}
    owner_file = str(po.get("file") or "").strip()
    if not owner_file or not getattr(bundle, "items", None):
        return meta
    owner_norm = _norm_path(owner_file)
    idx = -1
    for i, it in enumerate(bundle.items):
        p = _norm_path(it.path)
        if p == owner_norm or p.endswith("/" + owner_norm):
            idx = i
            break
    if idx < 0:
        return meta
    meta["owner_original_rank_in_bundle"] = idx + 1
    if idx > 0:
        item = bundle.items.pop(idx)
        bundle.items.insert(0, item)
        meta["owner_promoted_for_context"] = True
    meta["owner_rank_after_bias"] = 1
    return meta


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
            _status_message(status, conf) + " "
            "Treat the following as provisional; verify against the current codebase."
        )
    else:
        meta["uncertainty"] = False

    # Primary owner block (never omit file + class when authority exists)
    role_line = ""
    cf = ar.get("control_flow") or []
    if isinstance(cf, list) and cf:
        role_line = " Control flow trace: " + " → ".join(str(x) for x in cf[:6]) + "."
    owner_content = _owner_item_content(bundle, p_file)
    source_used = "snippet_window"
    method_supported = _snippet_mentions_method(owner_content, p_method)
    method_window = _extract_method_window(owner_content, p_method) if method_supported else ""
    if p_method and not method_supported:
        full_src = _load_owner_source_from_root(bundle, p_file)
        if full_src:
            full_supported = _snippet_mentions_method(full_src, p_method)
            if full_supported:
                method_supported = True
                method_window = _extract_method_window(full_src, p_method)
                source_used = "owner_file_surfacing"
    meta["method_claim_alignment_pass"] = bool(method_supported)
    meta["method_window_visible"] = bool(method_window)
    meta["method_window_source"] = source_used if method_window else "none"
    method_bit = f", method `{p_method}`" if p_method and method_supported else ""
    steps.append(
        f"Primary implementation owner: `{p_class}` in `{p_file}`{method_bit}.{role_line}"
    )
    if p_method and not method_supported:
        steps.append(
            f"Method-level owner hook `{p_method}` is authority-derived; current owner snippet window does not expose that method body."
        )

    if _is_how_it_works_query(query):
        snippet = _primary_owner_snippet(bundle, p_file)
        how = (
            f"How it works (grounded): `{p_class}`"
            + (f".`{p_method}`" if p_method and method_supported else "")
            + " is the main execution path for this behavior."
        )
        if method_window:
            how += f" Method-window excerpt: {method_window}"
        elif snippet:
            how += f" Evidence excerpt: {snippet}"
        steps.append(how)
    elif method_window:
        steps.append(f"Visible method-window evidence: {method_window}")

    stitched = _stitch_execution_path(ar, p_class, p_method if method_supported else "")
    if stitched:
        steps.append(stitched)

    # Collaborators as supporting only
    collab = _collaborator_paths(ar)
    if collab:
        shaped = _shape_collaborators(collab, owner_file=p_file, bundle=bundle)
        meta["collaborator_paths_total"] = len(collab)
        meta["collaborator_paths_emitted"] = len(shaped)
        preview = ", ".join(shaped)[:400]
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

    ar_for_reasoning = ar
    if p_method and not method_supported:
        po = dict(primary)
        po["method"] = ""
        ar_for_reasoning = dict(ar)
        ar_for_reasoning["primary_owner"] = po

    intent = infer_intent(query)
    meta["intent"] = intent
    cr = generate_change_reasoning(bundle, ar_for_reasoning, intent)
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
        # Preserve structural direct answers from deterministic planner for class
        # relationship asks, then append authority owner/context details.
        if generic_steps:
            first = str(generic_steps[0] or "").strip()
            first_l = first.lower()
            if first_l.startswith("direct answer (grounded):") and any(
                tok in first_l
                for tok in (
                    "base class",
                    "common api base class",
                    "api base-class",
                    "extends",
                    "implements",
                )
            ):
                if not authority_steps or first != authority_steps[0]:
                    return [first] + authority_steps
        return authority_steps
    return generic_steps
