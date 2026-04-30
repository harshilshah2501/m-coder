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

from runtime.mcoder_cli.answer_shaping import _is_structural_query, shape_prompt_summary

_SCHEMA = "articulated_answer.v0"
_LEGACY_ENV = "MCODER_LEGACY_ASK_RENDERER"

# When graph paths are absent, reasoning_context always adds these; they describe
# snapshot limits, not failures — STRONG asks should not end with a forensic disclaimer.
_ROUTINE_COVERAGE_GAPS = frozenset(
    {
        "Full request routing not resolved in current evidence.",
        "Persistence/store call chain not resolved.",
        "No graph call-paths available; flow is inferred from class names only.",
    }
)


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
        return "This answer stays within the code evidence and plan steps attached to this run."
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


def _dedupe_labels(items: List[str], *, drop: Optional[str] = None) -> List[str]:
    """Drop duplicates and optional anchor label so we do not repeat `Cls.method` twice."""
    seen: set[str] = set()
    out: List[str] = []
    drop_key = (drop or "").strip().lower()
    for raw in items:
        label = str(raw or "").strip()
        if not label:
            continue
        key = label.lower()
        if drop_key and key == drop_key:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(label)
    return out


def _render_list(items: List[str], limit: int = 3, *, drop: Optional[str] = None) -> str:
    uniq = _dedupe_labels(items, drop=drop)
    shown = [f"`{x}`" for x in uniq[:limit] if x]
    if not shown:
        return ""
    if len(shown) == 1:
        return shown[0]
    if len(shown) == 2:
        return f"{shown[0]} and {shown[1]}"
    return ", ".join(shown[:-1]) + f", and {shown[-1]}"


def _render_class_list(items: List[str], limit: int = 3, *, drop: Optional[str] = None) -> str:
    classes: List[str] = []
    for raw in items:
        c = _class_from_component_label(str(raw))
        if c:
            classes.append(c)
    drop_cls = _class_from_component_label(drop or "")
    return _render_list(classes, limit=limit, drop=drop_cls or None)


def _routine_coverage_only(gaps: List[str]) -> bool:
    if not gaps:
        return False
    for g in gaps:
        if str(g).strip() not in _ROUTINE_COVERAGE_GAPS:
            return False
    return True


def _should_append_chain_disclaimer(evidence_quality: str, gaps: List[str]) -> bool:
    if not gaps:
        return False
    if str(evidence_quality or "").upper() == "STRONG" and _routine_coverage_only(gaps):
        return False
    return True


def _query_intent(query: str) -> str:
    q = str(query or "").strip().lower()
    # Discovery-style notification queries often include "email"/"sms";
    # classify these before "mail" to avoid forcing the mail-config template.
    if (
        any(k in q for k in ("notification", "email", "sms"))
        and any(k in q for k in ("find", "list", "class", "classes", "handle", "involved"))
    ):
        return "notification"
    if re.search(r"\bmail\b", q):
        return "mail"
    if "config store" in q or "config stores" in q:
        return "config_store"
    if "alert" in q and any(k in q for k in ("enrichment", "correlation", "ingest", "pipeline")):
        return "alert_flow"
    return "api"


def _is_planning_or_refactor_query(q: str) -> bool:
    """User intent: design/change work, not a live architecture tour of the API layer."""
    ql = str(q or "").strip().lower()
    if ql.startswith("plan ") or " plan " in ql:
        return True
    return any(
        k in ql
        for k in (
            "refactor",
            "rollback",
            "migration",
            "safe change",
            "roll out",
            "rollout",
            "feature flag",
            "phased",
        )
    )


def _class_from_component_label(label: str) -> str:
    s = str(label or "").strip()
    if not s:
        return ""
    return s.split(".")[0].strip()


def _is_api_base_class_question(query: str) -> bool:
    """User asks for the superclass of REST/handler APIs — not the Vert.x Verticle server type."""
    ql = str(query or "").strip().lower()
    if not any(
        k in ql
        for k in ("base class", "parent class", "which class", "what class", "extends", "implements")
    ):
        return False
    return bool(
        any(k in ql for k in (" api", "apis", "rest", "handler"))
        or "all apis" in ql.replace("'", "")
        or ql.startswith("which class is the base class for all apis")
    )


def _find_abstract_api_in_context(groups: Dict[str, List[str]], reasoning_context: Dict[str, Any]) -> str:
    """Locate AbstractAPI from typed buckets (labels are `Class.method` strings)."""
    for lab in groups.get("abstractions", []):
        if _class_from_component_label(str(lab)) == "AbstractAPI":
            return "AbstractAPI"
    typed = _as_dict(reasoning_context.get("typed_nodes"))
    for bucket in ("abstractions", "handlers", "entrypoints", "collaborators"):
        for node in _as_list(typed.get(bucket)):
            if not isinstance(node, dict):
                continue
            if str(node.get("class") or "").strip() == "AbstractAPI":
                return "AbstractAPI"
    return ""


def _chain_contains_class(chain: List[str], name: str) -> bool:
    want = name.strip().lower()
    for raw in chain:
        if _class_from_component_label(str(raw)).lower() == want:
            return True
    return False


def _is_api_layer_architecture_query(ql: str) -> bool:
    """Broad architecture tour of the API layer (not a single-method drill)."""
    return ("architecture" in ql or ("explain" in ql and "layer" in ql)) and ("api" in ql or "api layer" in ql)


def _planning_lede_from_steps(plan_steps: List[str]) -> str:
    """First substantive plan lines, skipping owner preambles and raw evidence dumps."""
    skip_prefixes = (
        "primary implementation owner:",
        "execution owner anchor",
        "authority status:",
        "explain/debug analysis completed",
    )
    parts: List[str] = []
    for raw in plan_steps:
        line = str(raw).strip()
        if not line:
            continue
        low = line.lower()
        if any(low.startswith(p) for p in skip_prefixes):
            continue
        if "method-window excerpt:" in low or "visible method-window evidence:" in low:
            continue
        if line not in parts:
            parts.append(line)
        if len(parts) >= 2:
            break
    if not parts:
        return ""
    out = " ".join(parts)
    if len(out) > 1200:
        return out[:1197] + "..."
    return out


def _unified_paragraphs(
    *,
    query: str,
    reasoning_context: Dict[str, Any],
    evidence_quality: str,
    plan_steps: Optional[List[str]] = None,
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
    inh = _as_dict(reasoning_context.get("inheritance"))
    chain = [str(x).strip() for x in _as_list(inh.get("chain")) if str(x).strip()]
    ql = str(query or "").strip().lower()
    steps_for_plan = list(plan_steps or [])

    # Planning / refactor: prefer real plan steps over the generic "API layer starts at…" template.
    if _is_planning_or_refactor_query(query):
        lede = _planning_lede_from_steps(steps_for_plan)
        if lede:
            extra = ""
            if "alert" in ql or "enrichment" in ql:
                extra = " Validate alert and enrichment call sites in the workspace before applying changes."
            return [lede + " Use the numbered plan steps and evidence paths below for sequencing and checkpoints." + extra]
        if steps_for_plan:
            return [
                "This is a planning-oriented question: use the plan steps and evidence references below as the source of truth for ordering and rollback notes."
            ]

    # Structural (base class / inheritance): never use the generic API-layer paragraph.
    if _is_structural_query(query):
        chain_txt = " → ".join(f"`{c}`" for c in chain) if chain else ""
        class_q = any(
            k in ql
            for k in ("base class", "parent class", "extends", "implements", "what class", "which class")
        )
        if class_q:
            # REST handler base (AbstractAPI) vs Vert.x Verticle server chain — do not conflate.
            if _is_api_base_class_question(query):
                api_root = _find_abstract_api_in_context(groups, reasoning_context)
                vert_only = bool(chain) and _class_from_component_label(str(chain[-1])) == "AbstractVerticle"
                if api_root and vert_only and not _chain_contains_class(chain, "AbstractAPI"):
                    return [
                        (
                            f"`{api_root}` is the shared superclass for concrete REST/API handler classes in this codebase. "
                            f"The chain in evidence ({chain_txt}) reflects the Vert.x HTTP server type hierarchy (`Verticle`), "
                            f"which is separate from handler classes extending `{api_root}`."
                        )
                    ]
                if chain and _chain_contains_class(chain, "AbstractAPI"):
                    idx = next(
                        i
                        for i, x in enumerate(chain)
                        if _class_from_component_label(str(x)) == "AbstractAPI"
                    )
                    sub = chain[: idx + 1]
                    st = " → ".join(f"`{c}`" for c in sub)
                    return [
                        (
                            f"In the grounded inheritance evidence, `AbstractAPI` is the superclass at the base of this API handler chain: "
                            f"{st}. Concrete `*API` classes implement request behavior on top of that type."
                        )
                    ]
                if api_root:
                    return [
                        (
                            f"`{api_root}` is the shared superclass for concrete REST/API handler classes. "
                            f"Confirm `extends` on concrete `*API` classes when the graph chain is partial or shows only deployment types."
                        )
                    ]
                if vert_only and chain:
                    return [
                        (
                            f"The inheritance chain in current evidence is {chain_txt} (Vert.x `Verticle` / server deployment). "
                            f"That documents the HTTP server type, not REST handler inheritance; inspect concrete `*API` sources for `extends AbstractAPI`."
                        )
                    ]
            if chain:
                if class_q:
                    root = chain[-1]
                    return [
                        (
                            f"In the grounded inheritance evidence, `{root}` is the superclass at the base of this chain: "
                            f"{chain_txt}. Subclasses extend that type per the inheritance edges visible in this snapshot."
                        )
                    ]
                return [f"Inheritance in current evidence: {chain_txt}."]
        abs_first = _find_abstract_api_in_context(groups, reasoning_context)
        if not abs_first:
            for lab in groups.get("abstractions", []):
                c0 = _class_from_component_label(str(lab))
                if c0:
                    abs_first = c0
                    break
        if abs_first:
            return [
                f"In this snapshot, the strongest grounded abstraction is `{abs_first}`. "
                f"Use source `extends` / `implements` edges to confirm which concrete classes tie back to it."
            ]
        if class_q:
            return [
                "Could not resolve a grounded inheritance chain for this API base-class question in the current snapshot. "
                "Run Explain/Debug with a concrete `*API` file selected, or narrow the Ask to a known API class symbol."
            ]

    if len(all_components) < 2:
        base = (
            f"The strongest grounded component is `{anchor}`."
            if anchor
            else "Available context is insufficient to confirm a full architecture flow."
        )
        if gaps:
            return [base + " The full downstream chain is not fully visible in this snapshot."]
        if str(evidence_quality or "").upper() != "STRONG":
            return [base + " Additional grounded evidence is needed for a reliable flow explanation."]
        return [base]

    intent = _query_intent(query)
    abstractions = groups.get("abstractions", [])
    handlers = groups.get("handlers", [])
    stores = groups.get("stores", [])
    collaborators = groups.get("collaborators", [])

    # 2–3 direct sentences: active voice, no pasted flow_steps (avoids G# / diagnostic traces).
    sentences: List[str] = []
    if intent == "mail":
        anchor_cls = _class_from_component_label(anchor) or "MailServerConfiguration"
        sentences.append(
            f"Mail server configuration is handled by `{anchor_cls}`, with lifecycle hooks coordinating validation before settings are persisted."
        )
        follow = _render_class_list(stores or collaborators or handlers, limit=3, drop=anchor)
        if follow:
            sentences.append(
                f"It works with {follow} for transport settings, validation, and persistence boundaries."
            )
    elif intent == "notification":
        owners = _render_class_list(([anchor] if anchor else []) + handlers, limit=2, drop=None)
        head = owners or "`NotificationEngine`"
        collab = _render_class_list(collaborators or stores, limit=4, drop=anchor)
        sentences.append(
            f"Notification handling centers on {head}, coordinating dispatch across notification-related components."
        )
        if collab:
            sentences.append(f"Key collaborators include {collab} for routing, configuration, and supporting services.")
    elif intent == "config_store":
        abs_label = _render_class_list(abstractions or ([anchor] if anchor else []), limit=2, drop=anchor)
        abs_ref = abs_label or f"`{anchor}`"
        sentences.append(
            f"Config stores are organized around {abs_ref}, which provides the shared store contract for configuration reads and writes."
        )
        concrete = _render_class_list(stores or collaborators, limit=3, drop=anchor)
        if concrete:
            sentences.append(
                f"Concrete implementations such as {concrete} handle domain-specific retrieval, validation, and update behavior."
            )
    elif intent == "alert_flow":
        parts = _render_list(handlers or collaborators, limit=4, drop=anchor)
        anchor_bit = f"`{anchor}`" if anchor else "the entry components in evidence"
        if parts:
            sentences.append(
                f"Alert and enrichment behavior in this snapshot is centered on {anchor_bit}, working together with {parts}."
            )
        else:
            sentences.append(
                f"Alert-side processing in this snapshot is anchored at {anchor_bit}; review handlers and collaborators in the plan steps for the full flow."
            )
    else:
        if _is_api_layer_architecture_query(ql):
            ep = _render_class_list(groups.get("entrypoints", []), limit=1, drop=None)
            mid = _render_class_list(abstractions, limit=2, drop=anchor)
            end = _render_class_list(handlers or collaborators or stores, limit=4, drop=anchor)
            bits: List[str] = []
            if ep:
                bits.append(f"{ep} is the HTTP/API entry; it wires the server and routes requests to handlers.")
            elif anchor:
                bits.append(f"`{_class_from_component_label(anchor) or anchor}` is the strongest resolved API entry anchor in this snapshot.")
            else:
                bits.append("The API entrypoint is not clearly resolved in this snapshot.")
            if mid:
                bits.append(f"Concrete REST handlers extend {mid} for shared routing and lifecycle behavior.")
            if end:
                bits.append(f"Representative implementation classes in this snapshot include {end}.")
            if bits:
                sentences.append(" ".join(bits))
            else:
                sentences.append(
                    f"The API layer starts at `{anchor}`, which bootstraps routing and delegates requests to concrete handlers."
                )
                mid2 = _render_list(abstractions, limit=2, drop=anchor)
                end2 = _render_list(handlers or collaborators or stores, limit=3, drop=anchor)
                if mid2 and end2:
                    sentences.append(
                        f"Shared lifecycle behavior flows through {mid2}, and work coordinates with {end2}."
                    )
                elif end2:
                    sentences.append(f"Key implementation components include {end2}.")
                elif mid2:
                    sentences.append(f"Shared abstractions include {mid2}.")
        else:
            sentences.append(
                f"The API layer starts at `{anchor}`, which bootstraps routing and delegates requests to concrete handlers."
            )
            mid = _render_list(abstractions, limit=2, drop=anchor)
            end = _render_list(handlers or collaborators or stores, limit=3, drop=anchor)
            if mid and end:
                sentences.append(
                    f"Shared lifecycle behavior flows through {mid}, and work coordinates with {end}."
                )
            elif end:
                sentences.append(f"Key implementation components include {end}.")
            elif mid:
                sentences.append(f"Shared abstractions include {mid}.")

    # One bounded-confidence sentence only when gaps are non-routine or evidence is not STRONG.
    if gaps and _should_append_chain_disclaimer(evidence_quality, gaps):
        sentences = sentences[:3]
        sentences.append("The full downstream chain is not fully visible in this snapshot.")
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
    paragraphs = _unified_paragraphs(
        query=query,
        reasoning_context=rc,
        evidence_quality=eq,
        plan_steps=steps,
    )
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
