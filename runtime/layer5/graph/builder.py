from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from runtime.layer5.authority.code_index_models import CodeIndex
from runtime.layer5.authority.registry_loader import AuthorityRegistry
from runtime.layer5.graph.models import CodeIntelligenceGraph, GraphEdge, GraphNode


_LIFECYCLE_METHODS = frozenset(
    {
        "beforeAdd",
        "beforeUpdate",
        "beforeDelete",
        "getItem",
        "start",
    }
)

_READ_METHOD_MARKERS = ("get", "read", "find", "fetch", "load")
_WRITE_METHOD_MARKERS = ("set", "save", "update", "put", "write", "create", "delete")


def _file_node_id(path: str) -> str:
    return f"file::{path}"


def _class_node_id(class_name: str) -> str:
    return f"class::{class_name}"


def _method_node_id(class_name: str, method_name: str) -> str:
    return f"method::{class_name}.{method_name}"


def _concept_node_id(concept: str) -> str:
    return f"concept::{concept}"


def _event_address_node_id(address: str) -> str:
    return f"event::{address}"


def _edge_id(src: str, typ: str, dst: str, qualifier: str = "") -> str:
    payload = f"{src}|{typ}|{dst}|{qualifier}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _norm(path: str) -> str:
    return path.replace("\\", "/")


class GraphBuilder:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def build(
        self,
        code_index: CodeIndex,
        *,
        registry: Optional[AuthorityRegistry] = None,
        repo_identity: Optional[Dict[str, str]] = None,
        extractor_version: str = "cig_builder.v1",
        config_hash: str = "",
    ) -> CodeIntelligenceGraph:
        nodes: Dict[str, GraphNode] = {}
        edges: Dict[str, GraphEdge] = {}

        # Base file/class/method graph.
        for relative_path, file_record in sorted(code_index.files.items()):
            fp = _norm(relative_path)
            file_node = GraphNode(
                id=_file_node_id(fp),
                kind="file",
                label=fp,
                attrs={"package": file_record.package, "module": file_record.module},
            )
            nodes[file_node.id] = file_node

            for cls in file_record.classes:
                cls_id = _class_node_id(cls.name)
                nodes.setdefault(
                    cls_id,
                    GraphNode(
                        id=cls_id,
                        kind="class",
                        label=cls.name,
                        attrs={"package": cls.package, "file": fp},
                    ),
                )
                self._add_edge(edges, file_node.id, "DECLARES", cls_id, "graph_assembler")

                if cls.superclass:
                    base_id = _class_node_id(cls.superclass.strip())
                    nodes.setdefault(
                        base_id,
                        GraphNode(id=base_id, kind="class", label=cls.superclass.strip(), attrs={}),
                    )
                    self._add_edge(edges, cls_id, "EXTENDS", base_id, "symbol_extractor")
                    if cls.superclass.strip() == "AbstractAPI":
                        self._add_edge(edges, cls_id, "API_CLASS_EXTENDS", base_id, "motadata_overlay")

                for method_name in sorted(set(cls.methods)):
                    method_id = _method_node_id(cls.name, method_name)
                    nodes.setdefault(
                        method_id,
                        GraphNode(
                            id=method_id,
                            kind="method",
                            label=f"{cls.name}.{method_name}",
                            attrs={"class": cls.name, "file": fp},
                        ),
                    )
                    self._add_edge(edges, cls_id, "CONTAINS", method_id, "symbol_extractor")
                    if cls.superclass and method_name in _LIFECYCLE_METHODS:
                        self._add_edge(edges, cls_id, "OVERRIDES", method_id, "motadata_overlay")

        # Import and call edges.
        for relative_path, file_record in sorted(code_index.files.items()):
            src_file_id = _file_node_id(_norm(relative_path))
            for imp in sorted(file_record.imports):
                dst = imp.rsplit(".", 1)[-1]
                dst_id = _class_node_id(dst)
                nodes.setdefault(dst_id, GraphNode(id=dst_id, kind="class", label=dst, attrs={}))
                self._add_edge(edges, src_file_id, "IMPORTS", dst_id, "import_dependency_extractor")

        for ce in code_index.call_edges:
            src_id = _method_node_id(ce.source_class, ce.source_method)
            dst_id = _method_node_id(ce.target_class, ce.target_method)
            nodes.setdefault(
                src_id,
                GraphNode(
                    id=src_id,
                    kind="method",
                    label=f"{ce.source_class}.{ce.source_method}",
                    attrs={"class": ce.source_class, "file": _norm(ce.source_file)},
                ),
            )
            nodes.setdefault(
                dst_id,
                GraphNode(
                    id=dst_id,
                    kind="method",
                    label=f"{ce.target_class}.{ce.target_method}",
                    attrs={"class": ce.target_class, "file": _norm(ce.target_file or "")},
                ),
            )
            self._add_edge(
                edges,
                src_id,
                "CALLS",
                dst_id,
                "call_edge_extractor",
                attrs={"confidence": ce.confidence.value},
            )
            self._add_config_store_edges(nodes, edges, src_id, ce.target_class, ce.target_method)

        # Entrypoints and entrypoint invokes.
        for ep in code_index.entry_points:
            src_id = _method_node_id(ep.class_name, ep.method_name)
            nodes.setdefault(
                src_id,
                GraphNode(
                    id=src_id,
                    kind="entrypoint",
                    label=f"{ep.class_name}.{ep.method_name}",
                    attrs={"entry_type": ep.entry_type.value, "file": _norm(ep.relative_path)},
                ),
            )
            if ep.class_name == "APIServer" and ep.method_name == "start":
                for invoke in ep.invokes:
                    if "." in invoke:
                        inv_cls, _ = invoke.split(".", 1)
                        dst_id = _class_node_id(inv_cls)
                        nodes.setdefault(
                            dst_id,
                            GraphNode(id=dst_id, kind="class", label=inv_cls, attrs={}),
                        )
                        self._add_edge(edges, src_id, "REGISTERS_ROUTE", dst_id, "entrypoint_extractor")
            for invoke in ep.invokes:
                if "." not in invoke:
                    continue
                inv_cls, inv_method = invoke.split(".", 1)
                dst_id = _method_node_id(inv_cls, inv_method)
                nodes.setdefault(
                    dst_id,
                    GraphNode(id=dst_id, kind="method", label=invoke, attrs={"class": inv_cls}),
                )
                self._add_edge(edges, src_id, "ENTRYPOINT_INVOKES", dst_id, "entrypoint_extractor")

        # Event bus publish/consume edges from source text (deterministic regex).
        self._extract_eventbus_edges(nodes, edges, code_index.files.keys())

        # Registry overlay edges.
        if registry:
            self._apply_registry_overlay(nodes, edges, registry)

        node_list = sorted(nodes.values(), key=lambda n: n.id)
        edge_list = sorted(edges.values(), key=lambda e: (e.src, e.type, e.dst, e.id))
        adjacency = self._build_adjacency(edge_list)
        graph = CodeIntelligenceGraph(
            generated_at=datetime.now(timezone.utc).isoformat(),
            repo_identity=repo_identity or {},
            extractor_identity={"extractor_version": extractor_version, "config_hash": config_hash},
            nodes=node_list,
            edges=edge_list,
            adjacency=adjacency,
        )
        graph.stats = {
            "node_count": len(node_list),
            "edge_count": len(edge_list),
            "file_count": len(code_index.files),
        }
        graph.diagnostics = {
            "invariant": "Repo is truth. Graph is map. LLM is narrator. Runtime is judge."
        }
        return graph

    def _add_edge(
        self,
        edges: Dict[str, GraphEdge],
        src: str,
        typ: str,
        dst: str,
        source: str,
        *,
        attrs: Optional[Dict[str, str]] = None,
    ) -> None:
        eid = _edge_id(src, typ, dst)
        merged_attrs = {"provenance.source": source, "provenance.mode": "deterministic_static"}
        if attrs:
            merged_attrs.update(attrs)
        edges[eid] = GraphEdge(id=eid, src=src, type=typ, dst=dst, attrs=merged_attrs)

    def _add_config_store_edges(
        self,
        nodes: Dict[str, GraphNode],
        edges: Dict[str, GraphEdge],
        src_method_id: str,
        target_class: str,
        target_method: str,
    ) -> None:
        if "configstore" not in target_class.lower():
            return
        dst = _class_node_id(target_class)
        nodes.setdefault(dst, GraphNode(id=dst, kind="class", label=target_class, attrs={}))
        t = target_method.lower()
        if any(m in t for m in _READ_METHOD_MARKERS):
            self._add_edge(edges, src_method_id, "READS_FROM", dst, "motadata_overlay")
        if any(m in t for m in _WRITE_METHOD_MARKERS):
            self._add_edge(edges, src_method_id, "WRITES_TO", dst, "motadata_overlay")

    def _extract_eventbus_edges(
        self,
        nodes: Dict[str, GraphNode],
        edges: Dict[str, GraphEdge],
        files: Iterable[str],
    ) -> None:
        publish_patterns = ('publish("', "send(")
        consume_patterns = ('consumer("', "@ConsumeEvent(")
        for relative_path in sorted(files):
            abs_path = self.workspace_root / relative_path
            try:
                content = abs_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            class_name = abs_path.stem
            method_id = _method_node_id(class_name, "__eventbus_regex__")
            nodes.setdefault(
                method_id,
                GraphNode(
                    id=method_id,
                    kind="method",
                    label=f"{class_name}.__eventbus_regex__",
                    attrs={
                        "class": class_name,
                        "evidence_mode": "regex_scan",
                    },
                ),
            )
            for marker in publish_patterns:
                for address in _extract_string_args(content, marker):
                    dst = _event_address_node_id(address)
                    nodes.setdefault(dst, GraphNode(id=dst, kind="event_address", label=address, attrs={}))
                    self._add_edge(
                        edges,
                        method_id,
                        "PUBLISHES_TO",
                        dst,
                        "motadata_overlay",
                        attrs={
                            "confidence": "bounded",
                            "provenance.detail": "regex_derived_eventbus_edge",
                        },
                    )
            for marker in consume_patterns:
                for address in _extract_string_args(content, marker):
                    dst = _event_address_node_id(address)
                    nodes.setdefault(dst, GraphNode(id=dst, kind="event_address", label=address, attrs={}))
                    self._add_edge(
                        edges,
                        method_id,
                        "CONSUMES_FROM",
                        dst,
                        "motadata_overlay",
                        attrs={
                            "confidence": "bounded",
                            "provenance.detail": "regex_derived_eventbus_edge",
                        },
                    )

    def _apply_registry_overlay(
        self,
        nodes: Dict[str, GraphNode],
        edges: Dict[str, GraphEdge],
        registry: AuthorityRegistry,
    ) -> None:
        for concept_name, concept in sorted(registry.concepts.items()):
            cnode = _concept_node_id(concept_name)
            nodes.setdefault(cnode, GraphNode(id=cnode, kind="concept", label=concept_name, attrs={}))
            owner = _class_node_id(concept.primary_owner.class_name)
            nodes.setdefault(owner, GraphNode(id=owner, kind="class", label=concept.primary_owner.class_name, attrs={}))
            self._add_edge(edges, cnode, "CONCEPT_OWNS", owner, "ownership_overlay_extractor")
            for collab in concept.collaborators:
                collab_class = Path(collab.file).stem
                c_id = _class_node_id(collab_class)
                nodes.setdefault(c_id, GraphNode(id=c_id, kind="class", label=collab_class, attrs={}))
                self._add_edge(edges, cnode, "CONCEPT_COLLABORATES_WITH", c_id, "ownership_overlay_extractor")
            for d in concept.forbidden_distractors:
                d_class = Path(d.file).stem
                d_id = _class_node_id(d_class)
                nodes.setdefault(d_id, GraphNode(id=d_id, kind="class", label=d_class, attrs={}))
                self._add_edge(edges, cnode, "CONCEPT_FORBIDS", d_id, "ownership_overlay_extractor")

            if concept.primary_owner.class_name == "MailServerConfiguration":
                mail_concept = _concept_node_id("notification_mail_delivery")
                nodes.setdefault(mail_concept, GraphNode(id=mail_concept, kind="concept", label="notification_mail_delivery", attrs={}))
                self._add_edge(edges, owner, "AFFECTS", mail_concept, "motadata_overlay")
            if concept.primary_owner.class_name == "NotificationEngine":
                n_concept = _concept_node_id("notification_dispatch_reply")
                nodes.setdefault(n_concept, GraphNode(id=n_concept, kind="concept", label="notification_dispatch_reply", attrs={}))
                self._add_edge(edges, owner, "HANDLES", n_concept, "motadata_overlay")

    def _build_adjacency(self, edges: List[GraphEdge]) -> Dict[str, Dict[str, List[str]]]:
        forward: Dict[str, Dict[str, List[str]]] = {}
        reverse: Dict[str, Dict[str, List[str]]] = {}
        for edge in edges:
            forward.setdefault(edge.src, {}).setdefault(edge.type, []).append(edge.dst)
            reverse.setdefault(edge.dst, {}).setdefault(edge.type, []).append(edge.src)
        for node_id in list(forward.keys()):
            for typ in list(forward[node_id].keys()):
                forward[node_id][typ] = sorted(set(forward[node_id][typ]))
        for node_id in list(reverse.keys()):
            for typ in list(reverse[node_id].keys()):
                reverse[node_id][typ] = sorted(set(reverse[node_id][typ]))
        return {"forward": forward, "reverse": reverse}


def _extract_string_args(content: str, marker: str) -> List[str]:
    out: List[str] = []
    start = 0
    while True:
        idx = content.find(marker, start)
        if idx < 0:
            break
        i = idx + len(marker)
        end = content.find('"', i)
        if end > i:
            value = content[i:end].strip()
            if value:
                out.append(value)
        start = i
    return out


def graph_content_hash(graph: CodeIntelligenceGraph) -> str:
    payload = {
        "schema_version": graph.schema_version,
        "graph_version": graph.graph_version,
        "nodes": [n.to_dict() for n in graph.nodes],
        "edges": [e.to_dict() for e in graph.edges],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

