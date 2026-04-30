from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

_CLASS_DEF_RE = re.compile(
    r"\b(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:class|interface|enum)\s+([A-Za-z_]\w*)\b"
)
_METHOD_DEF_RE = re.compile(
    r"""
    ^\s*
    (?:(?:public|private|protected)\s+)?
    (?:(?:static|final|synchronized|native|abstract|default)\s+)*
    (?:<[^>]+>\s+)?
    (?:(?:[\w\[\]<>.,?]+\s+)+)?
    (?P<name>[A-Za-z_]\w*)
    \s*\([^;{}]*\)\s*
    (?:throws\s+[^{]+)?\s*\{?
    """,
    re.VERBOSE,
)
_STATIC_IMPORT_RE = re.compile(r"^\s*import\s+static\s+([^;]+);")
_PACKAGE_RE = re.compile(r"^\s*package\s+([A-Za-z0-9_.]+)\s*;")
_CONST_DEF_RE = re.compile(
    r'\b(?:public|private|protected)?\s*static\s+final\s+String\s+([A-Z0-9_]+)\s*=\s*"([^"]*)"\s*;'
)
_ADDRESS_LITERAL_RE = re.compile(r'^\s*"([^"]+)"\s*$')
_CALL_RE = re.compile(
    r"""
    eventBus\(\)\s*\.\s*
    (?P<kind>publish|send|request|consumer|localConsumer)
    \s*\(\s*(?P<arg>[^,\)\n]+)
    """,
    re.VERBOSE,
)
_CONSUME_ANNOT_RE = re.compile(r"@ConsumeEvent\s*\(\s*\"([^\"]+)\"\s*\)")
_JAVA_KEYWORDS: Set[str] = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "return",
    "new",
    "throw",
    "case",
    "try",
    "do",
    "else",
    "synchronized",
}
_UNRESOLVED_SYMBOL = "__unresolved_static_or_lambda_context__"
_BAD_METHOD_NAMES = _JAVA_KEYWORDS
_UNRESOLVED_WARN_THRESHOLD = 0.70


def _edge_id(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _hash_obj(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _method_node_id(class_name: str, method_name: str) -> str:
    return f"method::{class_name}.{method_name}"


def _event_node_id(address: str) -> str:
    return f"event::{address}"


def _parse_call(
    arg_text: str,
    *,
    constants_by_full: Dict[str, str],
    static_imported_constants: Dict[str, str],
    static_imported_classes: List[str],
) -> Tuple[Optional[str], str, str]:
    text = (arg_text or "").strip()
    if any(x in text for x in ("+", "?", ":", " event.", " get", "(", ")")) and not _ADDRESS_LITERAL_RE.match(text):
        return None, text, "dynamic"
    m = _ADDRESS_LITERAL_RE.match(text)
    if m:
        return m.group(1).strip(), text, "resolved"
    if text.startswith("EventBusConstants."):
        key = text.split(".", 1)[1]
        resolved = constants_by_full.get(f"EventBusConstants.{key}")
        if resolved:
            return resolved, text, "resolved"
        return None, text, "unresolved_constant"
    if "." in text:
        resolved = constants_by_full.get(text)
        if resolved:
            return resolved, text, "resolved"
        last_two = ".".join(text.split(".")[-2:])
        resolved = constants_by_full.get(last_two)
        if resolved:
            return resolved, text, "resolved"
        return None, text, "unresolved_constant"
    if re.fullmatch(r"[A-Z_][A-Z0-9_]*", text):
        if text in static_imported_constants:
            return static_imported_constants[text], text, "resolved"
        for cls in static_imported_classes:
            resolved = constants_by_full.get(f"{cls}.{text}")
            if resolved:
                return resolved, text, "resolved"
        resolved = constants_by_full.get(f"EventBusConstants.{text}")
        if resolved:
            return resolved, text, "resolved"
        return None, text, "unresolved_constant"
    return None, text, "dynamic"


def _address_kind(address: str, resolved: bool) -> str:
    if not resolved:
        return "unknown"
    a = str(address or "").lower()
    if a.startswith("test.") or a.startswith("test_") or ".test" in a:
        return "test"
    if a.startswith("websocket.") or "websocket" in a or a.startswith("ws."):
        return "websocket"
    if a.startswith("event_") or a.startswith("ui_action_") or "heartbeat" in a or "control" in a:
        return "control"
    return "runtime"


def _build_constant_maps(workspace_root: Path, relative_files: Iterable[str]) -> Dict[str, str]:
    constants_by_full: Dict[str, str] = {}
    for rel in sorted(set(relative_files)):
        if not rel.endswith(".java"):
            continue
        rel_norm = rel.replace("\\", "/")
        path = workspace_root / rel_norm
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        package_name = ""
        class_name = path.stem
        for line in lines:
            pm = _PACKAGE_RE.search(line)
            if pm:
                package_name = pm.group(1)
            cm = _CLASS_DEF_RE.search(line)
            if cm:
                class_name = cm.group(1)
            km = _CONST_DEF_RE.search(line)
            if km:
                key = km.group(1).strip()
                val = km.group(2)
                constants_by_full[f"{class_name}.{key}"] = val
                if package_name:
                    constants_by_full[f"{package_name}.{class_name}.{key}"] = val
    return constants_by_full


def _scan_file(path: Path, rel_path: str, *, constants_by_full: Dict[str, str]) -> Dict[str, Any]:
    class_name_default = path.stem
    class_stack: List[Tuple[str, int]] = []
    method_stack: List[Tuple[str, int]] = []
    records: List[Dict[str, Any]] = []
    unknowns: List[Dict[str, Any]] = []
    bad_method_name_count = 0
    static_imported_constants: Dict[str, str] = {}
    static_imported_classes: List[str] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {"records": [], "unknowns": [], "bad_method_name_count": 0}

    depth = 0
    pending_method: Optional[Tuple[str, int]] = None
    in_block_comment = False
    for i, line in enumerate(lines, start=1):
        scan_line = line
        if in_block_comment:
            end_idx = scan_line.find("*/")
            if end_idx >= 0:
                scan_line = scan_line[end_idx + 2 :]
                in_block_comment = False
            else:
                depth += line.count("{")
                depth -= line.count("}")
                continue
        while True:
            start_idx = scan_line.find("/*")
            if start_idx < 0:
                break
            end_idx = scan_line.find("*/", start_idx + 2)
            if end_idx >= 0:
                scan_line = scan_line[:start_idx] + " " + scan_line[end_idx + 2 :]
            else:
                scan_line = scan_line[:start_idx]
                in_block_comment = True
                break
        line_for_scan = scan_line.split("//", 1)[0]

        sim = _STATIC_IMPORT_RE.search(line)
        if sim:
            imported = sim.group(1).strip()
            if imported.endswith(".*"):
                static_imported_classes.append(imported[:-2].split(".")[-1])
            else:
                const_name = imported.split(".")[-1]
                resolved = constants_by_full.get(imported)
                if resolved is not None:
                    static_imported_constants[const_name] = resolved

        class_match = _CLASS_DEF_RE.search(line_for_scan)
        if class_match and "{" in line_for_scan:
            class_name = class_match.group(1)
            open_count = line_for_scan.count("{")
            close_count = line_for_scan.count("}")
            class_stack.append((class_name, depth + open_count - close_count))

        mm = _METHOD_DEF_RE.search(line_for_scan)
        if mm:
            method_name = mm.group("name")
            if method_name not in _JAVA_KEYWORDS:
                if "{" in line_for_scan:
                    open_count = line_for_scan.count("{")
                    close_count = line_for_scan.count("}")
                    method_stack.append((method_name, depth + open_count - close_count))
                else:
                    pending_method = (method_name, depth + 1)

        if pending_method and "{" in line_for_scan and not method_stack:
            method_stack.append((pending_method[0], pending_method[1]))
            pending_method = None
        if ";" in line_for_scan and pending_method:
            pending_method = None

        for m in _CALL_RE.finditer(line_for_scan):
            kind = str(m.group("kind") or "")
            arg = str(m.group("arg") or "")
            address, raw, resolution_state = _parse_call(
                arg,
                constants_by_full=constants_by_full,
                static_imported_constants=static_imported_constants,
                static_imported_classes=static_imported_classes,
            )
            source_class = class_stack[-1][0] if class_stack else class_name_default
            source_method = method_stack[-1][0] if method_stack else _UNRESOLVED_SYMBOL
            if source_method in _BAD_METHOD_NAMES:
                bad_method_name_count += 1
            if address:
                records.append(
                    {
                        "kind": kind,
                        "address": address,
                        "address_kind": _address_kind(address, True),
                        "source_class": source_class,
                        "source_method": source_method,
                        "file": rel_path,
                        "line": i,
                        "snippet": line.strip(),
                    }
                )
            else:
                unknown_type = "DYNAMIC_ADDRESS" if resolution_state == "dynamic" else "UNRESOLVED_ADDRESS"
                unknowns.append(
                    {
                        "unknown_type": unknown_type,
                        "source": {
                            "file": rel_path,
                            "class": source_class,
                            "method": source_method,
                            "line": i,
                        },
                        "raw_token": raw,
                        "reason": f"Could not statically resolve {kind} address token",
                        "address_kind": "unknown",
                        "confidence": "unknown",
                        "evidence": {
                            "file": rel_path,
                            "class": source_class,
                            "method": source_method,
                            "line": i,
                            "snippet": line.strip(),
                        },
                    }
                )

        for m in _CONSUME_ANNOT_RE.finditer(line_for_scan):
            address = str(m.group(1) or "").strip()
            if not address:
                continue
            source_class = class_stack[-1][0] if class_stack else class_name_default
            source_method = method_stack[-1][0] if method_stack else _UNRESOLVED_SYMBOL
            if source_method in _BAD_METHOD_NAMES:
                bad_method_name_count += 1
            records.append(
                {
                    "kind": "consumer",
                    "address": address,
                    "address_kind": _address_kind(address, True),
                    "source_class": source_class,
                    "source_method": source_method,
                    "file": rel_path,
                    "line": i,
                    "snippet": line.strip(),
                }
            )

        depth += line_for_scan.count("{")
        depth -= line_for_scan.count("}")
        while method_stack and depth < method_stack[-1][1]:
            method_stack.pop()
        while class_stack and depth < class_stack[-1][1]:
            class_stack.pop()

    return {"records": records, "unknowns": unknowns, "bad_method_name_count": bad_method_name_count}


def build_eventbus_topology_map(
    *, workspace_root: Path, relative_files: Iterable[str], repo_identity: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    constants_by_full = _build_constant_maps(workspace_root, relative_files)
    recs: List[Dict[str, Any]] = []
    unknowns: List[Dict[str, Any]] = []
    bad_method_name_count = 0
    for rel in sorted(set(relative_files)):
        if not rel.endswith(".java"):
            continue
        rel_norm = rel.replace("\\", "/")
        scanned = _scan_file(workspace_root / rel_norm, rel_norm, constants_by_full=constants_by_full)
        recs.extend(scanned["records"])
        unknowns.extend(scanned["unknowns"])
        bad_method_name_count += int(scanned.get("bad_method_name_count", 0))

    nodes: Dict[str, Dict[str, Any]] = {}
    edges: Dict[str, Dict[str, Any]] = {}
    publishers: Dict[str, List[Dict[str, Any]]] = {}
    consumers: Dict[str, List[Dict[str, Any]]] = {}

    for r in recs:
        method_id = _method_node_id(r["source_class"], r["source_method"])
        event_id = _event_node_id(r["address"])
        nodes.setdefault(
            method_id,
            {
                "node_id": method_id,
                "node_type": "method",
                "label": f"{r['source_class']}.{r['source_method']}",
                "attrs": {"file": r["file"]},
            },
        )
        nodes.setdefault(
            event_id,
            {
                "node_id": event_id,
                "node_type": "event_address",
                "label": r["address"],
                "attrs": {},
            },
        )

        kind = str(r["kind"])
        if kind in {"publish", "send", "request"}:
            edge_type = "PUBLISHES_TO_ADDRESS"
            publishers.setdefault(r["address"], []).append(r)
        else:
            edge_type = "CONSUMES_FROM_ADDRESS"
            consumers.setdefault(r["address"], []).append(r)

        payload = f"{method_id}|{edge_type}|{event_id}|{r['file']}|{r['line']}"
        edge_id = _edge_id(payload)
        edges[edge_id] = {
            "edge_id": edge_id,
            "edge_type": edge_type,
            "source": method_id,
            "target": event_id,
            "address": r["address"],
            "address_kind": r.get("address_kind", "unknown"),
            "confidence": "bounded",
            "evidence": {
                "file": r["file"],
                "class": r["source_class"],
                "method": r["source_method"],
                "line": r["line"],
                "snippet": r["snippet"],
            },
            "provenance": {
                "source": "eventbus_topology_extractor",
                "mode": "deterministic_static",
                "detail": "line_scanned_eventbus_call",
            },
        }

    for address in sorted(set(publishers.keys()) & set(consumers.keys())):
        for p in publishers[address]:
            for c in consumers[address]:
                src = _method_node_id(p["source_class"], p["source_method"])
                dst = _method_node_id(c["source_class"], c["source_method"])
                payload = f"{src}|PUBLISHES_TO_CONSUMER|{dst}|{address}"
                edge_id = _edge_id(payload)
                edges[edge_id] = {
                    "edge_id": edge_id,
                    "edge_type": "PUBLISHES_TO_CONSUMER",
                    "source": src,
                    "target": dst,
                    "address": address,
                    "address_kind": _address_kind(address, True),
                    "confidence": "bounded",
                    "evidence": [
                        {
                            "file": p["file"],
                            "class": p["source_class"],
                            "method": p["source_method"],
                            "line": p["line"],
                            "snippet": p["snippet"],
                        },
                        {
                            "file": c["file"],
                            "class": c["source_class"],
                            "method": c["source_method"],
                            "line": c["line"],
                            "snippet": c["snippet"],
                        },
                    ],
                    "provenance": {
                        "source": "eventbus_topology_extractor",
                        "mode": "deterministic_static",
                        "detail": "address_exact_join",
                    },
                }

    node_list = [nodes[k] for k in sorted(nodes.keys())]
    edge_list = [edges[k] for k in sorted(edges.keys())]
    unknown_list = sorted(
        unknowns,
        key=lambda x: (
            str(x.get("source", {}).get("file", "")),
            int(x.get("source", {}).get("line", 0)),
            str(x.get("raw_token", "")),
        ),
    )

    confidence_counts = {"high": 0, "bounded": 0, "unknown": 0}
    for e in edge_list:
        confidence_counts[str(e.get("confidence", "bounded"))] = (
            confidence_counts.get(str(e.get("confidence", "bounded")), 0) + 1
        )
    confidence_counts["unknown"] = confidence_counts.get("unknown", 0) + len(unknown_list)

    resolved_address_count = len(recs)
    unresolved_address_count = len([u for u in unknown_list if u.get("unknown_type") == "UNRESOLVED_ADDRESS"])
    dynamic_address_count = len([u for u in unknown_list if u.get("unknown_type") == "DYNAMIC_ADDRESS"])
    kind_counts = {"runtime": 0, "test": 0, "control": 0, "websocket": 0, "unknown": 0}
    for e in edge_list:
        k = str(e.get("address_kind", "unknown"))
        kind_counts[k] = kind_counts.get(k, 0) + 1
    for u in unknown_list:
        k = str(u.get("address_kind", "unknown"))
        kind_counts[k] = kind_counts.get(k, 0) + 1

    unresolved_ratio = 0.0
    if resolved_address_count + len(unknown_list) > 0:
        unresolved_ratio = len(unknown_list) / float(resolved_address_count + len(unknown_list))
    warnings: List[str] = []
    if unresolved_ratio > _UNRESOLVED_WARN_THRESHOLD:
        warnings.append(
            f"unresolved_ratio_exceeds_threshold:{unresolved_ratio:.3f}>{_UNRESOLVED_WARN_THRESHOLD:.3f}"
        )
    if bad_method_name_count > 0:
        warnings.append(f"bad_method_name_count_nonzero:{bad_method_name_count}")
    runtime_count = kind_counts.get("runtime", 0)
    test_control_count = kind_counts.get("test", 0) + kind_counts.get("control", 0)
    if test_control_count > runtime_count:
        warnings.append(
            f"test_control_dominates_runtime:test_control={test_control_count},runtime={runtime_count}"
        )

    payload = {
        "schema_version": "motadata_wiring_map.v1",
        "map_type": "eventbus_topology",
        "map_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "extractor_identity": {
            "name": "eventbus_topology_extractor",
            "version": "v1",
            "mode": "deterministic_static",
        },
        "repo_identity": dict(repo_identity or {}),
        "nodes": node_list,
        "edges": edge_list,
        "unknowns": unknown_list,
    }
    payload["validation_summary"] = {
        "node_count": len(node_list),
        "edge_count": len(edge_list),
        "unknown_count": len(unknown_list),
        "resolved_address_count": resolved_address_count,
        "unresolved_address_count": unresolved_address_count,
        "dynamic_address_count": dynamic_address_count,
        "address_kind_distribution": kind_counts,
        "bad_method_name_count": bad_method_name_count,
        "confidence_distribution": confidence_counts,
        "warnings": warnings,
        "determinism_hash": _hash_obj(
            {
                "schema_version": payload["schema_version"],
                "map_type": payload["map_type"],
                "nodes": node_list,
                "edges": edge_list,
                "unknowns": unknown_list,
            }
        ),
    }
    return payload

