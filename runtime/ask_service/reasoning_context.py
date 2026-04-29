from __future__ import annotations

import re
from typing import Any, Dict, List, Sequence

# ---------------------------------------------------------------------------
# Pass D.1 — Reasoning Context Block
# Builds a structured, role-labeled context bundle from evidence + graph so
# the model can reason about architecture without hallucinating.
# ---------------------------------------------------------------------------

# Role-classification keyword sets
_ENTRYPOINT_WORDS = {"start", "bootstrap", "init", "main", "run", "launch", "begin", "entry"}
_ABSTRACT_WORDS = {"abstract", "base", "iface", "interface"}
_STORE_WORDS = {"store", "cache", "repository", "repo", "manager", "config", "registry", "database", "db"}
_HANDLER_WORDS = {"handler", "processor", "listener", "consumer", "service", "engine", "dispatcher", "resolver"}
_NOISE_WORDS = {"test", "mock", "stub", "fake", "helper", "util", "utils", "dto", "vo", "pojo"}


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _norm_path(path: str) -> str:
    return str(path or "").replace("\\", "/").strip()


def _short_class(name: str) -> str:
    """Return the last component of a dotted name, e.g. com.foo.Bar -> Bar."""
    parts = str(name or "").split(".")
    return parts[-1].strip() if parts else str(name or "").strip()


def _classify_node(name: str, method: str = "") -> str:
    """Return a D.1 bucket name for a class/method pair."""
    cls_low = _short_class(name).lower()
    meth_low = (method or "").lower()
    combined = cls_low + " " + meth_low

    if any(w in combined for w in _NOISE_WORDS):
        return "noise"
    if any(w in meth_low for w in _ENTRYPOINT_WORDS) or any(w in cls_low for w in _ENTRYPOINT_WORDS):
        return "entrypoint"
    if cls_low.startswith("abstract") or any(w in cls_low for w in _ABSTRACT_WORDS):
        return "abstraction"
    if any(w in cls_low for w in _STORE_WORDS):
        return "store"
    if any(w in cls_low for w in _HANDLER_WORDS):
        return "handler"
    return "collaborator"


def _role_description(name: str, method: str = "") -> str:
    """Human-readable role phrase for prompt rendering."""
    bucket = _classify_node(name, method)
    cls = _short_class(name)
    meth = (method or "").strip()
    anchor = f"{cls}.{meth}" if meth else cls
    roles = {
        "entrypoint": f"entrypoint / bootstrap ({anchor})",
        "abstraction": f"shared abstraction / base class ({anchor})",
        "store": f"configuration store / persistence ({anchor})",
        "handler": f"request handler / logic processor ({anchor})",
        "collaborator": f"collaborator ({anchor})",
        "noise": f"utility / test helper ({anchor})",
    }
    return roles.get(bucket, f"collaborator ({anchor})")


def _entry_citation(index_1_based: int, rel_path: str) -> str:
    rel = _norm_path(rel_path)
    if rel:
        return f"E{index_1_based}:{rel}"
    return f"E{index_1_based}"


def _extract_entry_refs(evidence_bundle: Dict[str, Any], cap: int = 8) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    entries = _as_list(evidence_bundle.get("entries"))
    for idx, ent in enumerate(entries[:cap], start=1):
        if not isinstance(ent, dict):
            continue
        rel = _norm_path(str(ent.get("relative_path") or ""))
        score = ent.get("retrieval_score")
        snippet = _as_dict(ent.get("snippet"))
        start = snippet.get("start_line")
        end = snippet.get("end_line")
        line_span = ""
        if isinstance(start, int) and isinstance(end, int):
            line_span = f"#L{start}-L{end}"
        # Infer class name from path (e.g. src/.../MailServerConfiguration.java -> MailServerConfiguration)
        path_parts = rel.replace("\\", "/").split("/")
        file_stem = path_parts[-1].rsplit(".", 1)[0] if path_parts else ""
        refs.append(
            {
                "id": f"E{idx}",
                "path": rel,
                "line_span": line_span,
                "retrieval_score": score,
                "citation": _entry_citation(idx, rel),
                "selection_reason": str(snippet.get("selection_reason") or ""),
                "retrieval_role": str(ent.get("retrieval_role") or ""),
                "inferred_class": file_stem,
                "d1_bucket": _classify_node(file_stem),
            }
        )
    return refs


def _extract_primary_owner(authority_resolution: Dict[str, Any], entry_refs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    po = _as_dict(authority_resolution.get("primary_owner"))
    owner_file = _norm_path(str(po.get("file") or ""))
    cls = str(po.get("class") or "").strip()
    method = str(po.get("method") or "").strip()
    owner_citation = ""
    for ref in entry_refs:
        if owner_file and _norm_path(str(ref.get("path") or "")) == owner_file:
            owner_citation = str(ref.get("citation") or "")
            break
    # Infer class from file if not provided
    if not cls and owner_file:
        stem = owner_file.replace("\\", "/").split("/")[-1].rsplit(".", 1)[0]
        cls = stem
    return {
        "class": cls,
        "method": method,
        "file": owner_file,
        "status": str(authority_resolution.get("authority_status") or ""),
        "confidence": str(authority_resolution.get("authority_confidence") or ""),
        "citation": owner_citation,
        "role_description": _role_description(cls, method),
        "d1_bucket": _classify_node(cls, method),
    }


def _extract_inheritance(graph_traversal: Dict[str, Any], entry_refs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    chain = [str(x).strip() for x in (_as_list(graph_traversal.get("inheritance_chain")) or _as_list(graph_traversal.get("inheritance"))) if str(x).strip()]
    citation = ""
    if entry_refs:
        citation = str(entry_refs[0].get("citation") or "")
    return {
        "chain": chain[:6],
        "citation": citation,
    }


def _extract_collaborators(
    authority_resolution: Dict[str, Any],
    graph_traversal: Dict[str, Any],
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()

    for item in _as_list(authority_resolution.get("collaborators")):
        if not isinstance(item, dict):
            continue
        cls = str(item.get("class") or "").strip()
        file_path = _norm_path(str(item.get("file") or ""))
        if not cls and not file_path:
            continue
        if not cls and file_path:
            cls = file_path.replace("\\", "/").split("/")[-1].rsplit(".", 1)[0]
        key = (cls or file_path).lower()
        if key in seen:
            continue
        seen.add(key)
        bucket = _classify_node(cls)
        if bucket == "noise":
            continue
        out.append(
            {
                "name": cls or file_path,
                "role": _role_description(cls),
                "file": file_path,
                "citation": file_path or "authority",
                "d1_bucket": bucket,
            }
        )

    for label in _as_list(graph_traversal.get("collaborators"))[:10]:
        name = str(label or "").strip()
        if not name:
            continue
        cls = _short_class(name)
        key = cls.lower()
        if key in seen:
            continue
        bucket = _classify_node(cls)
        if bucket == "noise":
            continue
        seen.add(key)
        out.append(
            {
                "name": cls,
                "role": _role_description(cls),
                "file": "",
                "citation": "G:collaborators",
                "d1_bucket": bucket,
            }
        )
    return out[:10]


def _extract_graph_paths(graph_traversal: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_paths: List[str] = []
    for key in ("flow_paths", "entrypoint_flow", "call_paths", "call_chain"):
        for p in _as_list(graph_traversal.get(key)):
            ps = str(p or "").strip()
            if ps and ps not in raw_paths:
                raw_paths.append(ps)
    out: List[Dict[str, Any]] = []
    for idx, path in enumerate(raw_paths[:3], start=1):
        out.append({"id": f"G{idx}", "path": path, "citation": f"G{idx}"})
    return out


def _build_d1_typed_nodes(
    entry_refs: List[Dict[str, Any]],
    primary_owner: Dict[str, Any],
    collaborators: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Produce the D.1 typed-node map:
      entrypoints, abstractions, handlers, stores, collaborators (filtered)
    Merges evidence entries + authority collaborators, de-duped by class name.
    """
    seen: set[str] = set()
    buckets: Dict[str, List[Dict[str, Any]]] = {
        "entrypoints": [],
        "abstractions": [],
        "handlers": [],
        "stores": [],
        "collaborators": [],
    }

    def _add(cls: str, method: str, path: str, citation: str) -> None:
        key = _short_class(cls).lower() if cls else path.lower()
        if not key or key in seen:
            return
        bucket = _classify_node(cls or path, method)
        if bucket in ("noise",):
            return
        target = bucket if bucket in buckets else "collaborators"
        seen.add(key)
        buckets[target].append(
            {
                "class": _short_class(cls) if cls else "",
                "method": method,
                "path": path,
                "citation": citation,
                "role": _role_description(cls or path, method),
            }
        )

    # Primary owner always first
    po_cls = str(primary_owner.get("class") or "")
    po_meth = str(primary_owner.get("method") or "")
    po_path = str(primary_owner.get("file") or "")
    po_cite = str(primary_owner.get("citation") or po_path or "primary_owner")
    if po_cls:
        _add(po_cls, po_meth, po_path, po_cite)

    # Evidence entries by inferred class
    for ref in entry_refs:
        cls = str(ref.get("inferred_class") or "")
        path = str(ref.get("path") or "")
        cite = str(ref.get("citation") or "")
        _add(cls, "", path, cite)

    # Authority collaborators
    for c in collaborators:
        cls = str(c.get("name") or "")
        path = str(c.get("file") or "")
        cite = str(c.get("citation") or "")
        _add(cls, "", path, cite)

    return buckets


def _infer_flow_steps(
    primary_owner: Dict[str, Any],
    typed_nodes: Dict[str, List[Dict[str, Any]]],
    graph_paths: List[Dict[str, Any]],
) -> List[str]:
    """
    Produce 2–3 natural-language flow steps from typed nodes + graph paths.
    Keeps only what is in evidence; no invented steps.
    """
    steps: List[str] = []
    po_cls = str(primary_owner.get("class") or "")
    po_meth = str(primary_owner.get("method") or "")
    anchor = f"{po_cls}.{po_meth}" if po_cls and po_meth else (po_cls or "(unknown anchor)")

    # Step 1: entrypoint or primary owner (human explanation tone, not diagnostic labels)
    entrypoints = typed_nodes.get("entrypoints", [])
    if entrypoints:
        ep = entrypoints[0]
        ep_cls = str(ep.get("class") or "")
        ep_meth = str(ep.get("method") or "")
        ep_anchor = f"{ep_cls}.{ep_meth}" if ep_cls and ep_meth else (ep_cls or "(entry)")
        steps.append(f"{ep_anchor} starts here and routes incoming work.")
    elif po_cls:
        steps.append(f"{anchor} is the entrypoint and delegates to downstream components.")

    # Step 2: handler or abstraction
    handlers = typed_nodes.get("handlers", [])
    abstractions = typed_nodes.get("abstractions", [])
    if handlers:
        names = ", ".join(str(h.get("class") or "") for h in handlers[:2] if h.get("class"))
        if names:
            steps.append(f"Handlers such as {names} carry the request forward.")
    elif abstractions:
        names = ", ".join(str(a.get("class") or "") for a in abstractions[:2] if a.get("class"))
        if names:
            steps.append(f"Shared lifecycle behavior runs through {names}.")

    # Step 3: store/persistence or graph-derived continuation (no G# debug tokens)
    stores = typed_nodes.get("stores", [])
    if stores:
        names = ", ".join(str(s.get("class") or "") for s in stores[:2] if s.get("class"))
        if names:
            steps.append(f"Configuration and state flow through {names}.")
    elif graph_paths:
        p = graph_paths[0]
        raw = str(p.get("path") or "").strip()
        snippet = raw[:200] if raw else ""
        if snippet:
            steps.append(f"Call relationships extend through: {snippet}.")
        else:
            steps.append("Additional call relationships appear in the retrieved structure snapshot.")

    return steps[:3]


def build_reasoning_context(
    *,
    query: str,
    evidence_bundle: Dict[str, Any],
    graph_traversal: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """
    Pass D.1: Build structured, role-labeled Reasoning Context Block.

    Returns a dict with typed node buckets (entrypoints, abstractions,
    handlers, stores, collaborators), inferred flow steps, and evidence anchors.
    """
    evidence = _as_dict(evidence_bundle)
    gt = _as_dict(graph_traversal)
    authority = _as_dict(evidence.get("authority_resolution"))
    entry_refs = _extract_entry_refs(evidence)
    primary_owner = _extract_primary_owner(authority, entry_refs)
    inheritance = _extract_inheritance(gt, entry_refs)
    collaborators = _extract_collaborators(authority, gt)
    graph_paths = _extract_graph_paths(gt)

    typed_nodes = _build_d1_typed_nodes(entry_refs, primary_owner, collaborators)
    flow_steps = _infer_flow_steps(primary_owner, typed_nodes, graph_paths)

    anchor_method = ""
    if primary_owner.get("class"):
        method = str(primary_owner.get("method") or "").strip()
        anchor_method = f"{primary_owner['class']}.{method}" if method else str(primary_owner["class"])

    # Confidence limits: note what is not resolved
    coverage_gaps: List[str] = []
    if not typed_nodes.get("entrypoints") and not typed_nodes.get("handlers"):
        coverage_gaps.append("Full request routing not resolved in current evidence.")
    if not typed_nodes.get("stores"):
        coverage_gaps.append("Persistence/store call chain not resolved.")
    if not graph_paths:
        coverage_gaps.append("No graph call-paths available; flow is inferred from class names only.")

    return {
        "schema_version": "reasoning_context.d1",
        "query": str(query or ""),
        "primary_owner": primary_owner,
        "anchor_method": anchor_method,
        "inheritance": inheritance,
        "typed_nodes": typed_nodes,
        "flow_steps": flow_steps,
        "coverage_gaps": coverage_gaps,
        "top_graph_paths": graph_paths,
        "evidence_citations": [ref.get("citation") for ref in entry_refs if ref.get("citation")],
        "evidence_sources": entry_refs,
        # Kept for backward-compat with answer_shaping / v1_ingest callers
        "collaborators": collaborators,
    }


def render_reasoning_context_for_prompt(reasoning_context: Dict[str, Any]) -> str:
    """
    Pass D.1 renderer: produce a structured, role-labeled text block for model prompts.

    Format mirrors the 'Reasoning Context' examples from the D.1 spec so the model
    sees labeled roles, typed nodes, and flow steps rather than raw JSON.
    """
    rc = _as_dict(reasoning_context)
    if not rc:
        return "Reasoning Context: unavailable"

    po = _as_dict(rc.get("primary_owner"))
    typed = _as_dict(rc.get("typed_nodes"))
    flow_steps = _as_list(rc.get("flow_steps"))
    gaps = _as_list(rc.get("coverage_gaps"))
    refs = _as_list(rc.get("evidence_sources"))
    graph_paths = _as_list(rc.get("top_graph_paths"))
    inh = _as_dict(rc.get("inheritance"))

    lines: List[str] = ["Reasoning Context:"]

    # --- Primary anchor ---
    po_cls = str(po.get("class") or "")
    po_meth = str(po.get("method") or "")
    po_file = str(po.get("file") or "")
    po_cite = str(po.get("citation") or po_file or "")
    if po_cls or po_meth:
        anchor_label = f"{po_cls}.{po_meth}" if po_cls and po_meth else (po_cls or po_meth)
        lines.append("")
        lines.append("Primary anchor:")
        line = f"  - {anchor_label}"
        if po.get("role_description"):
            line += f"\n    role: {po['role_description']}"
        if po_file:
            line += f"\n    source: {po_file}"
        if po_cite and po_cite != po_file:
            line += f"\n    citation: {po_cite}"
        lines.append(line)

    # --- Typed node sections ---
    _section_map = [
        ("entrypoints", "Entry points"),
        ("abstractions", "Abstractions"),
        ("handlers", "Handlers"),
        ("stores", "Stores / persistence"),
    ]
    for bucket_key, section_title in _section_map:
        nodes = _as_list(typed.get(bucket_key))
        # Skip if only entry is identical to primary owner
        visible = [
            n for n in nodes
            if isinstance(n, dict) and (
                _short_class(str(n.get("class") or "")).lower() != _short_class(po_cls).lower()
                or str(n.get("method") or "") != po_meth
            )
        ]
        if not visible:
            continue
        lines.append("")
        lines.append(f"{section_title}:")
        for node in visible[:3]:
            cls = str(node.get("class") or "")
            meth = str(node.get("method") or "")
            path = str(node.get("path") or "")
            cite = str(node.get("citation") or "")
            role = str(node.get("role") or "")
            label = f"{cls}.{meth}" if cls and meth else (cls or path)
            entry = f"  - {label}"
            if role:
                entry += f"\n    role: {role}"
            if path and path != po_file:
                entry += f"\n    source: {path}"
            if cite and cite not in (path, po_cite):
                entry += f"\n    citation: {cite}"
            lines.append(entry)

    # --- Collaborators (filtered, not noise) ---
    collabs = _as_list(typed.get("collaborators"))
    if collabs:
        lines.append("")
        lines.append("Collaborators:")
        for c in collabs[:4]:
            if not isinstance(c, dict):
                continue
            cls = str(c.get("class") or "")
            role = str(c.get("role") or "collaborator")
            path = str(c.get("path") or c.get("file") or "")
            cite = str(c.get("citation") or "")
            label = cls or path
            if not label:
                continue
            entry = f"  - {label}\n    role: {role}"
            if path and path != po_file:
                entry += f"\n    source: {path}"
            lines.append(entry)

    # --- Inheritance (if non-trivial) ---
    chain = _as_list(inh.get("chain"))
    if len(chain) >= 2:
        lines.append("")
        lines.append(f"Inheritance: {' -> '.join(str(x) for x in chain[:5])}")

    # --- Flow steps ---
    if flow_steps:
        lines.append("")
        lines.append("Flow:")
        for i, step in enumerate(flow_steps[:3], start=1):
            lines.append(f"  {i}. {step}")

    # --- Graph paths (first 2 raw, if available) ---
    if graph_paths:
        lines.append("")
        lines.append("Graph paths (deterministic):")
        for p in graph_paths[:2]:
            if not isinstance(p, dict):
                continue
            lines.append(f"  {p.get('id', 'G?')}: {str(p.get('path') or '')[:140]}")

    # --- Evidence anchors ---
    if refs:
        lines.append("")
        lines.append("Evidence anchors:")
        for ref in refs[:6]:
            if not isinstance(ref, dict):
                continue
            cid = str(ref.get("id") or "E?")
            path = str(ref.get("path") or "")
            span = str(ref.get("line_span") or "")
            bucket = str(ref.get("d1_bucket") or "")
            role_tag = f" [{bucket}]" if bucket and bucket not in ("collaborator", "") else ""
            lines.append(f"  {cid}: {path}{span}{role_tag}")

    # --- Confidence limits ---
    if gaps:
        lines.append("")
        lines.append("Confidence limits:")
        for gap in gaps:
            lines.append(f"  - {gap}")

    lines.append("")
    lines.append(
        "Grounding rule: use only the nodes and evidence listed above. "
        "Reference source paths when you cite a component. "
        "End with confidence limits if coverage is partial."
    )
    return "\n".join(lines)


def citations_present(text: str) -> bool:
    """True when text includes at least one allowed citation form."""
    raw = str(text or "")
    if re.search(r"\bE\d+\b", raw):
        return True
    if re.search(r"\bG\d+\b", raw):
        return True
    if re.search(r"[A-Za-z0-9_./\-]+\.(?:java|kt|py|yml|yaml|xml|json)", raw):
        return True
    return False
