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
    session.run("MATCH (n:Class) DETACH DELETE n").consume()
    session.run("MATCH (n:Package) DETACH DELETE n").consume()


def _upsert_graph(
    driver,
    records: list[JavaClassRecord],
    resolved_extends: dict[str, str],
    resolved_implements: dict[str, tuple[str, ...]],
    *,
    reset: bool,
    ingest_state: dict[str, Any],
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
            MERGE (state:GraphIngestState {key: $key})
            SET state.updatedAt = datetime(),
                state.javaRoot = $javaRoot,
                state.workspaceFingerprint = $workspaceFingerprint,
                state.javaFileCount = $javaFileCount,
                state.classRecordCount = $classRecordCount,
                state.packageCount = $packageCount,
                state.extendsEdgeCount = $extendsEdgeCount,
                state.implementsEdgeCount = $implementsEdgeCount,
                state.parseErrorCount = $parseErrorCount,
                state.missingParentCount = $missingParentCount
            """,
            **ingest_state,
        ).consume()


def ingest(java_root: Path, *, reset: bool = False) -> dict[str, Any]:
    parse_errors: list[str] = []
    missing_parents: set[str] = set()
    records: list[JavaClassRecord] = []
    files = list(_iter_java_files(java_root))

    for index, path in enumerate(files, start=1):
        try:
            records.extend(_parse_file(path))
        except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError, TypeError, ValueError) as exc:
            parse_errors.append(f"{path}: {exc}")
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

    uri, user, password = _neo4j_settings()
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    _load_schema(driver)
    summary = {
        "java_files": len(files),
        "class_records": len(records),
        "package_count": len({record.package for record in records if record.package}),
        "extends_edges": len(resolved_extends),
        "implements_edges": sum(len(value) for value in resolved_implements.values()),
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
            "parseErrorCount": len(parse_errors),
            "missingParentCount": summary["missing_parent_count"],
        },
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
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s %(message)s")
    java_root = Path(args.java_root).expanduser().resolve() if args.java_root else None
    if java_root is None or not java_root.exists() or not java_root.is_dir():
        raise SystemExit("A valid --java-root or MOTADATA_JAVA_ROOT is required")

    summary = ingest(java_root, reset=args.reset)
    LOG.info("ingest summary: %s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())