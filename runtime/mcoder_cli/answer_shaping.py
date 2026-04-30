from __future__ import annotations

import re
from typing import Any


_OWNER_RE = re.compile(
    r"(?:Primary implementation owner|Execution owner anchor \(supporting context, not base-class answer\)):\s*`(?P<cls>[^`]+)`\s+in\s+`(?P<file>[^`]+)`(?:,\s*method\s*`(?P<method>[^`]+)`)?",
    re.IGNORECASE,
)


# User-facing default prose: no diagnostic graph/debug phrasing (see docs/guides/BACKLOG_NARRATION_CIG_HOSTING.md).
_HUMAN_CONFIDENCE_LINE = "This summary follows the code and structure shown for this request."


def _human_confidence_one_sentence(coverage_gaps: list[str] | None) -> str:
    """Single closing sentence (confidence or limitation)—max one such sentence in composed answers."""
    gaps = [str(g).strip().rstrip(".") for g in (coverage_gaps or []) if str(g).strip()]
    if not gaps:
        return _HUMAN_CONFIDENCE_LINE
    if len(gaps) == 1:
        return f"Note: {gaps[0]}."
    return f"Note: {gaps[0]}; other details may be only partly visible in this run."


def _norm_query(q: str) -> str:
    return (q or "").strip().lower()


def _is_structural_query(q: str) -> bool:
    ql = _norm_query(q)
    return any(x in ql for x in ("base class", "parent class", "extends", "implements", "what is"))


def _is_discovery_query(q: str) -> bool:
    ql = _norm_query(q)
    return ("find" in ql or "list" in ql or "all" in ql) and ("class" in ql or "classes" in ql or "handle" in ql)


def _is_explain_query(q: str) -> bool:
    ql = _norm_query(q)
    return any(x in ql for x in ("how", "explain", "architecture", "work"))


def _is_debug_why_query(q: str) -> bool:
    ql = _norm_query(q)
    return "why" in ql or "debug" in ql


def _extract_owner(steps: list[str]) -> dict[str, str]:
    for s in steps:
        m = _OWNER_RE.search(str(s))
        if m:
            return {
                "cls": str(m.group("cls") or "").strip(),
                "file": str(m.group("file") or "").strip(),
                "method": str(m.group("method") or "").strip(),
            }
    return {"cls": "", "file": "", "method": ""}


def _is_raw_snippet_step(step: str) -> bool:
    low = step.lower()
    return (
        low.startswith("visible method-window evidence:")
        or "method-window excerpt:" in low
        or "evidence excerpt:" in low
    )


def _sanitize_step(step: str, owner: dict[str, str]) -> str:
    if not _is_raw_snippet_step(step):
        return step.strip()
    cls = owner.get("cls") or "owner class"
    method = owner.get("method") or "target method"
    file = owner.get("file") or "selected file"
    return f"Inspect `{cls}.{method}` in `{file}` to validate control-flow and persistence behavior."


def _is_status_preamble(step: str) -> bool:
    return step.lower().startswith("authority status:")


def _is_owner_line(step: str) -> bool:
    s = step.lower()
    return s.startswith("primary implementation owner:") or s.startswith(
        "execution owner anchor (supporting context, not base-class answer):"
    )


def _first_meaningful_step(steps: list[str]) -> str:
    for s in steps:
        if _is_status_preamble(s):
            continue
        return s
    return steps[0] if steps else ""


def _extract_grounded_explain_step(steps: list[str], owner: dict[str, str]) -> str:
    for s in steps:
        sl = s.lower()
        if sl.startswith("how it works (grounded):") or sl.startswith("architecture (grounded):"):
            _, _, tail = s.partition(":")
            text = tail.strip()
            for marker in ("Method-window excerpt:", "Visible method-window evidence:", "Evidence excerpt:"):
                if marker in text:
                    text = text.split(marker, 1)[0].strip()
            return _sanitize_step(text, owner)
    return ""


def _extract_classes_from_context(resp: dict[str, Any], query: str) -> list[str]:
    files = ((resp.get("context_bundle") or {}).get("files") or []) if isinstance(resp.get("context_bundle"), dict) else []
    ql = _norm_query(query)
    classes: list[str] = []
    for f in files:
        if not isinstance(f, dict):
            continue
        p = str(f.get("path") or "")
        if not p:
            continue
        base = p.replace("\\", "/").split("/")[-1]
        if "." in base:
            base = base.rsplit(".", 1)[0]
        if not base:
            continue
        if "notification" in ql:
            if "notification" not in p.lower() and "notification" not in base.lower():
                continue
        if base not in classes:
            classes.append(base)
    return classes[:5]


def _graph_block(resp: dict[str, Any]) -> dict[str, Any]:
    raw = resp.get("graph_traversal")
    if isinstance(raw, dict):
        return raw
    return {}


def _reasoning_context_block(resp: dict[str, Any]) -> dict[str, Any]:
    md = resp.get("metadata") if isinstance(resp.get("metadata"), dict) else {}
    rc = md.get("reasoning_context") if isinstance(md.get("reasoning_context"), dict) else {}
    return rc


def _has_citation(text: str) -> bool:
    s = str(text or "")
    if re.search(r"\bE\d+\b", s):
        return True
    if re.search(r"\bG\d+\b", s):
        return True
    if re.search(r"[A-Za-z0-9_./\-]+\.(?:java|kt|py|yml|yaml|xml|json)", s):
        return True
    return False


def _uncertain_if_uncited(text: str, allow_grounded_anchor: bool = False) -> str:
    t = str(text or "").strip()
    if not t:
        return ""
    if _has_citation(t):
        return t
    if allow_grounded_anchor:
        return t
    return "Unknown based on provided evidence."


def _compose_with_reasoning_context(query: str, resp: dict[str, Any]) -> dict[str, str] | None:
    rc = _reasoning_context_block(resp)
    if not rc:
        return None

    po = rc.get("primary_owner") if isinstance(rc.get("primary_owner"), dict) else {}
    owner_cls = str(po.get("class") or "").strip()
    owner_method = str(po.get("method") or "").strip()
    owner_file = str(po.get("file") or "").strip()
    owner_cite = str(po.get("citation") or "").strip()
    owner_role = str(po.get("role_description") or "").strip()
    owner_is_grounded = bool(owner_cls) and bool(owner_file or owner_cite)

    anchor = str(rc.get("anchor_method") or "").strip()
    inh = rc.get("inheritance") if isinstance(rc.get("inheritance"), dict) else {}
    chain = [str(x).strip() for x in (inh.get("chain") or []) if str(x).strip()]
    chain_cite = str(inh.get("citation") or "").strip()

    # D.1 typed node buckets
    typed = rc.get("typed_nodes") if isinstance(rc.get("typed_nodes"), dict) else {}
    flow_steps = rc.get("flow_steps") if isinstance(rc.get("flow_steps"), list) else []
    coverage_gaps = rc.get("coverage_gaps") if isinstance(rc.get("coverage_gaps"), list) else []
    # backward-compat: flat collaborators list for discovery fallback
    collabs_flat = rc.get("collaborators") if isinstance(rc.get("collaborators"), list) else []

    if _is_explain_query(query):
        owner_label = anchor or (f"{owner_cls}.{owner_method}" if owner_cls and owner_method else owner_cls)
        owner_claim = f"The primary anchor is `{owner_label}`"
        if owner_role:
            owner_claim += f", which acts as the {owner_role}"
        if owner_cite:
            owner_claim += f" [{owner_cite}]"
        # NOTE: do not emit owner_file raw path — it may not be in evidence bundle

        # Typed node summary (skip duplicate of primary owner)
        node_parts: list[str] = []
        for bucket_key, section in [("abstractions", "abstraction"), ("handlers", "handler"), ("stores", "store")]:
            nodes = [n for n in (typed.get(bucket_key) or []) if isinstance(n, dict) and n.get("class") and str(n.get("class") or "").lower() != owner_cls.lower()]
            if nodes:
                names = ", ".join(f"`{str(n.get('class') or '')}`" for n in nodes[:2])
                node_parts.append(f"{names} ({section})")

        collab_nodes = [n for n in (typed.get("collaborators") or []) if isinstance(n, dict) and n.get("class") and str(n.get("class") or "").lower() != owner_cls.lower()]
        if collab_nodes:
            names = ", ".join(f"`{str(n.get('class') or '')}`" for n in collab_nodes[:3])
            node_parts.append(f"{names} (collaborator)")

        body = owner_claim
        if node_parts:
            body += ". System components include: " + ", ".join(node_parts)

        if flow_steps:
            body += ". Flow: " + " → ".join(str(s) for s in flow_steps[:3])

        chain_claim = ""
        if chain:
            chain_claim = "Inheritance: " + " → ".join(f"`{c}`" for c in chain)
            if chain_cite:
                chain_claim += f" [{chain_cite}]"
        if chain_claim:
            body += ". " + chain_claim

        body += ". " + _human_confidence_one_sentence([str(g) for g in coverage_gaps])

        body = _uncertain_if_uncited(body, allow_grounded_anchor=owner_is_grounded)
        return {"answer_1": body, "next_step": "", "answer_shape": "explain"}

    if _is_discovery_query(query):
        # Build from typed nodes first, fall back to flat collaborators
        all_names: list[str] = []
        for bucket_key in ("handlers", "stores", "abstractions", "collaborators"):
            for node in (typed.get(bucket_key) or []):
                if not isinstance(node, dict):
                    continue
                cls = str(node.get("class") or "").strip()
                if cls and cls.lower() != owner_cls.lower():
                    all_names.append(cls)
        if not all_names:
            for item in collabs_flat[:8]:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name") or "").strip()
                if name:
                    all_names.append(name)

        if owner_cls:
            owner_part = f"`{owner_cls}`"
            if owner_cite:
                owner_part += f" [{owner_cite}]"
            # NOTE: do not emit owner_file raw path — it may not be in evidence bundle
            answer = "Primary owner: " + owner_part
            if all_names:
                formatted = ", ".join(f"`{n}`" for n in all_names[:6])
                answer += "; related classes: " + formatted
            answer = _uncertain_if_uncited(answer, allow_grounded_anchor=owner_is_grounded)
            return {"answer_1": answer, "next_step": "", "answer_shape": "discovery"}

    return None


def _path_nodes(path: str) -> list[str]:
    return [p.strip() for p in str(path).split("->") if p.strip()]


def _chain_methods(path: str) -> list[str]:
    methods: list[str] = []
    for node in _path_nodes(path):
        if "." in node:
            methods.append(node.rsplit(".", 1)[-1])
    return methods


def _compress_path(path: str) -> str:
    nodes = _path_nodes(path)
    if len(nodes) <= 4:
        return " -> ".join(f"`{n}`" for n in nodes)
    methods = _chain_methods(path)
    if methods:
        uniq: list[str] = []
        for m in methods:
            if m not in uniq:
                uniq.append(m)
        shown = "/".join(uniq[:5])
        return f"`{nodes[0]}` exposes lookup/helpers such as `{shown}` (plus additional hops)."
    return f"`{nodes[0]}` -> ... -> `{nodes[-1]}` ({len(nodes)} hops)"


def _infer_anchor_role(anchor: str) -> str:
    low = anchor.lower()
    if "abstractapi" in low:
        return "base API abstraction"
    if "apiserver.start" in low:
        return "API entrypoint and route bootstrap"
    if ".beforeupdate" in low:
        return "update lifecycle hook"
    if "abstractconfigstore" in low:
        return "shared storage abstraction"
    if ".start" in low:
        return "service entrypoint"
    return "core implementation anchor"


def _explain_intent(query: str) -> str:
    ql = _norm_query(query)
    if "mail" in ql:
        return "mail"
    if "config store" in ql or "config stores" in ql:
        return "config_store"
    if "api" in ql or "architecture" in ql:
        return "api"
    return "general"


def _dedupe_keep_order(items: list[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        if item and item not in out:
            out.append(item)
    return out


def _remove_anchor_duplicates(anchor: str, items: list[str]) -> list[str]:
    anchor_cls = anchor.rsplit(".", 1)[0] if "." in anchor else anchor
    filtered: list[str] = []
    for item in items:
        if item == anchor or item == anchor_cls:
            continue
        filtered.append(item)
    return filtered


def _render_anchor_list(items: list[str], limit: int = 3) -> str:
    uniq = _dedupe_keep_order(items)[:limit]
    if not uniq:
        return ""
    wrapped = [f"`{x}`" for x in uniq]
    if len(wrapped) == 1:
        return wrapped[0]
    if len(wrapped) == 2:
        return f"{wrapped[0]} and {wrapped[1]}"
    return ", ".join(wrapped[:-1]) + f", and {wrapped[-1]}"


def _merge_expanded_collaborators(query: str, collaborators: list[str], expanded_nodes: list[str], limit: int = 5) -> list[str]:
    if not expanded_nodes:
        return _dedupe_keep_order(collaborators)[:limit]
    ql = _norm_query(query)
    preferred_tokens = ["api", "handler"] if "api" in ql else []
    if "mail" in ql:
        preferred_tokens = ["mail", "config", "store", "notification"]
    elif "config" in ql:
        preferred_tokens = ["config", "store", "manager"]
    elif "notification" in ql:
        preferred_tokens = ["notification", "engine", "handler"]

    merged = _dedupe_keep_order(collaborators)
    candidates = []
    for node in expanded_nodes:
        label = str(node).strip()
        if not label:
            continue
        base = label.split(".", 1)[0]
        low = base.lower()
        score = 0
        if any(tok in low for tok in preferred_tokens):
            score += 3
        if base.endswith(("API", "Handler", "Store", "Manager", "Engine")):
            score += 2
        if "." not in base:
            score += 1
        candidates.append((score, base))
    for _, item in sorted(candidates, key=lambda x: (-x[0], x[1])):
        if item not in merged:
            merged.append(item)
        if len(merged) >= limit:
            break
    return merged[:limit]


def _narrative_explain(
    query: str,
    entry_line: str,
    abstraction_line: str,
    collaborators: list[str],
    store_line: str,
    limit_line: str,
) -> str:
    intent = _explain_intent(query)
    collab_text = _render_anchor_list(collaborators, limit=3)

    if intent == "mail":
        first = (
            f"Mail server configuration appears to flow through an update lifecycle anchored by {entry_line}, "
            "where changes are validated and persisted before downstream delivery behavior is applied."
        )
        second = (
            f"This path connects lifecycle logic to abstraction {abstraction_line}"
            + (f" and collaborators such as {collab_text}" if collab_text else "")
            + (f", with store flow {store_line}." if store_line else ".")
        )
    elif intent == "config_store":
        first = (
            f"Config stores appear to be organized around shared abstraction {abstraction_line}, "
            "which centralizes common read/write lookup behavior."
        )
        second = (
            f"Flow anchored by {entry_line}"
            + (f" likely fans into concrete components such as {collab_text}" if collab_text else "")
            + (f", with read/write path {store_line}." if store_line else ".")
        )
    elif intent == "api":
        first = (
            f"The API layer appears to start from entrypoint flow {entry_line}, "
            f"then route through base abstraction {abstraction_line} before delegating to concrete handlers/extensions."
        )
        second = (
            ("Collaborators include " + collab_text) if collab_text else "Collaborator resolution is currently sparse"
        ) + (f", with persistence/event path {store_line}." if store_line else ".")
    else:
        first = (
            f"The system appears to follow entrypoint flow {entry_line}, "
            f"move through abstraction {abstraction_line}, and delegate to implementation collaborators."
        )
        second = (
            ("Collaborators include " + collab_text) if collab_text else "Collaborator resolution is currently sparse"
        ) + (f", with supporting path {store_line}." if store_line else ".")

    low_lim = (limit_line or "").lower()
    if "coherent" in low_lim and "incomplete" not in low_lim and "sparse" not in low_lim:
        closing = _HUMAN_CONFIDENCE_LINE
    elif (limit_line or "").strip():
        trimmed = (limit_line or "").strip()
        if len(trimmed) > 160:
            trimmed = trimmed[:157] + "..."
        closing = f"This summary follows the code shown; {trimmed}."
    else:
        closing = _HUMAN_CONFIDENCE_LINE
    return first + " " + second + " " + closing


def _select_anchor_for_explain(flow_paths: list[str], owner: dict[str, str], owners: list[str]) -> str:
    if flow_paths:
        first_nodes = _path_nodes(flow_paths[0])
        if first_nodes:
            return first_nodes[0]
    if owner.get("cls"):
        method_part = f".{owner['method']}" if owner.get("method") else ""
        return f"{owner['cls']}{method_part}"
    if owners:
        return owners[0]
    return ""


def _bounded_inference_explain(
    query: str,
    anchor: str,
    inheritance: list[str],
    collaborators: list[str],
    classes_from_context: list[str],
) -> str:
    role = _infer_anchor_role(anchor)
    ql = _norm_query(query)
    intent = _explain_intent(query)
    abstraction = inheritance[1] if len(inheritance) >= 2 else ("AbstractAPI" if "api" in ql else "")
    collab = collaborators[:3] if collaborators else classes_from_context[:3]
    collab = _remove_anchor_duplicates(anchor, _dedupe_keep_order(collab))
    collab_line = _render_anchor_list(collab, limit=3) or "related handlers/stores in nearby context"

    if intent == "mail" and "beforeupdate" in anchor.lower():
        body = (
            f"Mail server configuration appears to run through an update lifecycle where `{anchor}` acts as the control hook, "
            f"validates/persists configuration state, and coordinates collaborators such as {collab_line}."
        )
    elif intent == "config_store":
        body = (
            f"Config stores appear to center on a shared abstraction where `{anchor}` indicates {role}, "
            f"while collaborators such as {collab_line} layer domain-specific read/write behavior."
        )
    elif intent == "api":
        body = (
            f"The API architecture appears to bootstrap at `{anchor}` ({role}), "
            + (f"route through `{abstraction}`, " if abstraction else "")
            + f"and delegate behavior to collaborators such as {collab_line}."
        )
    else:
        body = (
            f"The system appears to route through anchor `{anchor}` ({role}) with collaborators such as {collab_line}."
        )
    return body + " " + _HUMAN_CONFIDENCE_LINE


def _select_paths(paths: list[str], owners: list[str], collaborators: list[str], limit: int = 3) -> list[str]:
    scored: list[tuple[int, int, str]] = []
    owner_set = {o.lower() for o in owners}
    collab_set = {c.lower() for c in collaborators}
    for path in paths:
        p = path.lower()
        score = 0
        if any(o.lower() in p for o in owner_set):
            score += 2
        if any(c.lower() in p for c in collab_set):
            score += 1
        # prefer richer paths
        score += min(3, len(_path_nodes(path)) - 1)
        scored.append((score, -len(path), path))
    scored.sort(reverse=True)
    out: list[str] = []
    for _, _, p in scored:
        if p not in out:
            out.append(p)
        if len(out) >= limit:
            break
    return out


def _explain_bundle_score(
    flow_paths: list[str],
    inheritance: list[str],
    owners: list[str],
    collaborators: list[str],
    call_paths: list[str],
) -> int:
    score = 0
    if any(len(_path_nodes(p)) >= 2 for p in flow_paths):
        score += 1
    if len(inheritance) >= 2:
        score += 1
    if owners and collaborators:
        score += 1
    if any(len(_path_nodes(p)) >= 2 for p in call_paths):
        score += 1
    return score


def _compose_with_graph(query: str, resp: dict[str, Any]) -> dict[str, str] | None:
    g = _graph_block(resp)
    if not g:
        return None

    inheritance = [str(x) for x in (g.get("inheritance_chain") or g.get("inheritance") or []) if str(x).strip()]
    flow = [str(x) for x in (g.get("entrypoint_flow") or g.get("flow_paths") or []) if str(x).strip()]
    call_chain = [str(x) for x in (g.get("call_chain") or g.get("call_paths") or []) if str(x).strip()]
    concepts = g.get("concepts") if isinstance(g.get("concepts"), dict) else {}
    owners = [str(x) for x in ((g.get("owners") or concepts.get("owners") or [])) if str(x).strip()]
    collaborators = [
        str(x) for x in ((g.get("collaborators") or concepts.get("collaborators") or [])) if str(x).strip()
    ]
    expanded_nodes = [str(x) for x in (g.get("expanded_nodes") or []) if str(x).strip()]
    collaborators = _merge_expanded_collaborators(query, collaborators, expanded_nodes, limit=5)

    # Anti-collapse rule: avoid single-anchor output when graph resolves multiple meaningful nodes.
    meaningful_nodes = len(set(inheritance + flow + owners + collaborators + call_chain))

    if _is_structural_query(query) and inheritance:
        answer = "Based on graph-backed evidence, inheritance chain: " + " -> ".join(f"`{c}`" for c in inheritance) + "."
        return {"answer_1": answer, "next_step": "", "answer_shape": "structural"}

    if _is_explain_query(query) and (flow or inheritance or owners or collaborators or call_chain):
        intent = _explain_intent(query)
        selected_flow = _select_paths(flow, owners, collaborators, limit=3)
        selected_calls = _select_paths(call_chain, owners, collaborators, limit=2)
        bundle_score = _explain_bundle_score(selected_flow, inheritance, owners, collaborators, selected_calls)
        shallow_flow = bool(selected_flow) and all(len(_path_nodes(p)) <= 1 for p in selected_flow)
        owner = _extract_owner(
            [str(s).strip() for s in (((resp.get("plan_summary") or {}).get("steps") or [])) if str(s).strip()]
        )
        classes_from_context = _extract_classes_from_context(resp, query)

        if bundle_score < 2 or shallow_flow:
            anchor = _select_anchor_for_explain(selected_flow, owner, owners)
            if not anchor and selected_calls:
                first = _path_nodes(selected_calls[0])
                anchor = first[0] if first else ""
            if not anchor:
                return None
            answer = _bounded_inference_explain(query, anchor, inheritance, collaborators, classes_from_context)
            return {"answer_1": answer, "next_step": "", "answer_shape": "explain"}

        entry_line = (
            "; ".join(_compress_path(p) for p in selected_flow)
            if selected_flow
            else "No strong entry flow resolved."
        )
        abstraction_line = (
            " -> ".join(f"`{x}`" for x in inheritance[:3]) if len(inheritance) >= 2 else "Not fully resolved."
        )
        collab_items = collaborators[:5]
        collab_items = _remove_anchor_duplicates(selected_flow[0].split("->")[0].strip() if selected_flow else "", collab_items)
        store_line = (
            "; ".join(_compress_path(p) for p in selected_calls)
            if selected_calls
            else ""
        )
        limits = []
        if len(inheritance) < 2:
            limits.append("abstraction chain incomplete")
        if not collaborators:
            limits.append("collaborator set sparse")
        if not selected_calls:
            limits.append("store/event path unresolved")
        limit_line = ", ".join(limits) if limits else "graph evidence is coherent for current query scope"
        answer = _narrative_explain(
            query=query,
            entry_line=entry_line,
            abstraction_line=abstraction_line,
            collaborators=collab_items,
            store_line=store_line,
            limit_line=limit_line,
        )
        return {"answer_1": answer, "next_step": "", "answer_shape": "explain"}

    if _is_debug_why_query(query) and (call_chain or flow):
        chain = call_chain if call_chain else flow
        answer = (
            "Hypothesis (graph-backed): behavior follows "
            + " -> ".join(f"`{n}`" for n in chain)
            + "."
        )
        next_step = "Check for missing edge/branch at the first unexpected hop in this chain."
        return {"answer_1": answer, "next_step": next_step, "answer_shape": "debug"}

    if _is_discovery_query(query) and (owners or collaborators):
        owner_text = ", ".join(f"`{o}`" for o in owners) if owners else "none resolved"
        collab_text = ", ".join(f"`{c}`" for c in collaborators[:6]) if collaborators else "none resolved"
        answer = (
            "Based on deterministic graph evidence, primary owners: "
            + owner_text
            + "; collaborators: "
            + collab_text
            + "."
        )
        return {"answer_1": answer, "next_step": "", "answer_shape": "discovery"}

    return None


def shape_prompt_summary(query: str, resp: dict[str, Any]) -> dict[str, str]:
    rc_shaped = _compose_with_reasoning_context(query, resp)
    if rc_shaped:
        return rc_shaped

    graph_shaped = _compose_with_graph(query, resp)
    if graph_shaped:
        return graph_shaped

    steps = ((resp.get("plan_summary") or {}).get("steps") or []) if isinstance(resp.get("plan_summary"), dict) else []
    steps = [str(s).strip() for s in steps if str(s).strip()]
    if not steps:
        return {"answer_1": "", "next_step": "", "answer_shape": "none"}

    owner = _extract_owner(steps)
    first = _sanitize_step(_first_meaningful_step(steps), owner)
    second = _sanitize_step(steps[1], owner) if len(steps) > 1 else ""

    # Structural: keep direct answer and suppress owner context.
    if _is_structural_query(query):
        direct = next((s for s in steps if s.lower().startswith("direct answer (grounded):")), "")
        if direct:
            return {"answer_1": _sanitize_step(direct, owner), "next_step": "", "answer_shape": "structural"}
        return {
            "answer_1": "Based on current evidence, a definitive structural base-class answer is not fully confirmed.",
            "next_step": "",
            "answer_shape": "structural",
        }

    # Discovery/list: list classes first, avoid single-owner collapse.
    if _is_discovery_query(query):
        classes = _extract_classes_from_context(resp, query)
        if classes:
            answer = "Based on current evidence, relevant classes include: " + ", ".join(f"`{c}`" for c in classes) + "."
            next_step = ""
            if classes:
                next_step = f"Inspect `{classes[0]}` and related handlers to confirm responsibilities and call flow."
            return {"answer_1": answer, "next_step": next_step, "answer_shape": "discovery"}
        fallback_answer = "Based on current evidence, a complete class list could not be confidently enumerated yet."
        fallback_next = "" if _is_owner_line(second) else second
        return {"answer_1": fallback_answer, "next_step": fallback_next, "answer_shape": "discovery"}

    # Explain/how/architecture: concise explanation + anchors.
    if _is_explain_query(query):
        grounded = _extract_grounded_explain_step(steps, owner)
        if grounded:
            next_step = ""
            if owner.get("cls"):
                method_part = f".{owner['method']}" if owner.get("method") else ""
                if owner.get("file"):
                    next_step = (
                        f"Inspect `{owner['cls']}{method_part}` in `{owner['file']}` and verify collaborators/branch handling."
                    )
            return {"answer_1": grounded, "next_step": next_step, "answer_shape": "explain"}
        if owner.get("cls"):
            method_part = f".{owner['method']}" if owner.get("method") else ""
            answer = (
                f"Based on current evidence, `{owner['cls']}{method_part}` appears to be the main anchor for this behavior."
            )
            next_step = ""
            if owner.get("file"):
                next_step = (
                    f"Inspect `{owner['cls']}{method_part}` in `{owner['file']}` and verify collaborators/branch handling."
                )
            return {"answer_1": answer, "next_step": next_step, "answer_shape": "explain"}
        return {"answer_1": first, "next_step": second, "answer_shape": "explain"}

    # Why/debug phrasing in prompt path.
    if _is_debug_why_query(query):
        answer = f"Hypothesis (based on current evidence): {first}"
        next_step = second or (
            f"Next inspection target: `{owner.get('cls')}`"
            + (f".{owner.get('method')}" if owner.get("method") else "")
            + (f" in `{owner.get('file')}`." if owner.get("file") else ".")
        )
        return {"answer_1": answer, "next_step": next_step, "answer_shape": "debug"}

    return {"answer_1": first, "next_step": second, "answer_shape": "default"}

