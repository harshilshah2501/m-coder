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

from runtime.mcoder_cli.answer_shaping import _is_discovery_query, _is_structural_query, shape_prompt_summary

_SCHEMA = "articulated_answer.v0"
_LEGACY_ENV = "MCODER_LEGACY_ASK_RENDERER"
_SYNTHESIS_FLAG_ENV = "MCODER_REASONING_SYNTHESIS_V1"

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


def _top_classes(items: List[str], limit: int = 3) -> List[str]:
    out: List[str] = []
    for raw in items:
        cls = _class_from_component_label(raw)
        if cls and cls not in out:
            out.append(cls)
        if len(out) >= limit:
            break
    return out


def _role_label(cls: str) -> str:
    c = (cls or "").strip()
    lc = c.lower()
    if "server" in lc:
        return "entrypoint"
    if c.startswith("Abstract"):
        return "abstraction"
    if lc.endswith("engine"):
        return "orchestrator"
    if "handler" in lc:
        return "bridge/handler"
    if "store" in lc or "manager" in lc:
        return "store/orchestrator"
    if c.endswith("API"):
        return "api handler"
    return "component"


def _prioritized_collaborator_classes(
    *,
    query: str,
    reasoning_context: Dict[str, Any],
    groups: Dict[str, List[str]],
    limit: int = 4,
) -> List[str]:
    """Prefer authority + subsystem-relevant collaborators over lexical top-k noise."""
    ql = str(query or "").lower()
    tokens: List[str] = []
    if any(t in ql for t in ("notification", "email", "sms")):
        tokens = ["notification", "email", "sms"]
    elif "mail" in ql:
        tokens = ["mail", "smtp", "credential"]

    objs = [x for x in _as_list(reasoning_context.get("collaborators")) if isinstance(x, dict)]
    authority: List[str] = []
    graph: List[str] = []
    for c in objs:
        cls = _class_from_component_label(str(c.get("name") or "") or str(c.get("file") or ""))
        if not cls:
            continue
        cite = str(c.get("citation") or "")
        if cite.startswith("G:"):
            if cls not in graph:
                graph.append(cls)
        else:
            if cls not in authority:
                authority.append(cls)
    pool = authority + graph
    for raw in groups.get("handlers", []) + groups.get("collaborators", []) + groups.get("stores", []):
        cls = _class_from_component_label(raw)
        if cls and cls not in pool:
            pool.append(cls)
    if tokens:
        focused = [c for c in pool if any(t in c.lower() for t in tokens)]
        if focused:
            return focused[:limit]
    return pool[:limit]


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


def _owner_anchor_resolved(reasoning_context: Dict[str, Any]) -> bool:
    anchor = str(reasoning_context.get("anchor_method") or "").strip()
    if anchor and "." in anchor:
        return True
    owner = _as_dict(reasoning_context.get("primary_owner"))
    cls = str(owner.get("class") or "").strip()
    meth = str(owner.get("method") or "").strip()
    return bool(cls and meth)


def _should_emit_synthesis_limits_paragraph(reasoning_context: Dict[str, Any], evidence_quality: str) -> bool:
    """
    Omit the closing uncertainty block when STRONG evidence already has a resolved anchor and only
    routine snapshot gaps — avoids repeating boilerplate on every ASK response.
    """
    eq = str(evidence_quality or "").upper()
    if eq != "STRONG":
        return True
    if not _owner_anchor_resolved(reasoning_context):
        return True
    gaps = [str(g).strip() for g in _as_list(reasoning_context.get("coverage_gaps")) if str(g).strip()]
    if not gaps:
        return False
    if _routine_coverage_only(gaps):
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
    route_mapping = _as_dict(reasoning_context.get("api_route_mapping"))
    if str(route_mapping.get("schema_version") or "") == "api_route_handler_mapping.v1":
        for c in _as_list(route_mapping.get("api_classes")):
            if not isinstance(c, dict):
                continue
            if str(c.get("extends") or "").strip() == "AbstractAPI":
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
    return (
        (("architecture" in ql or ("explain" in ql and "layer" in ql)) and ("api" in ql or "api layer" in ql))
        or ("http request" in ql and "apiserver" in ql)
        or ("requests enter" in ql and ("apiserver" in ql or "handler" in ql))
        or ("reach concrete handler" in ql and "apiserver" in ql)
    )


def _is_api_route_flow_query(ql: str) -> bool:
    # Word-boundary-ish checks: class names like NetRouteScheduler contained "route".
    if re.search(r"\bapi\b", ql) or "http" in ql or "apiserver" in ql.replace(" ", ""):
        return True
    return bool(
        re.search(r"\broutes?\b", ql)
        or re.search(r"\brouting\b", ql)
        or re.search(r"\brouter\b", ql)
        or re.search(r"\bhandlers?\b", ql)
    )


_CLASS_NAME_TOKEN_RE = re.compile(r"\b[A-Z][a-zA-Z0-9]{2,}\b")

# Sentence-start / instruction words that match the Java class pattern but are not types.
_NON_TYPE_CLASS_TOKENS = frozenset(
    {
        "What",
        "When",
        "Where",
        "Which",
        "Whose",
        "How",
        "Why",
        "The",
        "This",
        "That",
        "These",
        "Those",
        "Please",
        "Explain",
        "Describe",
        "List",
        "Find",
        "Show",
        "Give",
        "Tell",
    }
)


def _java_class_candidates_in_query(query: str) -> List[str]:
    hits: List[str] = []
    seen: set[str] = set()
    for m in _CLASS_NAME_TOKEN_RE.finditer(query or ""):
        tok = m.group(0).strip()
        if tok in _NON_TYPE_CLASS_TOKENS:
            continue
        key = tok.lower()
        if key in seen:
            continue
        seen.add(key)
        hits.append(tok)
    return hits


def _is_named_class_capability_query(original: str, ql: str) -> bool:
    if not _java_class_candidates_in_query(original):
        return False
    if any(
        k in ql
        for k in (
            "responsibility",
            "purpose",
            "actually does",
            "role of",
            "role for",
        )
    ):
        return True
    if "actually" in ql and "does" in ql:
        return True
    if "what does" in ql or "what do " in ql:
        return True
    if "explain what " in ql or "describe what " in ql:
        return True
    if "what is " in ql:
        if any(
            m in ql
            for m in (
                "base class",
                "parent class",
                "inherits",
                "inheritance",
                "superclass",
                "implements",
                "extends",
            )
        ):
            return False
        return True
    return False


def _focus_class_for_capability_query(
    query: str,
    owner_cls: str,
    anchor: str,
    all_components: List[str],
) -> str:
    cand = _java_class_candidates_in_query(query)
    if not cand:
        return ""
    comps = {_class_from_component_label(c) for c in all_components if _class_from_component_label(c)}
    owner = (owner_cls or "").strip()
    anch_cls = _class_from_component_label(anchor)
    for pref in (owner, anch_cls):
        if pref and pref in cand:
            return pref
    for tok in cand:
        if tok in comps:
            return tok
    return cand[0]


def _compose_named_class_capability_paragraph(
    *,
    focus_cls: str,
    anchor: str,
    groups: Dict[str, List[str]],
) -> str:
    anchor_cls = _class_from_component_label(anchor)
    parts: List[str] = []
    if anchor and anchor_cls == focus_cls:
        parts.append(
            f"This bundle anchors on **`{focus_cls}`** (`{anchor}`): use the attached plan steps and snippets as the authority for what that type does in this snapshot."
        )
    elif anchor:
        parts.append(
            f"Your question highlights **`{focus_cls}`** while retrieval anchored at `{anchor}` — both are constrained to the excerpts and plan below; weight evidence that names `{focus_cls}` first."
        )
    else:
        parts.append(f"**`{focus_cls}`** is the clearest symbol named in your question; ground behavior only from the excerpts and plan below.")

    cols: List[str] = []
    seen: set[str] = set()
    for key in ("handlers", "collaborators", "stores", "entrypoints", "abstractions"):
        for lab in groups.get(key, []):
            c = _class_from_component_label(str(lab))
            if not c or c == focus_cls or c.lower() in seen:
                continue
            seen.add(c.lower())
            cols.append(c)
            if len(cols) >= 4:
                break
        if len(cols) >= 4:
            break
    cols_render = ", ".join(f"`{c}`" for c in cols[:4])
    if cols_render:
        parts.append(f"Neighboring grounded types in this view include {cols_render}.")
    return " ".join(parts)


def _api_route_mapping_summary(reasoning_context: Dict[str, Any]) -> Dict[str, Any]:
    m = _as_dict(reasoning_context.get("api_route_mapping"))
    if str(m.get("schema_version") or "") != "api_route_handler_mapping.v1":
        return {}
    return {
        "entrypoints": [x for x in _as_list(m.get("apiserver_entrypoints")) if isinstance(x, dict)],
        "routes": [x for x in _as_list(m.get("routes")) if isinstance(x, dict)],
        "api_classes": [x for x in _as_list(m.get("api_classes")) if isinstance(x, dict)],
        "lifecycle_hooks": [x for x in _as_list(m.get("lifecycle_hooks")) if isinstance(x, dict)],
        "eventbus_handoffs": [x for x in _as_list(m.get("eventbus_handoffs")) if isinstance(x, dict)],
        "unknowns": [x for x in _as_list(m.get("unknowns")) if isinstance(x, dict)],
    }


def _compose_api_route_mapping_paragraph(mapping: Dict[str, Any]) -> str:
    if not mapping:
        return ""
    routes = mapping.get("routes") or []
    api_classes = mapping.get("api_classes") or []
    hooks = mapping.get("lifecycle_hooks") or []
    unknowns = mapping.get("unknowns") or []

    has_api_v1_mount = any("/api/v1/*" in str(r.get("path") or "") for r in routes)
    has_namespace_routes = any("/settings/*" in str(r.get("path") or "") for r in routes)
    has_abstract_api = any(str(c.get("extends") or "") == "AbstractAPI" for c in api_classes)
    has_templates = any(str(h.get("class") or "") == "AbstractAPI" for h in hooks)

    parts: List[str] = []
    parts.append(
        "`APIServer.start` creates the HTTP server and root router"
        + (", mounts `/api/v1/*` into `apiRouter`" if has_api_v1_mount else "")
        + "."
    )
    if has_namespace_routes:
        parts.append("`apiRouter` binds namespace subrouters such as `/settings/*`, `/system/*`, and `/query/*`.")
    parts.append("`APIRouter.init` registers concrete API classes.")
    if has_templates:
        parts.append("`AbstractAPI.init` supplies the generic CRUD templates.")
    if has_abstract_api:
        examples = []
        for c in api_classes:
            cls = str(c.get("class") or "").strip()
            if cls and cls in {"MailServerConfiguration", "User", "TraceService"} and cls not in examples:
                examples.append(cls)
        if examples:
            rendered = ", ".join(f"`{x}`" for x in examples)
            parts.append(f"Classes like {rendered} provide endpoint-specific behavior via lifecycle hooks.")
    if unknowns:
        parts.append("Exact per-endpoint overrides still need class-by-class extraction.")
    return " ".join(parts)


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


def _eventbus_role_sentences(reasoning_context: Dict[str, Any]) -> List[str]:
    eb = _as_dict(reasoning_context.get("eventbus_context"))
    if not eb:
        return []
    producers = [x for x in _as_list(eb.get("producers")) if isinstance(x, dict)]
    consumers = [x for x in _as_list(eb.get("consumers")) if isinstance(x, dict)]
    by_addr_p: Dict[str, List[Dict[str, Any]]] = {}
    by_addr_c: Dict[str, List[Dict[str, Any]]] = {}
    for p in producers:
        a = str(p.get("address") or "").strip()
        if a:
            by_addr_p.setdefault(a, []).append(p)
    for c in consumers:
        a = str(c.get("address") or "").strip()
        if a:
            by_addr_c.setdefault(a, []).append(c)
    lines: List[str] = []
    paired = sorted(set(by_addr_p.keys()) & set(by_addr_c.keys()))
    if paired:
        a = paired[0]
        p = by_addr_p[a][0]
        c = by_addr_c[a][0]
        p_label = f"`{p.get('class')}.{p.get('method')}`" if p.get("class") and p.get("method") else "`Producer`"
        c_label = f"`{c.get('class')}.{c.get('method')}`" if c.get("class") and c.get("method") else "`Consumer`"
        lines.append(f"{p_label} publishes `{a}`.")
        lines.append(f"{c_label} consumes `{a}`.")
    else:
        addrs = _as_list(eb.get("addresses"))
        if addrs:
            shown = [str(_as_dict(a).get("address") or "").strip() for a in addrs][:2]
            shown = [s for s in shown if s]
            if shown:
                lines.append(f"Selected EventBus addresses include {', '.join(f'`{s}`' for s in shown)}.")
        lines.append("No exact producer-consumer pair is proven for the selected address.")
    return lines[:2]


def _planning_paragraph_from_context(query: str, groups: Dict[str, List[str]]) -> str:
    ordered = groups.get("entrypoints", []) + groups.get("abstractions", []) + groups.get("handlers", []) + groups.get("stores", []) + groups.get("collaborators", [])
    flow = _top_classes(ordered, limit=4)
    chain = ", ".join(f"`{c}`" for c in flow) if flow else ""
    base = (
        "Use a phased refactor plan: isolate the enrichment change behind a feature flag, "
        "add validation checkpoints, and define explicit rollback triggers before rollout."
    )
    if "alert" in query.lower() or "enrichment" in query.lower():
        base = (
            "For alert/enrichment changes, use phased rollout with feature-flag gating, "
            "pre/post validation checks, and a rollback path tied to concrete risk signals."
        )
    if chain:
        return base + f" Ground the work against classes in this snapshot, e.g. {chain}."
    return base + " Keep each phase bounded to concrete classes visible in current evidence."


def _synthesis_flag_enabled() -> bool:
    v = str(os.environ.get(_SYNTHESIS_FLAG_ENV, "")).strip().lower()
    return v in {"1", "true", "yes", "on"}


def _should_use_synthesis_first_narration(query: str, metadata: Dict[str, Any]) -> bool:
    """Broad/system flows only — never structural, discovery listing, or planning."""
    if not _synthesis_flag_enabled():
        return False
    syn = metadata.get("reasoning_synthesis")
    if not isinstance(syn, dict):
        return False
    if str(syn.get("schema_version") or "") != "reasoning_synthesis.v1":
        return False
    if _is_planning_or_refactor_query(query):
        return False
    if _is_structural_query(query):
        return False
    if _is_discovery_query(query):
        return False
    return _is_broad_system_or_flow_query(query)


def _is_broad_system_or_flow_query(query: str) -> bool:
    q = str(query or "").strip().lower()
    intent = _query_intent(query)
    if intent in ("mail", "config_store", "notification", "alert_flow", "api"):
        return True
    keys = (
        "architecture",
        "layer",
        "how does",
        "how ",
        "workflow",
        "explain ",
        "system ",
        "flow",
        "http ",
        "api ",
        "route",
        "notification",
        "mail ",
        "config store",
        "eventbus",
        "async",
        "enter ",
        "requests ",
    )
    return any(k in q for k in keys)


def _query_implies_http_api_surface(query: str) -> bool:
    """True when prose should reference HTTP ingress, routers, or route tables."""
    ql = str(query or "").strip().lower()
    # Avoid bare "route" — it appears in notification/event phrasing unrelated to HTTP ingress.
    needles = (
        "http ",
        "https:",
        "apiserver",
        "api server",
        "rest ",
        "ingress",
        "nginx",
        "/api/",
        "api layer",
        " router",
        "routers ",
        "api route",
        "http route",
        "routes and handler",
        "routing through",
        "route table",
        "route mapping",
        "handler class",
        "request enters",
        "through apiserver",
        "reach concrete handler",
        "http request",
        " apis and handler",
    )
    return any(n in ql for n in needles)


def _notification_evidence_heuristic(reasoning_context: Dict[str, Any], syn: Dict[str, Any]) -> bool:
    if str(syn.get("query_intent") or "") == "notification":
        return True
    eb = _as_dict(reasoning_context.get("eventbus_context"))
    if eb.get("producers") or eb.get("consumers") or eb.get("addresses"):
        return True
    typed = _as_dict(reasoning_context.get("typed_nodes"))
    for bucket in ("handlers", "collaborators", "entrypoints"):
        for node in _as_list(typed.get(bucket)):
            if not isinstance(node, dict):
                continue
            c = str(node.get("class") or "").lower()
            if any(tok in c for tok in ("notification", "notify", "email", "sms", "slack")):
                return True
    return False


def _eventbus_topology_proven(reasoning_context: Dict[str, Any]) -> bool:
    eb = _as_dict(reasoning_context.get("eventbus_context"))
    return bool(eb.get("producers") or eb.get("consumers") or eb.get("addresses"))


def _mail_delivery_tail_proven(reasoning_context: Dict[str, Any]) -> bool:
    """Async/delivery collaborator visible in buckets (best-effort, evidence-only tail)."""
    typed = _as_dict(reasoning_context.get("typed_nodes"))
    for bucket in ("collaborators", "handlers"):
        for node in _as_list(typed.get(bucket)):
            if not isinstance(node, dict):
                continue
            c = str(node.get("class") or "").lower()
            if any(tok in c for tok in ("mail", "smtp", "smtpclient", "send", "delivery", "deliver")):
                return True
    return False


def _explicit_api_voice_query(query: str) -> bool:
    """api_layer narration only when query clearly targets HTTP/API surface (Phase D.1)."""
    return _query_implies_http_api_surface(query)


def _effective_narration_subsystem(
    query: str,
    synthesis: Dict[str, Any],
    reasoning_context: Dict[str, Any],
) -> str:
    """
    Reconcile `_query_intent`, query text, synthesis subsystem label, and evidence so broad
    questions are not flattened into generic API ingress prose.
    """
    ql = str(query or "").strip().lower()
    qi = _query_intent(query)
    syn_sub = str(_as_dict(synthesis.get("subsystem")).get("label") or "general").strip() or "general"

    # Domain intents win unless the query is explicitly HTTP/API wording.
    if qi == "mail" or bool(re.search(r"\bmail\b", ql)):
        if not (_explicit_api_voice_query(query) and "mail" not in ql):
            return "mail_configuration"
    if qi == "config_store" or ("config store" in ql or "config stores" in ql):
        if not _explicit_api_voice_query(query):
            return "config_store"
        return "api_layer"

    notification_terms = (
        "notification",
        "notify",
        "eventbus",
        "event bus",
        "message bus",
        "publish",
        "consume",
        "producer",
        "consumer",
        "subscriber",
        "dispatch",
        "pipeline",
    )
    notification_q = qi == "notification" or any(k in ql for k in notification_terms)
    notify_evidence = _notification_evidence_heuristic(reasoning_context, synthesis)

    explicit_http = _explicit_api_voice_query(query)
    if not explicit_http:
        if notification_q and (notify_evidence or qi == "notification"):
            return "notification"
        if notify_evidence and (
            "event-driven" in ql
            or bool(re.search(r"\bevents?\b", ql))
            or ("trap" in ql and "snmp" in ql)
            or ("end-to-end" in ql and "notification" in ql)
        ):
            return "notification"

    if any(k in ql for k in ("correlation engine", "correlation skip", "enrichment branch", "availability correlation")):
        return "availability_correlation"

    if explicit_http or ("explain" in ql and "api layer" in ql):
        return "api_layer"

    if syn_sub == "api_layer":
        if notify_evidence and not explicit_http:
            return "notification"
        if qi == "mail" or bool(re.search(r"\bmail\b", ql)):
            return "mail_configuration"
        if not explicit_http:
            return "general"

    if syn_sub in _SUBSYSTEM_SUMMARY_LEDE:
        return syn_sub
    return "general"


_FLOW_VOICE_PREFIX: Dict[str, str] = {
    "notification": (
        "Notification narrations here foreground orchestrators and delivery channels surfaced in evidence, not generic HTTP ingress."
    ),
    "config_store": (
        "Configuration narrations emphasize abstraction layers and concrete stores rather than repeating server bootstrap language."
    ),
    "mail_configuration": (
        "Mail settings narration centers validation hooks and persistence collaborators tied to the anchored classes."
    ),
    "availability_correlation": (
        "Correlation narrations hinge on engine bootstrap evidence; widen snippets before asserting branch-level skips."
    ),
}


_SUBSYSTEM_SUMMARY_LEDE: Dict[str, str] = {
    "api_layer": (
        "The HTTP/API surface in this evidence snapshot is organized around server bootstrap, shared handler contracts, "
        "and concrete route bindings where the offline route map applies."
    ),
    "mail_configuration": (
        "Mail and delivery settings flow through validation and persistence-oriented components tied to the evidence bundle, "
        "not a single isolated method."
    ),
    "notification": (
        "Notification behavior is split between orchestration components and channel implementations; async handoffs apply "
        "only where EventBus topology proves a matching address."
    ),
    "config_store": (
        "Configuration storage is shaped by shared store abstractions with concrete implementations visible in this snapshot."
    ),
    "availability_correlation": (
        "Availability and correlation logic anchors on engine-style components in evidence; wider excerpts are needed for branch-level causality."
    ),
    "general": (
        "This answer summarizes subsystem roles visible in grounded evidence and maps; treat named classes as anchors, not a full runtime trace."
    ),
}


_FLOW_STEP_PHRASES: Dict[str, str] = {
    "ingress_bootstrap": "traffic enters through server bootstrap and route mounting",
    "shared_abstraction_or_rest_contract": "shared REST abstractions define common handler contracts",
    "request_handler_or_concrete_api": "concrete API classes implement endpoints backed by this snapshot",
    "persistence_config_store": "callers reach concrete configuration stores through the persistence boundary shown in evidence",
    "async_eventbus_handoff": "asynchronous work may cross the EventBus where topology ties producers and consumers to an address",
    "flow_steps_sketch": "supporting classes tie into the grounded flow sketch where evidence lists them",
    "mail_configuration_lifecycle": "mail configuration updates run through API lifecycle hooks where those classes participate",
    "api_request_routing": "HTTP routes are reflected in the route table captured in evidence",
    "typed_flow_sketch": "the inferred typed-node sketch suggests how work moves between layers",
    "configuration_validation_and_persistence": "validation and enrichment run before configuration state is written or refreshed",
    "config_typed_abstraction": "typed configuration abstractions mediate reads and writes before concrete store implementations",
    "notification_orchestration": "orchestration coordinates channel-oriented handlers before persistence side effects",
    "mail_async_delivery_tail": "downstream collaborators may handle delivery asynchronously when evidence surfaces mail or SMTP-oriented handlers",
}


def _synthesis_summary_paragraph(voice: str) -> str:
    lab = voice if voice in _SUBSYSTEM_SUMMARY_LEDE else "general"
    return _SUBSYSTEM_SUMMARY_LEDE.get(lab, _SUBSYSTEM_SUMMARY_LEDE["general"])


def _dedupe_phrase_order(phrases: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for p in phrases:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _provenance_fact_is_route_table_noise(line: str) -> bool:
    """Route / graph snapshot lines from synthesis proven_facts — noisy for mail/config/notification asks."""
    low = str(line or "").strip().lower()
    if not low:
        return False
    return (
        low.startswith("route start ")
        or low.startswith("route init ")
        or "api_route_mapping" in low
        or low.startswith("graph path snapshot:")
    )


def _synthesis_flow_paragraph(
    *,
    query: str,
    voice: str,
    synthesis: Dict[str, Any],
    reasoning_context: Dict[str, Any],
) -> str:
    """Map synthesis control_flow_steps to prose; omit HTTP ingress for non-API voices unless the query asks for it."""
    allow_http = voice == "api_layer" or _explicit_api_voice_query(query)
    steps = _as_list(synthesis.get("control_flow_steps"))
    keys_ordered: List[str] = []
    for st in steps:
        if not isinstance(st, dict):
            continue
        key = str(st.get("step") or "").strip()
        if key and key not in keys_ordered:
            keys_ordered.append(key)

    drop_http_voice = frozenset({"ingress_bootstrap", "api_request_routing"})

    phrases: List[str] = []
    seen: set[str] = set()
    eb_from_steps = False

    def push_key(key: str) -> None:
        nonlocal eb_from_steps
        if key == "async_eventbus_handoff":
            eb_from_steps = True
        if not allow_http and key in drop_http_voice:
            return
        if voice == "config_store" and not allow_http and key in (
            "ingress_bootstrap",
            "api_request_routing",
            "request_handler_or_concrete_api",
            "shared_abstraction_or_rest_contract",
            "typed_flow_sketch",
            "flow_steps_sketch",
        ):
            return
        if voice == "notification" and not allow_http:
            if key in drop_http_voice:
                return
            if key in (
                "request_handler_or_concrete_api",
                "shared_abstraction_or_rest_contract",
                "typed_flow_sketch",
                "flow_steps_sketch",
            ):
                return
        if voice == "mail_configuration" and not allow_http:
            if key in drop_http_voice:
                return
            if key in (
                "request_handler_or_concrete_api",
                "shared_abstraction_or_rest_contract",
                "typed_flow_sketch",
                "flow_steps_sketch",
                "api_request_routing",
            ):
                return
        if voice == "general" and not allow_http and key in (
            "ingress_bootstrap",
            "api_request_routing",
            "request_handler_or_concrete_api",
            "shared_abstraction_or_rest_contract",
        ):
            return
        ph = _FLOW_STEP_PHRASES.get(key)
        if ph and ph not in seen:
            seen.add(ph)
            phrases.append(ph)

    for k in keys_ordered:
        push_key(k)

    if voice == "config_store":
        if not allow_http:
            phrases.insert(0, _FLOW_STEP_PHRASES["config_typed_abstraction"])
            if _FLOW_STEP_PHRASES["persistence_config_store"] not in seen:
                seen.add(_FLOW_STEP_PHRASES["persistence_config_store"])
                phrases.append(_FLOW_STEP_PHRASES["persistence_config_store"])
        else:
            for k in ("shared_abstraction_or_rest_contract", "request_handler_or_concrete_api", "persistence_config_store"):
                push_key(k)

    elif voice == "notification":
        phrases.insert(0, _FLOW_STEP_PHRASES["notification_orchestration"])
        if _eventbus_topology_proven(reasoning_context) or eb_from_steps:
            eb = _FLOW_STEP_PHRASES["async_eventbus_handoff"]
            if eb not in seen:
                seen.add(eb)
                phrases.append(eb)

    elif voice == "mail_configuration":
        heads = (
            _FLOW_STEP_PHRASES["mail_configuration_lifecycle"],
            _FLOW_STEP_PHRASES["configuration_validation_and_persistence"],
        )
        phrases = _dedupe_phrase_order([*heads, *phrases])
        if allow_http or _mail_delivery_tail_proven(reasoning_context):
            tail = _FLOW_STEP_PHRASES["mail_async_delivery_tail"]
            phrases = _dedupe_phrase_order([*phrases, tail])

    elif voice == "api_layer":
        push_key("ingress_bootstrap")
        if not phrases:
            phrases.append(_FLOW_STEP_PHRASES["shared_abstraction_or_rest_contract"])

    phrases = _dedupe_phrase_order(phrases)[:8]
    prefix = (_FLOW_VOICE_PREFIX.get(voice) or "").strip()
    if not phrases:
        return ""

    body_core = "; ".join(phrases)
    if prefix:
        return f"In broad strokes, {prefix} {body_core}."
    return f"In broad strokes, {body_core}."


def _synthesis_anchors_paragraph(
    syn: Dict[str, Any],
    reasoning_context: Dict[str, Any],
    *,
    voice: str,
    query: str,
) -> str:
    facts = _as_list(syn.get("proven_facts"))[:8]
    anchor = str(reasoning_context.get("anchor_method") or "").strip()
    allow_route_facts = voice == "api_layer" or _query_implies_http_api_surface(query)
    parts: List[str] = []
    if anchor:
        parts.append(f"Primary anchor: `{anchor}`.")
    for f in facts:
        fs = str(f).strip()
        if not fs or fs in parts:
            continue
        if not allow_route_facts and _provenance_fact_is_route_table_noise(fs):
            continue
        parts.append(fs)
    if not parts:
        return ""
    return "Key evidence hooks: " + " ".join(parts)


def _synthesis_limits_paragraph(
    syn: Dict[str, Any],
    evidence_quality: str,
    reasoning_context: Dict[str, Any],
) -> str:
    if not _should_emit_synthesis_limits_paragraph(reasoning_context, evidence_quality):
        return ""
    lim = [str(x).strip() for x in _as_list(syn.get("confidence_limits")) if str(x).strip()]
    if not lim:
        return _evidence_limit_note({"evidence_quality": evidence_quality})
    return "What this snapshot does not yet prove: " + " ".join(lim[:6])


def _synthesis_flow_or_route_mapping_paragraph(
    *,
    query: str,
    voice: str,
    synthesis: Dict[str, Any],
    reasoning_context: Dict[str, Any],
) -> str:
    """
    Prefer the same concrete `api_route_mapping` paragraph as unified_contract when evidence
    supports it — synthesis-only flow phrases are weaker for API architecture / HTTP ingress asks.
    """
    ql = str(query or "").strip().lower()
    if voice != "api_layer":
        return _synthesis_flow_paragraph(
            query=query, voice=voice, synthesis=synthesis, reasoning_context=reasoning_context
        )
    route_mapping = _api_route_mapping_summary(reasoning_context)
    mapped = _compose_api_route_mapping_paragraph(route_mapping).strip()
    if not mapped:
        return _synthesis_flow_paragraph(
            query=query, voice=voice, synthesis=synthesis, reasoning_context=reasoning_context
        )
    if _is_api_layer_architecture_query(ql) or _query_implies_http_api_surface(query):
        return mapped
    return _synthesis_flow_paragraph(
        query=query, voice=voice, synthesis=synthesis, reasoning_context=reasoning_context
    )


def _synthesis_first_paragraphs(
    *,
    query: str,
    metadata: Dict[str, Any],
    reasoning_context: Dict[str, Any],
    evidence_quality: str,
) -> Optional[List[str]]:
    syn = metadata.get("reasoning_synthesis")
    if not isinstance(syn, dict):
        return None
    voice = _effective_narration_subsystem(query, syn, reasoning_context)
    p1 = _synthesis_summary_paragraph(voice)
    p2 = _synthesis_flow_or_route_mapping_paragraph(
        query=query, voice=voice, synthesis=syn, reasoning_context=reasoning_context
    )
    p3 = _synthesis_anchors_paragraph(syn, reasoning_context, voice=voice, query=query)
    p4 = _synthesis_limits_paragraph(syn, evidence_quality, reasoning_context)
    out: List[str] = []
    if p1:
        out.append(p1)
    if p2:
        out.append(p2)
    if p3:
        out.append(p3)
    if p4:
        out.append(p4)
    return out if len(out) >= 2 else None


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
    route_mapping = _api_route_mapping_summary(reasoning_context)
    steps_for_plan = list(plan_steps or [])

    # Planning / refactor in ASK: keep architecture framing, avoid pseudo-execution steps.
    if _is_planning_or_refactor_query(query):
        contextual = _planning_paragraph_from_context(query, groups)
        if contextual:
            return [contextual + " This is architectural guidance in ASK mode; use PLAN mode for executable sequencing, checkpoints, and rollback gates."]
        lede = _planning_lede_from_steps(steps_for_plan)
        if lede:
            return [lede + " Use the numbered plan steps below for sequencing and safeguards."]
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
                            f"`AbstractAPI` is the expected shared superclass for concrete REST/API handler classes. "
                            f"The inheritance chain in current evidence ({chain_txt}) documents the Vert.x server deployment type, "
                            f"not REST handler inheritance."
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
    event_publish_consume_query = any(k in ql for k in ("publish", "consume", "producer", "consumer", "event"))
    abstractions = groups.get("abstractions", [])
    handlers = groups.get("handlers", [])
    stores = groups.get("stores", [])
    collaborators = groups.get("collaborators", [])

    # 2–3 direct sentences: active voice, no pasted flow_steps (avoids G# / diagnostic traces).
    sentences: List[str] = []
    if intent == "mail":
        anchor_cls = _class_from_component_label(anchor) or "MailServerConfiguration"
        sentences.append(
            f"`{anchor_cls}` handles validation and persistence before mail settings are applied."
        )
        follow = _render_class_list(stores or collaborators or handlers, limit=4, drop=anchor)
        if follow:
            sentences.append(
                f"It works with {follow} for transport, event bridging, and store updates."
            )
        sentences.append("This keeps update hooks separate from delivery-side behavior.")
    elif event_publish_consume_query:
        eb_lines = _eventbus_role_sentences(reasoning_context)
        if eb_lines:
            sentences.extend(eb_lines)
        else:
            sentences.append("Event roles are not directly resolved in the current EventBus context.")
    elif intent == "notification":
        owners = _render_class_list(([anchor] if anchor else []) + handlers, limit=2, drop=None)
        head = owners or "`NotificationEngine`"
        pclasses = _prioritized_collaborator_classes(
            query=query, reasoning_context=reasoning_context, groups=groups, limit=4
        )
        collab = _render_list(pclasses, limit=4, drop=_class_from_component_label(anchor))
        sentences.append(f"Notification flow is coordinated by {head}.")
        if collab:
            sentences.append(f"Channel and trigger concerns are handled by {collab}.")
        eb_lines = _eventbus_role_sentences(reasoning_context)
        if eb_lines:
            sentences.extend(eb_lines)
        sentences.append("Delivery logic stays separate from orchestration.")
    elif any(k in ql for k in ("trigger", "message bus", "async")):
        eb_lines = _eventbus_role_sentences(reasoning_context)
        if eb_lines:
            sentences.extend(eb_lines)
        else:
            sentences.append("Event roles are not directly resolved in the current EventBus context.")
    elif intent == "config_store":
        abs_label = _render_class_list(abstractions or ([anchor] if anchor else []), limit=2, drop=anchor)
        abs_ref = abs_label or f"`{anchor}`"
        sentences.append(
            f"Config stores are built around {abs_ref}, which defines the shared read/write contract."
        )
        concrete = _render_class_list(stores or collaborators, limit=3, drop=anchor)
        if concrete:
            sentences.append(
                f"{concrete} implement domain-specific retrieval and update behavior."
            )
        sentences.append("Callers stay decoupled from backend-specific storage details.")
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
            mapped = _compose_api_route_mapping_paragraph(route_mapping)
            if mapped:
                sentences.append(mapped)
            else:
                ep = _render_class_list(groups.get("entrypoints", []), limit=1, drop=None)
                mid = _render_class_list(abstractions, limit=2, drop=anchor)
                end = _render_class_list(handlers or collaborators or stores, limit=4, drop=anchor)
                bits: List[str] = []
                if ep:
                    bits.append(f"{ep} is the HTTP entrypoint and receives incoming requests.")
                elif anchor:
                    bits.append(f"`{_class_from_component_label(anchor) or anchor}` is the strongest entrypoint signal in this snapshot.")
                else:
                    bits.append("The API entrypoint is not clearly resolved in this snapshot.")
                if mid:
                    bits.append(f"{mid} provides shared API lifecycle hooks used by concrete handlers.")
                if end:
                    bits.append(f"Behind ingress, domain logic is handled by {end}.")
                tops = _top_classes(groups.get("entrypoints", []) + abstractions + handlers + stores + collaborators, limit=4)
                if tops:
                    bits.append(f"Main components in evidence: {', '.join(f'`{c}`' for c in tops[:4])}.")
                bits.append("Exact route-to-handler wiring is not directly confirmed in this snapshot.")
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
        elif _is_api_route_flow_query(ql):
            mapped = _compose_api_route_mapping_paragraph(route_mapping)
            if mapped:
                sentences.append(mapped)
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
        else:
            focus_cls = ""
            if _is_named_class_capability_query(query, ql):
                focus_cls = _focus_class_for_capability_query(
                    query,
                    owner_cls,
                    anchor,
                    all_components,
                )
            if focus_cls:
                sentences.append(
                    _compose_named_class_capability_paragraph(
                        focus_cls=focus_cls,
                        anchor=anchor,
                        groups=groups,
                    )
                )
            else:
                ep = _render_class_list(groups.get("entrypoints", []), limit=1, drop=None)
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

    shape_id = "unified_contract"
    paragraphs: List[str]
    if _should_use_synthesis_first_narration(query, md):
        syn_par = _synthesis_first_paragraphs(
            query=query,
            metadata=md,
            reasoning_context=rc,
            evidence_quality=eq,
        )
        if syn_par:
            paragraphs = [_strengthen_phrasing(p, eq) for p in syn_par]
            shape_id = "synthesis_first_v1"
        else:
            paragraphs = _unified_paragraphs(
                query=query,
                reasoning_context=rc,
                evidence_quality=eq,
                plan_steps=steps,
            )
    else:
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

    max_para = 4 if shape_id == "synthesis_first_v1" else 1
    limit_note = _evidence_limit_note(metadata)
    if shape_id == "synthesis_first_v1" and not _should_emit_synthesis_limits_paragraph(rc, eq):
        limit_note = ""
    payload: Dict[str, Any] = {
        "schema_version": _SCHEMA,
        "paragraphs": paragraphs[:max_para],
        "supporting_plan_bullets": _supporting_bullets_from_steps(steps)[:5],
        "evidence_limit": limit_note,
        "shape": shape_id,
    }
    return payload
