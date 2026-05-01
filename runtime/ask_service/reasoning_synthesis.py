"""
Reasoning Synthesis Layer v1 — deterministic structural summary between
reasoning_context.d1 and narration consumers.

Phase A/B: produce validateable metadata only; articulated_answer does not consume
this payload yet (shadow / evaluation path).

Does not invent symbols: only classifies and merges evidence already present in
reasoning_context.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

SYNTHESIS_SCHEMA_VERSION = "reasoning_synthesis.v1"
MAX_SYSTEM_SUMMARY_LEN = 500
MAX_COMPONENT_ROWS = 8
MAX_FACTS = 10


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _short_anchor_class(anchor_method: str) -> str:
    s = str(anchor_method or "").strip()
    if not s:
        return ""
    if "." in s:
        return s.split(".", 1)[0].strip()
    return s


def classify_query_intent(query: str, task_type: str = "general") -> str:
    """
    Map free-form query + task_type to reasoning_synthesis.v1 query_intent bucket.
    Kept local to avoid import cycles with articulated_answer.
    """
    tt = str(task_type or "").strip().upper()
    if tt == "EXPLAIN_DEBUG":
        return "debug"
    q = str(query or "").strip().lower()
    if q.startswith("plan ") or " plan " in q or any(
        k in q for k in ("refactor", "rollback", "feature flag", "phased rollout", "migration")
    ):
        return "plan"
    if any(k in q for k in ("find all", "list ", "classes that", "which classes")):
        return "list"
    if (
        any(k in q for k in ("notification", "email", "sms"))
        and any(k in q for k in ("find", "list", "class", "classes", "handle", "involved"))
    ):
        return "notification"
    if re.search(r"\bmail\b", q):
        return "mail"
    if "config store" in q or "config stores" in q:
        return "config_store"
    if any(k in q for k in ("availability", "correlation", "enrichment")) and any(
        k in q for k in ("debug", "why", "skip", "failure", "drop")
    ):
        return "correlation"
    if any(k in q for k in ("how ", "how does", "workflow", "flow", "change settings", "users change")):
        return "how"
    if any(
        k in q
        for k in (
            "architecture",
            "layer",
            "http requests",
            "apiserver",
            "abstractapi",
            "base class",
            "extends",
            "broad stroke",
            "end-to-end",
            "nginx",
            "ingress",
        )
    ):
        return "architecture"
    if any(k in q for k in ("caching", "cache", "session", "redis")):
        return "architecture"
    if any(k in q for k in ("trace", "pipeline")) and any(
        k in q for k in ("notification", "event", "async")
    ):
        return "notification"
    return "unknown"


def _distinct_grounded_classes(reasoning_context: Dict[str, Any]) -> Tuple[List[str], int]:
    """Ordered unique class names from typed_nodes + anchor class."""
    seen: set[str] = set()
    order: List[str] = []
    anchor = str(reasoning_context.get("anchor_method") or "").strip()
    ac = _short_anchor_class(anchor)
    if ac:
        seen.add(ac.lower())
        order.append(ac)
    typed = _as_dict(reasoning_context.get("typed_nodes"))
    for bucket in ("entrypoints", "abstractions", "handlers", "stores", "collaborators"):
        for node in _as_list(typed.get(bucket)):
            if not isinstance(node, dict):
                continue
            c = str(node.get("class") or "").strip()
            if c and c.lower() not in seen:
                seen.add(c.lower())
                order.append(c)
    return order, len(order)


def _expand_grounded_classes(reasoning_context: Dict[str, Any]) -> Tuple[List[str], int]:
    """
    Extend distinct classes with symbols proven in maps, authority collaborators,
    inheritance, and EventBus — same evidence bundle, deeper role graph for metrics.
    """
    base, _ = _distinct_grounded_classes(reasoning_context)
    seen = {x.lower() for x in base}
    order = list(base)

    def add(raw: str) -> None:
        s = str(raw or "").strip()
        if not s:
            return
        short = s.split(".")[-1] if "." in s else s
        if not short or short.lower() in seen:
            return
        seen.add(short.lower())
        order.append(short)

    for c in _as_list(reasoning_context.get("collaborators")):
        if isinstance(c, dict):
            add(str(c.get("name") or ""))

    arm = _as_dict(reasoning_context.get("api_route_mapping"))
    if str(arm.get("schema_version") or "") == "api_route_handler_mapping.v1":
        for ep in _as_list(arm.get("apiserver_entrypoints")):
            if isinstance(ep, dict):
                add(str(ep.get("class") or ""))
        for r in _as_list(arm.get("routes")):
            if isinstance(r, dict):
                add(str(r.get("class") or ""))
        for c in _as_list(arm.get("api_classes")):
            if isinstance(c, dict):
                add(str(c.get("class") or ""))

    inh = _as_dict(reasoning_context.get("inheritance"))
    for x in _as_list(inh.get("chain")):
        add(str(x).strip())

    eb = _as_dict(reasoning_context.get("eventbus_context"))
    for key in ("producers", "consumers"):
        for item in _as_list(eb.get(key)):
            if isinstance(item, dict):
                add(str(item.get("class") or ""))

    return order, len(order)


def _multi_hop_eligible(reasoning_context: Dict[str, Any], distinct_count: int) -> bool:
    if distinct_count >= 2:
        return True
    if _as_list(reasoning_context.get("top_graph_paths")):
        return True
    arm = _as_dict(reasoning_context.get("api_route_mapping"))
    if _as_list(arm.get("routes")):
        return True
    eb = _as_dict(reasoning_context.get("eventbus_context"))
    if _as_list(eb.get("producers")) and _as_list(eb.get("consumers")):
        return True
    return False


def _subsystem_block(intent: str, anchor_cls: str, reasoning_context: Dict[str, Any]) -> Dict[str, Any]:
    typed = _as_dict(reasoning_context.get("typed_nodes"))
    signals: List[str] = []
    label = "general"
    al = str(anchor_cls or "").lower()

    if intent == "mail" or "mail" in al:
        label = "mail_configuration"
        signals.append("query_intent")
    elif intent == "notification":
        label = "notification"
        signals.append("query_intent")
    elif intent == "config_store":
        label = "config_store"
        signals.append("query_intent")
    elif intent == "correlation":
        label = "availability_correlation"
        signals.append("query_intent")
    elif intent in ("architecture", "how", "list") or any(
        k in al for k in ("api", "server", "router", "verticle")
    ):
        label = "api_layer"
        signals.append("anchor_or_typed")

    if _as_list(typed.get("handlers")):
        signals.append("typed_nodes.handlers")
    if _as_list(typed.get("stores")):
        signals.append("typed_nodes.stores")
    eb = _as_dict(reasoning_context.get("eventbus_context"))
    if eb.get("addresses") or eb.get("producers"):
        signals.append("eventbus_context")

    arm = _as_dict(reasoning_context.get("api_route_mapping"))
    if str(arm.get("schema_version") or "") == "api_route_handler_mapping.v1":
        signals.append("api_route_mapping.v1")
        if _as_list(arm.get("routes")):
            signals.append("api_route_mapping.routes")
        if _as_list(arm.get("api_classes")):
            signals.append("api_route_mapping.api_classes")

    # Align api_layer label when maps strongly indicate HTTP surface but intent was unknown.
    if label == "general" and (
        "api_route_mapping.routes" in signals and ("typed_nodes.handlers" in signals or eb.get("producers"))
    ):
        label = "api_layer"
        signals.append("inferred_api_surface")

    route_boost = "api_route_mapping.routes" in signals
    typed_boost = bool(_as_list(typed.get("handlers")) or _as_list(typed.get("entrypoints")))
    eb_boost = bool(eb.get("addresses") or eb.get("producers"))
    strong_agreement = sum(1 for x in (route_boost, typed_boost, eb_boost) if x) >= 2

    conf = "high" if strong_agreement or len(signals) >= 3 else ("high" if len(signals) >= 2 else ("medium" if signals else "low"))
    return {"label": label, "confidence": conf, "signals": signals[:12]}


def _collect_role_rows(
    reasoning_context: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    typed = _as_dict(reasoning_context.get("typed_nodes"))
    entrypoints: List[Dict[str, Any]] = []
    abstractions: List[Dict[str, Any]] = []
    core: List[Dict[str, Any]] = []
    stores: List[Dict[str, Any]] = []
    collab: List[Dict[str, Any]] = []

    def row(bucket: str, node: Dict[str, Any], role: str) -> Dict[str, Any]:
        cls = str(node.get("class") or "").strip()
        meth = str(node.get("method") or "").strip()
        sym = f"{cls}.{meth}" if cls and meth else cls
        return {"symbol": sym, "role": role, "source": f"typed_nodes.{bucket}"}

    for node in _as_list(typed.get("entrypoints"))[:MAX_COMPONENT_ROWS]:
        if isinstance(node, dict):
            entrypoints.append(row("entrypoints", node, "ingress_bootstrap"))
    for node in _as_list(typed.get("abstractions"))[:MAX_COMPONENT_ROWS]:
        if isinstance(node, dict):
            abstractions.append(row("abstractions", node, "shared_abstraction"))
    for node in _as_list(typed.get("handlers"))[:MAX_COMPONENT_ROWS]:
        if isinstance(node, dict):
            core.append(row("handlers", node, "handler_or_engine"))
    for node in _as_list(typed.get("stores"))[:MAX_COMPONENT_ROWS]:
        if isinstance(node, dict):
            stores.append(row("stores", node, "persistence_or_config_store"))
    for node in _as_list(typed.get("collaborators"))[:MAX_COMPONENT_ROWS]:
        if isinstance(node, dict):
            collab.append(row("collaborators", node, "collaborator"))

    inh = _as_dict(reasoning_context.get("inheritance"))
    chain = [str(x).strip() for x in _as_list(inh.get("chain")) if str(x).strip()]
    for sym in chain[:4]:
        short = sym.split(".")[-1] if "." in sym else sym
        if short.lower().startswith("abstract"):
            abstractions.append(
                {"symbol": short, "role": "inheritance_abstraction", "source": "inheritance.chain"}
            )

    arm = _as_dict(reasoning_context.get("api_route_mapping"))
    if str(arm.get("schema_version") or "") == "api_route_handler_mapping.v1":
        for c in _as_list(arm.get("api_classes"))[:MAX_COMPONENT_ROWS]:
            if not isinstance(c, dict):
                continue
            nm = str(c.get("class") or "").strip()
            ext = str(c.get("extends") or "").strip()
            if ext == "AbstractAPI" and nm:
                abstractions.append(
                    {"symbol": nm, "role": "rest_handler_class", "source": "api_route_mapping.api_classes"}
                )

    return entrypoints, abstractions, core, stores, collab


def _async_eventbus_components(reasoning_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    eb = _as_dict(reasoning_context.get("eventbus_context"))
    out: List[Dict[str, Any]] = []
    by_addr: Dict[str, Dict[str, Any]] = {}
    for key, edge_list in (("producers", "producer"), ("consumers", "consumer")):
        for item in _as_list(eb.get(key)):
            if not isinstance(item, dict):
                continue
            addr = str(item.get("address") or "").strip()
            if not addr:
                continue
            slot = by_addr.setdefault(addr, {"address": addr, "producers": [], "consumers": []})
            cls = str(item.get("class") or "").strip()
            if cls:
                if edge_list == "producer":
                    slot["producers"].append(cls)
                else:
                    slot["consumers"].append(cls)
    for addr, slot in list(by_addr.items())[:MAX_COMPONENT_ROWS]:
        out.append(
            {
                "kind": "eventbus",
                "address": addr,
                "producers": sorted(set(slot.get("producers") or []))[:5],
                "consumers": sorted(set(slot.get("consumers") or []))[:5],
                "source": "eventbus_topology",
                "exact_match_only": True,
            }
        )
    return out


def _proven_facts(reasoning_context: Dict[str, Any]) -> List[str]:
    facts: List[str] = []
    arm = _as_dict(reasoning_context.get("api_route_mapping"))
    if str(arm.get("schema_version") or "") == "api_route_handler_mapping.v1":
        for r in _as_list(arm.get("routes"))[:6]:
            if not isinstance(r, dict):
                continue
            method = str(r.get("method") or "").strip()
            path = str(r.get("path") or "").strip()
            handler = str(
                r.get("handler_class") or r.get("handler") or r.get("handler_or_subrouter") or ""
            ).strip()
            if path:
                tail = handler if handler else "(handler unresolved in snapshot)"
                facts.append(f"Route {method or 'HTTP'} {path} maps to {tail} per api_route_mapping snapshot.")
    for gp in _as_list(reasoning_context.get("top_graph_paths"))[:3]:
        if isinstance(gp, dict):
            raw = str(gp.get("path") or "").strip()
            if raw:
                facts.append(f"Graph path snapshot: {raw[:240]}.")
    eb = _as_dict(reasoning_context.get("eventbus_context"))
    for addr_entry in _as_list(eb.get("addresses"))[:3]:
        if isinstance(addr_entry, dict):
            a = str(addr_entry.get("address") or "").strip()
            if a:
                facts.append(f"EventBus topology highlights address {a}.")
    for item in _async_eventbus_components(reasoning_context):
        addr = item.get("address")
        ps = item.get("producers") or []
        cs = item.get("consumers") or []
        if addr and (ps or cs):
            facts.append(
                f"EventBus address {addr}: producers {ps or '[]'}; consumers {cs or '[]'} (topology snapshot)."
            )
    return facts[:MAX_FACTS]


def _bounded_inferences(reasoning_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    anchor = str(reasoning_context.get("anchor_method") or "").strip()
    method = ""
    cls = ""
    if "." in anchor:
        cls, method = anchor.split(".", 1)
    meth_l = method.lower()
    if "beforeupdate" in meth_l or method == "beforeUpdate":
        out.append(
            {
                "statement": f"`{method}` behaves as a lifecycle hook on configuration updates (name pattern only).",
                "rule_id": "pattern.beforeUpdate",
                "confidence": "medium",
            }
        )
    if cls.lower().startswith("abstract"):
        out.append(
            {
                "statement": f"`{cls}` reads as a shared abstraction / contract boundary.",
                "rule_id": "pattern.abstractPrefix",
                "confidence": "medium",
            }
        )
    po = _as_dict(reasoning_context.get("primary_owner"))
    po_cls = str(po.get("class") or "").strip()
    if po_cls.lower() == "apiserver":
        out.append(
            {
                "statement": "APIServer maps to ingress/bootstrap for the HTTP/API surface when present as an entrypoint.",
                "rule_id": "pattern.apiIngress",
                "confidence": "medium",
            }
        )
    return out[:6]


def _build_system_summary(
    *,
    subsystem: Dict[str, Any],
    intent: str,
    anchor_cls: str,
    distinct_count: int,
    multi_hop: bool,
) -> str:
    """Subsystem-first wording; avoid leading with anchor Class.method as subject."""
    lab = str(subsystem.get("label") or "general")
    templates = {
        "api_layer": (
            "HTTP/API behavior in this snapshot spans ingress/bootstrap surfaces, shared handler abstractions where visible, "
            "and concrete route bindings when the offline route-handler map is present."
        ),
        "mail_configuration": (
            "Mail and delivery configuration flows through validation and persistence-oriented components referenced in this evidence set, "
            "rather than a single method in isolation."
        ),
        "notification": (
            "Notification-oriented behavior is distributed across orchestration/engine classes and channel collaborators visible here, "
            "with async handoffs only where EventBus topology proves matching addresses."
        ),
        "config_store": (
            "Configuration storage behavior centers on shared store abstractions plus concrete persistence classes grounded in this snapshot."
        ),
        "availability_correlation": (
            "Availability and correlation concerns tie to engine/bootstrap-style components in evidence; cross-branch causality requires wider snippets."
        ),
        "general": (
            "Subsystem roles in this snapshot are inferred only from grounded classes and maps below; narrative should cite them as evidence, not as the whole story."
        ),
    }
    base = templates.get(lab, templates["general"])
    suffix_parts: List[str] = []
    if distinct_count >= 2:
        suffix_parts.append(f"{distinct_count} distinct grounded components participate.")
    else:
        suffix_parts.append("Only one grounded component class is strongly isolated in this snapshot.")
    if multi_hop:
        suffix_parts.append("Multi-hop elaboration is supported by edges or maps.")
    else:
        suffix_parts.append("Treat multi-hop stories cautiously until additional edges appear.")
    glue = " ".join(suffix_parts)
    text = f"{base} {glue}"
    if anchor_cls and anchor_cls not in text:
        text += f" Primary authority anchor class in evidence: {anchor_cls}."
    return text[:MAX_SYSTEM_SUMMARY_LEN]


def _method_collapse_reason(
    distinct_count: int,
    multi_hop: bool,
    reasoning_context: Dict[str, Any],
) -> Tuple[bool, str]:
    gaps = _as_list(reasoning_context.get("coverage_gaps"))
    if distinct_count < 2 and not multi_hop:
        return True, "Fewer than two distinct grounded components and no proven edge/map hop."
    if distinct_count < 2 and multi_hop:
        return False, "Single dominant class but maps/paths supply external hop evidence."
    return False, "≥2 distinct grounded components or proven hop via paths/maps/eventbus."


def _control_flow_steps(intent: str, reasoning_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Prefer ingress → abstraction → handler → store → async when evidence exists."""
    steps: List[Dict[str, Any]] = []
    typed = _as_dict(reasoning_context.get("typed_nodes"))
    arm = _as_dict(reasoning_context.get("api_route_mapping"))
    has_routes = bool(_as_list(arm.get("routes")))
    has_api_classes = bool(_as_list(arm.get("api_classes")))
    has_ep = bool(_as_list(arm.get("apiserver_entrypoints")))

    if has_ep or has_routes:
        steps.append({"step": "ingress_bootstrap", "support": "api_route_mapping.apiserver_entrypoints|routes"})
    if _as_list(typed.get("abstractions")) or has_api_classes:
        steps.append({"step": "shared_abstraction_or_rest_contract", "support": "typed_nodes|api_route_mapping.api_classes"})
    if _as_list(typed.get("handlers")) or has_api_classes:
        steps.append({"step": "request_handler_or_concrete_api", "support": "typed_nodes.handlers|api_classes"})
    if _as_list(typed.get("stores")):
        steps.append({"step": "persistence_config_store", "support": "typed_nodes.stores"})
    eb = _as_dict(reasoning_context.get("eventbus_context"))
    if eb.get("producers") or eb.get("consumers") or eb.get("addresses"):
        steps.append({"step": "async_eventbus_handoff", "support": "eventbus_topology"})
    if _as_list(reasoning_context.get("flow_steps")):
        steps.append({"step": "flow_steps_sketch", "support": "reasoning_context.flow_steps"})
    if intent == "mail":
        steps.append({"step": "mail_configuration_lifecycle", "support": "query_intent"})
    if not steps and has_routes:
        steps.append({"step": "api_request_routing", "support": "api_route_mapping"})
    return steps[:8]


def _next_inspection_targets(reasoning_context: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()

    def push(label: str, path: str) -> None:
        p = str(path or "").strip()
        if not p or p in seen:
            return
        seen.add(p)
        out.append(f"{label}: {p}")

    po = _as_dict(reasoning_context.get("primary_owner"))
    pf = str(po.get("file") or "").strip()
    if pf:
        push("Primary owner", pf)

    arm = _as_dict(reasoning_context.get("api_route_mapping"))
    if str(arm.get("schema_version") or "") == "api_route_handler_mapping.v1":
        for ep in _as_list(arm.get("apiserver_entrypoints"))[:1]:
            if isinstance(ep, dict) and ep.get("file"):
                push("APIServer / route bootstrap", str(ep.get("file")))
        for r in _as_list(arm.get("routes"))[:2]:
            if isinstance(r, dict) and r.get("file"):
                push("Route mapping evidence", str(r.get("file")))
        for c in _as_list(arm.get("api_classes"))[:1]:
            if isinstance(c, dict) and c.get("file"):
                push("Concrete API class", str(c.get("file")))

    eb = _as_dict(reasoning_context.get("eventbus_context"))
    for key in ("producers", "consumers"):
        for item in _as_list(eb.get(key))[:2]:
            if isinstance(item, dict) and item.get("file"):
                push(f"EventBus {key[:-1]}", str(item.get("file")))

    for ref in _as_list(reasoning_context.get("evidence_sources"))[:6]:
        if not isinstance(ref, dict):
            continue
        p = str(ref.get("path") or "").strip()
        if p:
            push("Evidence entry", p)

    return out[:8]


def build_reasoning_synthesis(
    *,
    query: str,
    reasoning_context: Dict[str, Any],
    task_type: str = "general",
) -> Dict[str, Any]:
    rc = _as_dict(reasoning_context)
    intent = classify_query_intent(query, task_type=task_type)
    anchor_cls = _short_anchor_class(str(rc.get("anchor_method") or ""))
    classes, distinct_count = _expand_grounded_classes(rc)
    multi_hop = _multi_hop_eligible(rc, distinct_count)
    subsystem = _subsystem_block(intent, anchor_cls, rc)

    entrypoints, abstractions, core, stores, collab = _collect_role_rows(rc)
    async_comp = _async_eventbus_components(rc)
    facts = _proven_facts(rc)
    inferences = _bounded_inferences(rc)
    collapse, collapse_reason = _method_collapse_reason(distinct_count, multi_hop, rc)

    summary = _build_system_summary(
        subsystem=subsystem,
        intent=intent,
        anchor_cls=anchor_cls,
        distinct_count=distinct_count,
        multi_hop=multi_hop,
    )

    limits = [str(g).strip() for g in _as_list(rc.get("coverage_gaps")) if str(g).strip()]
    eb = _as_dict(rc.get("eventbus_context"))
    if intent in ("notification", "architecture") and not eb.get("producers") and not eb.get("addresses"):
        limits.append("EventBus topology context empty or not selected for this query.")

    out: Dict[str, Any] = {
        "schema_version": SYNTHESIS_SCHEMA_VERSION,
        "query_intent": intent,
        "subsystem": subsystem,
        "system_summary": summary,
        "entrypoints": entrypoints[:MAX_COMPONENT_ROWS],
        "abstractions": abstractions[:MAX_COMPONENT_ROWS],
        "core_components": core[:MAX_COMPONENT_ROWS],
        "collaborators": collab[:MAX_COMPONENT_ROWS],
        "storage_components": stores[:MAX_COMPONENT_ROWS],
        "async_components": async_comp,
        "control_flow_steps": _control_flow_steps(intent, rc),
        "proven_facts": facts,
        "bounded_inferences": inferences,
        "confidence_limits": limits[:8],
        "next_inspection_targets": _next_inspection_targets(rc),
        "method_collapse_risk": {"detected": collapse, "reason": collapse_reason},
        "synthesis_metrics": {
            "distinct_grounded_components": distinct_count,
            "multi_hop_eligible": multi_hop,
            "ordered_grounded_classes": classes[:12],
        },
    }
    return out


def validate_reasoning_synthesis(payload: Any) -> List[str]:
    """Structural validation; returns human-readable issues (empty if OK)."""
    errs: List[str] = []
    if not isinstance(payload, dict):
        return ["payload must be an object"]
    if str(payload.get("schema_version") or "") != SYNTHESIS_SCHEMA_VERSION:
        errs.append("schema_version must be reasoning_synthesis.v1")
    for key in (
        "query_intent",
        "subsystem",
        "system_summary",
        "entrypoints",
        "abstractions",
        "core_components",
        "collaborators",
        "storage_components",
        "async_components",
        "control_flow_steps",
        "proven_facts",
        "bounded_inferences",
        "confidence_limits",
        "next_inspection_targets",
        "method_collapse_risk",
    ):
        if key not in payload:
            errs.append(f"missing key: {key}")
    mcr = payload.get("method_collapse_risk")
    if not isinstance(mcr, dict) or "detected" not in mcr:
        errs.append("method_collapse_risk.detected required")
    return errs


def legacy_answer_method_collapse_hint(text: str) -> bool:
    """Heuristic: legacy prose opens by emphasizing a single Class.method anchor."""
    t = str(text or "").strip()
    if not t:
        return False
    head = t.split("\n", 1)[0][:220]
    # Backtick-wrapped Class.method at start
    if re.match(r"^[`']?[A-Za-z][A-Za-z0-9_]*\.[a-z][A-Za-z0-9_]*[`']?\s", head):
        return True
    if re.search(
        r"(strongest grounded component is|The strongest grounded component is)\s*`[A-Za-z][A-Za-z0-9_]*\.[a-z]",
        head,
        re.I,
    ):
        return True
    return False


def compute_shadow_rubric(
    *,
    legacy_answer_text: str,
    synthesis: Dict[str, Any],
    evidence_quality: str,
) -> Dict[str, Any]:
    """
    Lightweight offline scores for shadow reports (not production quality gates).
    """
    syn = _as_dict(synthesis)
    metrics = _as_dict(syn.get("synthesis_metrics"))
    distinct = int(metrics.get("distinct_grounded_components") or 0)
    multi = bool(metrics.get("multi_hop_eligible"))
    mcr = _as_dict(syn.get("method_collapse_risk"))
    collapse_syn = bool(mcr.get("detected"))
    facts = _as_list(syn.get("proven_facts"))
    infer = _as_list(syn.get("bounded_inferences"))

    depth = 0
    if syn.get("subsystem") and _as_dict(syn.get("subsystem")).get("label"):
        depth = 1
    if distinct >= 2:
        depth = 2
    if distinct >= 3 and multi:
        depth = 3
    # Conservative depth lift: multiple distinct proven_facts without inventing components.
    if depth < 2 and len(facts) >= 2:
        depth = 2
    if depth < 3 and distinct >= 2 and multi and len(facts) >= 2:
        depth = 3

    fluency = 2 if len(str(legacy_answer_text or "").split()) >= 12 else 1
    if legacy_answer_method_collapse_hint(str(legacy_answer_text or "")):
        fluency = min(fluency, 1)

    grounding = 1
    if len(facts) >= 1:
        grounding = 2
    if len(facts) >= 2 and str(evidence_quality or "").upper() == "STRONG":
        grounding = 3

    overclaim = 1
    if not facts and infer:
        overclaim = 2
    if not facts and len(infer) >= 3:
        overclaim = 3
    if facts:
        overclaim = min(overclaim, 1)

    method_collapse = collapse_syn or legacy_answer_method_collapse_hint(str(legacy_answer_text or ""))

    return {
        "depth_score": depth,
        "fluency_score": fluency,
        "grounding_score": grounding,
        "overclaim_risk": overclaim,
        "method_collapse_detected": method_collapse,
        "notes": "Heuristic shadow rubric; not a production gate.",
    }


def attach_reasoning_synthesis_to_metadata(metadata: Dict[str, Any], *, query: str, task_type: str) -> None:
    """Populate metadata['reasoning_synthesis'] from metadata['reasoning_context']."""
    rc = metadata.get("reasoning_context")
    if not isinstance(rc, dict):
        return
    syn = build_reasoning_synthesis(query=query, reasoning_context=rc, task_type=str(task_type or "general"))
    metadata["reasoning_synthesis"] = syn
    warns = validate_reasoning_synthesis(syn)
    if warns:
        metadata["reasoning_synthesis_validation_warnings"] = warns
