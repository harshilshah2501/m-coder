#!/usr/bin/env python3
"""Ingest Java class/package structure into Neo4j.

The indexer parses ``*.java`` files with ``javalang`` and emits only grounded
workspace classes and package nodes. Parent relationships are added only when a
superclass or interface resolves to another class already present in this
workspace snapshot. Unresolved parent names are logged once and skipped so the
graph never invents fake external nodes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import javalang
from neo4j import GraphDatabase


LOG = logging.getLogger(__name__)
SCHEMA_PATH = Path(__file__).with_name("schema.cypher")
DEFAULT_JAVA_ROOT_ENV = "MOTADATA_JAVA_ROOT"
DEFAULT_NEO4J_PASSWORD = "NEO4J_PASSWORD"
PROGRESS_EVERY = 50


@dataclass(frozen=True)
class JavaClassRecord:
    class_name: str
    qualified_name: str
    package: str
    top_package: str
    extends: str | None
    implements: tuple[str, ...]
    is_abstract: bool
    is_interface: bool
    file_path: str
    imports: tuple[str, ...]


@dataclass(frozen=True)
class EventBusAddressConstant:
    key: str
    value: str
    class_qualified_name: str
    class_name: str
    field_name: str
    file_path: str


@dataclass(frozen=True)
class AnchorRecord:
    anchor_id: str
    category: str
    class_qualified_name: str
    file_path: str
    line_number: int
    snippet: str
    address_value: str | None = None
    address_token: str | None = None
    address_constant_key: str | None = None


ANCHOR_CATEGORIES = (
    "VERTICLE_REGISTRATION",
    "API_ROUTE_REGISTRATION",
    "EVENTBUS_CONSUMER_REGISTRATION",
    "EVENTBUS_PUBLISH_ANCHOR",
    "INTEGRATION_REGISTRATION",
    "CONFIG_ACCESS_ANCHOR",
)


def _neo4j_settings() -> tuple[str, str, str]:
    uri = os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", DEFAULT_NEO4J_PASSWORD)
    return uri, user, password


def _iter_java_files(java_root: Path) -> Iterable[Path]:
    for path in sorted(java_root.rglob("*.java")):
        if "target" in path.parts:
            continue
        yield path


def _top_package(package_name: str) -> str:
    prefix = "com.mindarray."
    if not package_name.startswith(prefix):
        return ""
    rest = package_name[len(prefix):]
    return rest.split(".", 1)[0]


def _type_name(type_node: Any) -> str | None:
    if type_node is None:
        return None
    name = getattr(type_node, "name", None)
    if isinstance(name, str) and name.strip():
        return name.strip()
    return None


def _simple_type_name(type_name: str | None) -> str | None:
    if not type_name:
        return None
    cleaned = type_name.strip()
    if not cleaned:
        return None
    cleaned = cleaned.split("<", 1)[0].strip()
    if not cleaned:
        return None
    return cleaned.rsplit(".", 1)[-1]


def _extract_imports(source: str) -> tuple[str, tuple[str, ...]]:
    package_match = re.search(r"(?m)^\s*package\s+([A-Za-z0-9_.]+)\s*;", source)
    package_name = package_match.group(1) if package_match else ""
    imports = tuple(
        match.group(1)
        for match in re.finditer(r"(?m)^\s*import\s+(?:static\s+)?([A-Za-z0-9_.*]+)\s*;", source)
    )
    return package_name, imports


def _line_to_class_ranges(source: str, file_records: list[JavaClassRecord]) -> list[tuple[int, str]]:
    names = {record.class_name: record.qualified_name for record in file_records}
    ranges: list[tuple[int, str]] = []
    class_pattern = re.compile(r"\b(?:class|interface)\s+([A-Za-z_][A-Za-z0-9_]*)\b")
    for line_no, line in enumerate(source.splitlines(), start=1):
        match = class_pattern.search(line)
        if not match:
            continue
        class_name = match.group(1)
        qualified_name = names.get(class_name)
        if qualified_name:
            ranges.append((line_no, qualified_name))
    ranges.sort(key=lambda item: item[0])
    return ranges


def _owner_class_for_line(
    line_number: int,
    class_ranges: list[tuple[int, str]],
    fallback_class: str | None,
) -> str | None:
    owner = fallback_class
    for start, qualified_name in class_ranges:
        if start > line_number:
            break
        owner = qualified_name
    return owner


def _build_eventbus_constant(
    *,
    package_name: str,
    class_name: str,
    field_name: str,
    value: str,
    file_path: str,
) -> EventBusAddressConstant:
    class_qualified_name = f"{package_name}.{class_name}" if package_name else class_name
    return EventBusAddressConstant(
        key=f"{class_qualified_name}.{field_name}",
        value=value,
        class_qualified_name=class_qualified_name,
        class_name=class_name,
        field_name=field_name,
        file_path=file_path,
    )


def _extract_eventbus_constants(source: str, file_path: str) -> list[EventBusAddressConstant]:
    package_name, _ = _extract_imports(source)
    class_stack: list[str] = []
    constants: list[EventBusAddressConstant] = []
    in_block_comment = False
    class_pattern = re.compile(r"\b(?:class|interface)\s+([A-Za-z_][A-Za-z0-9_]*)\b")
    const_pattern = re.compile(
        r'\b(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?String\s+'
        r'([A-Z][A-Z0-9_]*)\s*=\s*"([^"]+)"'
    )
    brace_depth = 0
    class_depths: list[int] = []

    for raw_line in source.splitlines():
        line, in_block_comment = _strip_inline_comments(raw_line, in_block_comment=in_block_comment)
        if not line.strip():
            brace_depth += line.count("{") - line.count("}")
            while class_depths and brace_depth < class_depths[-1]:
                class_depths.pop()
                class_stack.pop()
            continue

        class_match = class_pattern.search(line)
        if class_match and "{" in line:
            class_stack.append(class_match.group(1))
            class_depths.append(brace_depth)

        const_match = const_pattern.search(line)
        if const_match and class_stack:
            constants.append(
                _build_eventbus_constant(
                    package_name=package_name,
                    class_name=class_stack[-1],
                    field_name=const_match.group(1),
                    value=const_match.group(2),
                    file_path=file_path,
                )
            )

        brace_depth += line.count("{") - line.count("}")
        while class_depths and brace_depth < class_depths[-1]:
            class_depths.pop()
            class_stack.pop()

    return constants


def _build_eventbus_indexes(
    constants: list[EventBusAddressConstant],
) -> tuple[dict[str, EventBusAddressConstant], dict[str, list[EventBusAddressConstant]], dict[str, EventBusAddressConstant]]:
    by_key = {item.key: item for item in constants}
    by_ref: dict[str, list[EventBusAddressConstant]] = {}
    by_field: dict[str, list[EventBusAddressConstant]] = {}
    for item in constants:
        simple_class = item.class_name
        by_ref.setdefault(f"{simple_class}.{item.field_name}", []).append(item)
        by_ref.setdefault(item.field_name, []).append(item)
        by_field.setdefault(item.field_name, []).append(item)
    unique_by_field = {field: rows[0] for field, rows in by_field.items() if len(rows) == 1}
    return by_key, by_ref, unique_by_field


def _normalize_eventbus_token(token: str) -> str:
    cleaned = token.strip()
    cleaned = cleaned.rstrip(");,")
    cleaned = re.sub(r"^\(([^)]+)\)\s*", "", cleaned)
    return cleaned


def _resolve_eventbus_address(
    token: str,
    *,
    by_key: dict[str, EventBusAddressConstant],
    by_ref: dict[str, list[EventBusAddressConstant]],
    unique_by_field: dict[str, EventBusAddressConstant],
) -> tuple[str | None, str | None]:
    normalized = _normalize_eventbus_token(token)
    if not normalized:
        return None, None
    literal_match = re.fullmatch(r'"([^"]+)"', normalized)
    if literal_match:
        return literal_match.group(1), None
    if normalized in by_key:
        item = by_key[normalized]
        return item.value, item.key
    if normalized in by_ref and len(by_ref[normalized]) == 1:
        item = by_ref[normalized][0]
        return item.value, item.key
    tail = normalized.rsplit(".", 1)[-1]
    item = unique_by_field.get(tail)
    if item is not None:
        return item.value, item.key
    return None, None


def _anchor_id(*, file_path: str, class_qualified_name: str, line_number: int, category: str, snippet: str) -> str:
    digest = hashlib.sha256()
    digest.update(file_path.encode("utf-8", errors="replace"))
    digest.update(class_qualified_name.encode("utf-8", errors="replace"))
    digest.update(str(line_number).encode("utf-8"))
    digest.update(category.encode("utf-8"))
    digest.update(snippet.encode("utf-8", errors="replace"))
    return digest.hexdigest()


def _extract_file_anchors(
    *,
    source: str,
    file_path: str,
    file_records: list[JavaClassRecord],
    by_key: dict[str, EventBusAddressConstant],
    by_ref: dict[str, list[EventBusAddressConstant]],
    unique_by_field: dict[str, EventBusAddressConstant],
) -> tuple[list[AnchorRecord], dict[str, set[str]], dict[str, set[str]]]:
    class_ranges = _line_to_class_ranges(source, file_records)
    fallback_class = file_records[0].qualified_name if file_records else None
    anchors: list[AnchorRecord] = []
    publishers_by_address: dict[str, set[str]] = {}
    consumers_by_address: dict[str, set[str]] = {}
    in_block_comment = False

    for line_no, raw_line in enumerate(source.splitlines(), start=1):
        line, in_block_comment = _strip_inline_comments(raw_line, in_block_comment=in_block_comment)
        stripped = line.strip()
        if not stripped:
            continue
        owner = _owner_class_for_line(line_no, class_ranges, fallback_class)
        if owner is None:
            continue

        matched_categories: list[tuple[str, str]] = []
        if re.search(r"\bdeployVerticle\s*\(", stripped):
            matched_categories.append(("VERTICLE_REGISTRATION", stripped))
        if re.search(r"\brouter\s*\.\s*(?:route|get|post|put|delete|patch|options|head|mountSubRouter)\s*\(", stripped):
            matched_categories.append(("API_ROUTE_REGISTRATION", stripped))
        if re.search(r"\b(?:registerIntegration|registerPlugin|registerConnector|registerAdapter|addIntegration)\s*\(", stripped):
            matched_categories.append(("INTEGRATION_REGISTRATION", stripped))
        if re.search(r"\b(?:config|getConfig|getConfiguration|getProperty|ConfigurationManager)\s*\(", stripped):
            matched_categories.append(("CONFIG_ACCESS_ANCHOR", stripped))

        consumer_match = re.search(r"\.\s*(?:consumer|localConsumer)\s*\(\s*([^,\s\)]+)", stripped)
        if consumer_match:
            token = consumer_match.group(1)
            address_value, constant_key = _resolve_eventbus_address(
                token,
                by_key=by_key,
                by_ref=by_ref,
                unique_by_field=unique_by_field,
            )
            anchors.append(
                AnchorRecord(
                    anchor_id=_anchor_id(
                        file_path=file_path,
                        class_qualified_name=owner,
                        line_number=line_no,
                        category="EVENTBUS_CONSUMER_REGISTRATION",
                        snippet=stripped,
                    ),
                    category="EVENTBUS_CONSUMER_REGISTRATION",
                    class_qualified_name=owner,
                    file_path=file_path,
                    line_number=line_no,
                    snippet=stripped,
                    address_value=address_value,
                    address_token=_normalize_eventbus_token(token),
                    address_constant_key=constant_key,
                )
            )
            if address_value:
                consumers_by_address.setdefault(address_value, set()).add(owner)

        publish_match = re.search(r"\.\s*(?:publish|send|request)\s*\(\s*([^,\s\)]+)", stripped)
        if publish_match:
            token = publish_match.group(1)
            address_value, constant_key = _resolve_eventbus_address(
                token,
                by_key=by_key,
                by_ref=by_ref,
                unique_by_field=unique_by_field,
            )
            anchors.append(
                AnchorRecord(
                    anchor_id=_anchor_id(
                        file_path=file_path,
                        class_qualified_name=owner,
                        line_number=line_no,
                        category="EVENTBUS_PUBLISH_ANCHOR",
                        snippet=stripped,
                    ),
                    category="EVENTBUS_PUBLISH_ANCHOR",
                    class_qualified_name=owner,
                    file_path=file_path,
                    line_number=line_no,
                    snippet=stripped,
                    address_value=address_value,
                    address_token=_normalize_eventbus_token(token),
                    address_constant_key=constant_key,
                )
            )
            if address_value:
                publishers_by_address.setdefault(address_value, set()).add(owner)

        for category, snippet in matched_categories:
            anchors.append(
                AnchorRecord(
                    anchor_id=_anchor_id(
                        file_path=file_path,
                        class_qualified_name=owner,
                        line_number=line_no,
                        category=category,
                        snippet=snippet,
                    ),
                    category=category,
                    class_qualified_name=owner,
                    file_path=file_path,
                    line_number=line_no,
                    snippet=snippet,
                )
            )

    return anchors, publishers_by_address, consumers_by_address

def _strip_inline_comments(line: str, *, in_block_comment: bool) -> tuple[str, bool]:
    text = line
    if in_block_comment:
        end = text.find("*/")
        if end == -1:
            return "", True
        text = text[end + 2 :]
        in_block_comment = False

    while "/*" in text:
        start = text.find("/*")
        end = text.find("*/", start + 2)
        if end == -1:
            return text[:start], True
        text = text[:start] + text[end + 2 :]

    if "//" in text:
        text = text.split("//", 1)[0]
    return text, in_block_comment


def _parse_signature(signature: str) -> tuple[str, str | None, tuple[str, ...], bool, bool] | None:
    normalized = " ".join(signature.replace("\n", " ").split())
    match = re.search(
        r"\b(?P<kind>class|interface)\s+"
        r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
        r"(?:\s+extends\s+(?P<extends>[A-Za-z0-9_$.<>]+))?"
        r"(?:\s+implements\s+(?P<implements>[A-Za-z0-9_$.<>\s,]+))?\s*\{",
        normalized,
    )
    if not match:
        return None
    kind = match.group("kind")
    class_name = match.group("name")
    extends_name = _simple_type_name(match.group("extends"))
    implements_value = match.group("implements") or ""
    implements = tuple(
        candidate
        for candidate in (_simple_type_name(part) for part in implements_value.split(","))
        if candidate
    )
    is_interface = kind == "interface"
    is_abstract = is_interface or " abstract " in f" {normalized} "
    return class_name, extends_name, implements, is_abstract, is_interface


def _parse_file_fallback(path: Path, source: str) -> list[JavaClassRecord]:
    package_name, imports = _extract_imports(source)
    records: list[JavaClassRecord] = []
    brace_depth = 0
    in_block_comment = False
    signature_parts: list[str] = []
    signature_depth = 0

    for raw_line in source.splitlines():
        line, in_block_comment = _strip_inline_comments(raw_line, in_block_comment=in_block_comment)
        if not line.strip():
            continue

        if not signature_parts and brace_depth == 0 and (" class " in f" {line} " or " interface " in f" {line} "):
            signature_parts = [line.strip()]
            signature_depth = brace_depth
            if "{" not in line:
                brace_depth += line.count("{") - line.count("}")
                continue
        elif signature_parts:
            signature_parts.append(line.strip())

        if signature_parts and "{" in line:
            parsed = _parse_signature(" ".join(signature_parts))
            if parsed and signature_depth == 0:
                class_name, extends_name, implements, is_abstract, is_interface = parsed
                qualified_name = f"{package_name}.{class_name}" if package_name else class_name
                records.append(
                    JavaClassRecord(
                        class_name=class_name,
                        qualified_name=qualified_name,
                        package=package_name,
                        top_package=_top_package(package_name),
                        extends=extends_name,
                        implements=implements,
                        is_abstract=is_abstract,
                        is_interface=is_interface,
                        file_path=str(path.resolve()),
                        imports=imports,
                    )
                )
            signature_parts = []

        brace_depth += line.count("{") - line.count("}")

    return records


def _parse_file(path: Path) -> list[JavaClassRecord]:
    source = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = javalang.parse.parse(source)
    except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError, TypeError, ValueError):
        fallback_records = _parse_file_fallback(path, source)
        if fallback_records:
            return fallback_records
        raise
    package_name = tree.package.name if tree.package else ""
    imports = tuple(imp.path for imp in (tree.imports or []) if getattr(imp, "path", None))

    records: list[JavaClassRecord] = []
    for type_decl in tree.types:
        is_interface = isinstance(type_decl, javalang.tree.InterfaceDeclaration)
        is_class = isinstance(type_decl, javalang.tree.ClassDeclaration)
        if not is_interface and not is_class:
            continue
        simple_name = type_decl.name
        qualified_name = f"{package_name}.{simple_name}" if package_name else simple_name
        extends_name = None
        implements: tuple[str, ...] = ()
        if is_class:
            extends_name = _type_name(type_decl.extends)
            implements = tuple(
                candidate
                for candidate in (_type_name(item) for item in (type_decl.implements or []))
                if candidate
            )
        else:
            extends_name = _type_name(type_decl.extends)
        modifiers = set(type_decl.modifiers or [])
        records.append(
            JavaClassRecord(
                class_name=simple_name,
                qualified_name=qualified_name,
                package=package_name,
                top_package=_top_package(package_name),
                extends=extends_name,
                implements=implements,
                is_abstract=("abstract" in modifiers) or is_interface,
                is_interface=is_interface,
                file_path=str(path.resolve()),
                imports=imports,
            )
        )
    return records


def _resolve_parent_name(
    parent_name: str | None,
    record: JavaClassRecord,
    by_qualified_name: dict[str, JavaClassRecord],
    by_simple_name: dict[str, list[JavaClassRecord]],
) -> str | None:
    if not parent_name:
        return None
    if parent_name in by_qualified_name:
        return parent_name
    imported_match = next(
        (
            import_path
            for import_path in record.imports
            if import_path.endswith(f".{parent_name}") and import_path in by_qualified_name
        ),
        None,
    )
    if imported_match:
        return imported_match
    package_match = f"{record.package}.{parent_name}" if record.package else parent_name
    if package_match in by_qualified_name:
        return package_match
    candidates = by_simple_name.get(parent_name, [])
    if len(candidates) == 1:
        return candidates[0].qualified_name
    return None


def _load_schema(driver) -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    statements = [part.strip() for part in schema.split(";") if part.strip()]
    with driver.session() as session:
        for statement in statements:
            session.run(statement).consume()


def _workspace_fingerprint(files: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in files:
        stat = path.stat()
        digest.update(str(path).encode("utf-8", errors="replace"))
        digest.update(str(stat.st_size).encode("utf-8"))
        digest.update(str(stat.st_mtime_ns).encode("utf-8"))
    return digest.hexdigest()


def _reset_graph(session) -> None:
    session.run("MATCH (n:GraphIngestState) DETACH DELETE n").consume()
    session.run("MATCH (n:GraphIngestMetric) DETACH DELETE n").consume()
    session.run("MATCH (n:Class) DETACH DELETE n").consume()
    session.run("MATCH (n:Package) DETACH DELETE n").consume()
    session.run("MATCH (n:Anchor) DETACH DELETE n").consume()
    session.run("MATCH (n:EventBusAddress) DETACH DELETE n").consume()
    session.run("MATCH (n:EventBusAddressConstant) DETACH DELETE n").consume()


def _upsert_graph(
    driver,
    records: list[JavaClassRecord],
    resolved_extends: dict[str, str],
    resolved_implements: dict[str, tuple[str, ...]],
    anchors: list[AnchorRecord],
    eventbus_constants: list[EventBusAddressConstant],
    publishes_eventbus_rows: list[dict[str, str]],
    consumes_eventbus_rows: list[dict[str, str]],
    publish_consume_rows: list[dict[str, str]],
    *,
    reset: bool,
    ingest_state: dict[str, Any],
    metric_rows: list[dict[str, Any]],
) -> None:
    class_rows = [
        {
            "name": record.class_name,
            "qualifiedName": record.qualified_name,
            "package": record.package,
            "topPackage": record.top_package,
            "isAbstract": record.is_abstract,
            "isInterface": record.is_interface,
            "filePath": record.file_path,
        }
        for record in records
    ]
    package_rows = [
        {"name": record.package, "topPackage": record.top_package}
        for record in records
        if record.package
    ]
    extends_rows = [
        {
            "child": child_qn,
            "parent": parent_qn,
            "simple_name": parent_qn.rsplit(".", 1)[-1],
        }
        for child_qn, parent_qn in resolved_extends.items()
    ]
    implements_rows = [
        {
            "child": child_qn,
            "parent": parent_qn,
            "simple_name": parent_qn.rsplit(".", 1)[-1],
        }
        for child_qn, parents in resolved_implements.items()
        for parent_qn in parents
    ]
    anchor_rows = [
        {
            "anchorId": anchor.anchor_id,
            "category": anchor.category,
            "classQualifiedName": anchor.class_qualified_name,
            "filePath": anchor.file_path,
            "lineNumber": anchor.line_number,
            "snippet": anchor.snippet,
            "addressValue": anchor.address_value,
            "addressToken": anchor.address_token,
            "addressConstantKey": anchor.address_constant_key,
        }
        for anchor in anchors
    ]
    eventbus_address_rows = sorted(
        {row["address"] for row in publishes_eventbus_rows + consumes_eventbus_rows if row.get("address")}
        | {item.value for item in eventbus_constants}
    )
    eventbus_constant_rows = [
        {
            "key": item.key,
            "value": item.value,
            "classQualifiedName": item.class_qualified_name,
            "className": item.class_name,
            "fieldName": item.field_name,
            "filePath": item.file_path,
        }
        for item in eventbus_constants
    ]

    with driver.session() as session:
        if reset:
            _reset_graph(session)
        session.run(
            """
            UNWIND $rows AS row
            MERGE (c:Class {qualifiedName: row.qualifiedName})
            SET c.name = row.name,
                c.package = row.package,
                c.topPackage = row.topPackage,
                c.isAbstract = row.isAbstract,
                c.isInterface = row.isInterface,
                c.filePath = row.filePath
            """,
            rows=class_rows,
        ).consume()
        session.run(
            """
            UNWIND $rows AS row
            MERGE (p:Package {name: row.name})
            SET p.topPackage = row.topPackage
            """,
            rows=package_rows,
        ).consume()
        session.run(
            """
            UNWIND $rows AS row
            MATCH (c:Class {qualifiedName: row.qualifiedName})
            MATCH (p:Package {name: row.package})
            MERGE (c)-[:IN_PACKAGE]->(p)
            """,
            rows=class_rows,
        ).consume()
        session.run(
            """
            UNWIND $rows AS row
            MATCH (child:Class {qualifiedName: row.child})
            MATCH (parent:Class {qualifiedName: row.parent})
            MERGE (child)-[rel:EXTENDS]->(parent)
            SET rel.simple_name = row.simple_name
            """,
            rows=extends_rows,
        ).consume()
        session.run(
            """
            UNWIND $rows AS row
            MATCH (child:Class {qualifiedName: row.child})
            MATCH (parent:Class {qualifiedName: row.parent})
            MERGE (child)-[rel:IMPLEMENTS]->(parent)
            SET rel.simple_name = row.simple_name
            """,
            rows=implements_rows,
        ).consume()
        session.run(
            """
            UNWIND $rows AS row
            MERGE (a:Anchor {anchorId: row.anchorId})
            SET a.category = row.category,
                a.filePath = row.filePath,
                a.lineNumber = row.lineNumber,
                a.snippet = row.snippet,
                a.addressValue = row.addressValue,
                a.addressToken = row.addressToken,
                a.addressConstantKey = row.addressConstantKey
            WITH row, a
            MATCH (c:Class {qualifiedName: row.classQualifiedName})
            MERGE (c)-[:HAS_ANCHOR]->(a)
            """,
            rows=anchor_rows,
        ).consume()
        session.run(
            """
            UNWIND $rows AS value
            MERGE (:EventBusAddress {value: value})
            """,
            rows=eventbus_address_rows,
        ).consume()
        session.run(
            """
            UNWIND $rows AS row
            MERGE (k:EventBusAddressConstant {key: row.key})
            SET k.value = row.value,
                k.classQualifiedName = row.classQualifiedName,
                k.className = row.className,
                k.fieldName = row.fieldName,
                k.filePath = row.filePath
            WITH row, k
            MERGE (addr:EventBusAddress {value: row.value})
            MERGE (k)-[:RESOLVES_TO]->(addr)
            """,
            rows=eventbus_constant_rows,
        ).consume()
        session.run(
            """
            UNWIND $rows AS row
            MATCH (c:Class {qualifiedName: row.publisher})
            MATCH (addr:EventBusAddress {value: row.address})
            MERGE (c)-[:PUBLISHES_EVENTBUS]->(addr)
            """,
            rows=publishes_eventbus_rows,
        ).consume()
        session.run(
            """
            UNWIND $rows AS row
            MATCH (c:Class {qualifiedName: row.consumer})
            MATCH (addr:EventBusAddress {value: row.address})
            MERGE (c)-[:CONSUMES_EVENTBUS]->(addr)
            """,
            rows=consumes_eventbus_rows,
        ).consume()
        session.run(
            """
            UNWIND $rows AS row
            MATCH (publisher:Class {qualifiedName: row.publisher})
            MATCH (consumer:Class {qualifiedName: row.consumer})
            MERGE (publisher)-[rel:PUBLISHES_TO_CONSUMER {address: row.address}]->(consumer)
            """,
            rows=publish_consume_rows,
        ).consume()
        session.run(
            """
            MERGE (state:GraphIngestState {key: $key})
            SET state.updatedAt = datetime(),
                state.javaRoot = $javaRoot,
                state.workspaceFingerprint = $workspaceFingerprint,
                state.javaFileCount = $javaFileCount,
                state.classRecordCount = $classRecordCount,
                state.packageCount = $packageCount,
                state.extendsEdgeCount = $extendsEdgeCount,
                state.implementsEdgeCount = $implementsEdgeCount,
                state.anchorCount = $anchorCount,
                state.eventbusAddressCount = $eventbusAddressCount,
                state.eventbusAddressConstantCount = $eventbusAddressConstantCount,
                state.publishesEventbusEdgeCount = $publishesEventbusEdgeCount,
                state.consumesEventbusEdgeCount = $consumesEventbusEdgeCount,
                state.publishesToConsumerEdgeCount = $publishesToConsumerEdgeCount,
                state.anchorCountVerticleRegistration = $anchorCountVerticleRegistration,
                state.anchorCountApiRouteRegistration = $anchorCountApiRouteRegistration,
                state.anchorCountEventbusConsumerRegistration = $anchorCountEventbusConsumerRegistration,
                state.anchorCountEventbusPublishAnchor = $anchorCountEventbusPublishAnchor,
                state.anchorCountIntegrationRegistration = $anchorCountIntegrationRegistration,
                state.anchorCountConfigAccessAnchor = $anchorCountConfigAccessAnchor,
                state.eventbusAddressConstantKeys = $eventbusAddressConstantKeys,
                state.parseErrorCount = $parseErrorCount,
                state.missingParentCount = $missingParentCount
            """,
            **ingest_state,
        ).consume()
        session.run(
            """
            UNWIND $rows AS row
            MERGE (metric:GraphIngestMetric {metricKey: row.metricKey})
            SET metric.stateKey = row.stateKey,
                metric.metricType = row.metricType,
                metric.metricName = row.metricName,
                metric.count = row.count,
                metric.updatedAt = datetime()
            """,
            rows=metric_rows,
        ).consume()


def _build_metric_rows(
    *,
    state_key: str,
    anchor_counts: dict[str, int],
    edge_type_counts: dict[str, int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for category in sorted(anchor_counts):
        rows.append(
            {
                "metricKey": f"{state_key}:anchor:{category}",
                "stateKey": state_key,
                "metricType": "ANCHOR_CATEGORY",
                "metricName": category,
                "count": int(anchor_counts[category]),
            }
        )
    for edge_type in sorted(edge_type_counts):
        rows.append(
            {
                "metricKey": f"{state_key}:edge:{edge_type}",
                "stateKey": state_key,
                "metricType": "EDGE_TYPE",
                "metricName": edge_type,
                "count": int(edge_type_counts[edge_type]),
            }
        )
    return rows


def extract_eventbus_address_constants(java_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in _iter_java_files(java_root):
        source = path.read_text(encoding="utf-8", errors="replace")
        for constant in _extract_eventbus_constants(source, str(path.resolve())):
            rows.append(
                {
                    "key": constant.key,
                    "value": constant.value,
                    "class_qualified_name": constant.class_qualified_name,
                    "field_name": constant.field_name,
                    "file_path": constant.file_path,
                }
            )
    rows.sort(key=lambda item: item["key"])
    return rows


def ingest(java_root: Path, *, reset: bool = False) -> dict[str, Any]:
    parse_errors: list[str] = []
    missing_parents: set[str] = set()
    records: list[JavaClassRecord] = []
    files = list(_iter_java_files(java_root))
    file_sources: dict[str, str] = {}
    records_by_file: dict[str, list[JavaClassRecord]] = {}
    all_eventbus_constants: list[EventBusAddressConstant] = []

    for index, path in enumerate(files, start=1):
        source = path.read_text(encoding="utf-8", errors="replace")
        file_path = str(path.resolve())
        file_sources[file_path] = source
        try:
            file_records = _parse_file(path)
            records.extend(file_records)
            records_by_file[file_path] = file_records
        except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError, TypeError, ValueError) as exc:
            parse_errors.append(f"{path}: {exc}")
            records_by_file[file_path] = []
        all_eventbus_constants.extend(_extract_eventbus_constants(source, file_path))
        if index % PROGRESS_EVERY == 0:
            LOG.info("parsed %s/%s Java files", index, len(files))

    by_qualified_name = {record.qualified_name: record for record in records}
    by_simple_name: dict[str, list[JavaClassRecord]] = {}
    for record in records:
        by_simple_name.setdefault(record.class_name, []).append(record)

    resolved_extends: dict[str, str] = {}
    resolved_implements: dict[str, tuple[str, ...]] = {}
    for record in records:
        parent_qn = _resolve_parent_name(record.extends, record, by_qualified_name, by_simple_name)
        if record.extends and not parent_qn:
            missing_parents.add(record.extends)
        if parent_qn:
            resolved_extends[record.qualified_name] = parent_qn

        interface_qns: list[str] = []
        for interface_name in record.implements:
            interface_qn = _resolve_parent_name(interface_name, record, by_qualified_name, by_simple_name)
            if interface_qn:
                interface_qns.append(interface_qn)
            else:
                missing_parents.add(interface_name)
        if interface_qns:
            resolved_implements[record.qualified_name] = tuple(interface_qns)

    by_key, by_ref, unique_by_field = _build_eventbus_indexes(all_eventbus_constants)
    anchors: list[AnchorRecord] = []
    publishers_by_address: dict[str, set[str]] = {}
    consumers_by_address: dict[str, set[str]] = {}
    for file_path, source in file_sources.items():
        file_anchors, file_publishers, file_consumers = _extract_file_anchors(
            source=source,
            file_path=file_path,
            file_records=records_by_file.get(file_path, []),
            by_key=by_key,
            by_ref=by_ref,
            unique_by_field=unique_by_field,
        )
        anchors.extend(file_anchors)
        for address, owners in file_publishers.items():
            publishers_by_address.setdefault(address, set()).update(owners)
        for address, owners in file_consumers.items():
            consumers_by_address.setdefault(address, set()).update(owners)

    publishes_eventbus_rows = sorted(
        (
            {"publisher": publisher, "address": address}
            for address, publishers in publishers_by_address.items()
            for publisher in publishers
        ),
        key=lambda item: (item["publisher"], item["address"]),
    )
    consumes_eventbus_rows = sorted(
        (
            {"consumer": consumer, "address": address}
            for address, consumers in consumers_by_address.items()
            for consumer in consumers
        ),
        key=lambda item: (item["consumer"], item["address"]),
    )
    publish_consume_rows = sorted(
        (
            {"publisher": publisher, "consumer": consumer, "address": address}
            for address, publishers in publishers_by_address.items()
            for publisher in publishers
            for consumer in consumers_by_address.get(address, set())
        ),
        key=lambda item: (item["publisher"], item["consumer"], item["address"]),
    )

    anchor_counts = {category: 0 for category in ANCHOR_CATEGORIES}
    for anchor in anchors:
        anchor_counts[anchor.category] = anchor_counts.get(anchor.category, 0) + 1
    edge_type_counts = {
        "IN_PACKAGE": len(records),
        "EXTENDS": len(resolved_extends),
        "IMPLEMENTS": sum(len(value) for value in resolved_implements.values()),
        "HAS_ANCHOR": len(anchors),
        "PUBLISHES_EVENTBUS": len(publishes_eventbus_rows),
        "CONSUMES_EVENTBUS": len(consumes_eventbus_rows),
        "PUBLISHES_TO_CONSUMER": len(publish_consume_rows),
        "EVENTBUS_CONSTANT_RESOLVES_TO": len(all_eventbus_constants),
    }
    metric_rows = _build_metric_rows(
        state_key="java_ast",
        anchor_counts=anchor_counts,
        edge_type_counts=edge_type_counts,
    )

    uri, user, password = _neo4j_settings()
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    _load_schema(driver)
    summary = {
        "java_files": len(files),
        "class_records": len(records),
        "package_count": len({record.package for record in records if record.package}),
        "extends_edges": len(resolved_extends),
        "implements_edges": edge_type_counts["IMPLEMENTS"],
        "anchor_counts": anchor_counts,
        "edge_type_counts": edge_type_counts,
        "eventbus_address_count": len({item.value for item in all_eventbus_constants} | set(publishers_by_address) | set(consumers_by_address)),
        "eventbus_address_constant_count": len(all_eventbus_constants),
        "eventbus_address_constants": [item.key for item in sorted(all_eventbus_constants, key=lambda row: row.key)],
        "parse_errors": parse_errors,
        "missing_parent_count": len(missing_parents),
        "workspace_fingerprint": _workspace_fingerprint(files),
        "java_root": str(java_root),
        "reset_applied": reset,
    }
    _upsert_graph(
        driver,
        records,
        resolved_extends,
        resolved_implements,
        anchors,
        all_eventbus_constants,
        publishes_eventbus_rows,
        consumes_eventbus_rows,
        publish_consume_rows,
        reset=reset,
        ingest_state={
            "key": "java_ast",
            "javaRoot": summary["java_root"],
            "workspaceFingerprint": summary["workspace_fingerprint"],
            "javaFileCount": summary["java_files"],
            "classRecordCount": summary["class_records"],
            "packageCount": summary["package_count"],
            "extendsEdgeCount": summary["extends_edges"],
            "implementsEdgeCount": summary["implements_edges"],
            "anchorCount": len(anchors),
            "eventbusAddressCount": summary["eventbus_address_count"],
            "eventbusAddressConstantCount": summary["eventbus_address_constant_count"],
            "publishesEventbusEdgeCount": edge_type_counts["PUBLISHES_EVENTBUS"],
            "consumesEventbusEdgeCount": edge_type_counts["CONSUMES_EVENTBUS"],
            "publishesToConsumerEdgeCount": edge_type_counts["PUBLISHES_TO_CONSUMER"],
            "anchorCountVerticleRegistration": anchor_counts.get("VERTICLE_REGISTRATION", 0),
            "anchorCountApiRouteRegistration": anchor_counts.get("API_ROUTE_REGISTRATION", 0),
            "anchorCountEventbusConsumerRegistration": anchor_counts.get("EVENTBUS_CONSUMER_REGISTRATION", 0),
            "anchorCountEventbusPublishAnchor": anchor_counts.get("EVENTBUS_PUBLISH_ANCHOR", 0),
            "anchorCountIntegrationRegistration": anchor_counts.get("INTEGRATION_REGISTRATION", 0),
            "anchorCountConfigAccessAnchor": anchor_counts.get("CONFIG_ACCESS_ANCHOR", 0),
            "eventbusAddressConstantKeys": summary["eventbus_address_constants"],
            "parseErrorCount": len(parse_errors),
            "missingParentCount": summary["missing_parent_count"],
        },
        metric_rows=metric_rows,
    )
    driver.close()

    for parent_name in sorted(missing_parents):
        LOG.warning("skipping unresolved parent outside workspace: %s", parent_name)

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Index Java inheritance and package structure into Neo4j.")
    parser.add_argument(
        "--java-root",
        default=os.environ.get(DEFAULT_JAVA_ROOT_ENV, ""),
        help="Root directory containing Java sources (defaults to MOTADATA_JAVA_ROOT).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete previously indexed Class/Package nodes before ingesting the current snapshot.",
    )
    parser.add_argument(
        "--list-eventbus-address-constants",
        action="store_true",
        help="Print stable extracted EventBus address constants as JSON and exit.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s %(message)s")
    java_root = Path(args.java_root).expanduser().resolve() if args.java_root else None
    if java_root is None or not java_root.exists() or not java_root.is_dir():
        raise SystemExit("A valid --java-root or MOTADATA_JAVA_ROOT is required")

    if args.list_eventbus_address_constants:
        print(json.dumps(extract_eventbus_address_constants(java_root), indent=2, sort_keys=True))
        return 0

    summary = ingest(java_root, reset=args.reset)
    LOG.info("ingest summary: %s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())