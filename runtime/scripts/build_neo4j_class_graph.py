#!/usr/bin/env python3
"""
Build a minimal class-relationship graph for Ask Neo4j resolution.

This script intentionally indexes only class inheritance/implementation edges:
  - (:Class)-[:EXTENDS]->(:Class)
  - (:Class)-[:IMPLEMENTS]->(:Class)
"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Tuple

from runtime.neo4j_credentials import neo4j_password_from_env


PACKAGE_RE = re.compile(r"^\s*package\s+([A-Za-z_][\w\.]*)\s*;", re.MULTILINE)
CLASS_RE = re.compile(
    r"\bclass\s+([A-Za-z_]\w*)"
    r"(?:\s+extends\s+([A-Za-z_][A-Za-z0-9_\.]*))?"
    r"(?:\s+implements\s+([A-Za-z_][A-Za-z0-9_\.,\s]*))?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ClassRecord:
    name: str
    package: str
    file_path: str
    extends: str | None
    implements: Tuple[str, ...]

    @property
    def fqn(self) -> str:
        return f"{self.package}.{self.name}" if self.package else self.name


def _discover_java_files(root: Path, source_dirs: Iterable[str], max_files: int) -> List[Path]:
    files: List[Path] = []
    for src in source_dirs:
        src_root = (root / src).resolve()
        if not src_root.exists():
            continue
        for p in sorted(src_root.rglob("*.java")):
            files.append(p)
            if len(files) >= max_files:
                return files
    return files


def _parse_java_file(java_file: Path, workspace_root: Path) -> Iterator[ClassRecord]:
    text = java_file.read_text(encoding="utf-8", errors="replace")
    package_match = PACKAGE_RE.search(text)
    package = package_match.group(1).strip() if package_match else ""
    rel_path = str(java_file.relative_to(workspace_root)).replace("\\", "/")
    for m in CLASS_RE.finditer(text):
        cls = (m.group(1) or "").strip()
        parent = (m.group(2) or "").strip() or None
        impl_raw = (m.group(3) or "").strip()
        interfaces = tuple(x.strip() for x in impl_raw.split(",") if x.strip())
        if not cls:
            continue
        yield ClassRecord(
            name=cls,
            package=package,
            file_path=rel_path,
            extends=parent,
            implements=interfaces,
        )


def _resolve_target_fqn(symbol: str, package: str, class_by_name: Dict[str, str]) -> str:
    raw = (symbol or "").strip()
    if not raw:
        return ""
    clean = raw.split("<", 1)[0].strip()
    if "." in clean:
        return clean
    if clean in class_by_name:
        return class_by_name[clean]
    return f"{package}.{clean}" if package else clean


def _cypher_bootstrap(session) -> None:
    session.run("CREATE CONSTRAINT class_fqn_unique IF NOT EXISTS FOR (c:Class) REQUIRE c.fqn IS UNIQUE")
    session.run("CREATE INDEX class_name_idx IF NOT EXISTS FOR (c:Class) ON (c.name)")
    session.run("CREATE INDEX class_package_idx IF NOT EXISTS FOR (c:Class) ON (c.package)")


def _upsert_graph(session, records: List[ClassRecord], clear_existing: bool) -> None:
    if clear_existing:
        session.run("MATCH (n:Class) DETACH DELETE n")
    _cypher_bootstrap(session)
    class_by_name = {r.name: r.fqn for r in records}
    for rec in records:
        session.run(
            "MERGE (c:Class {fqn: $fqn}) "
            "SET c.name = $name, c.package = $package, c.file = $file",
            fqn=rec.fqn,
            name=rec.name,
            package=rec.package,
            file=rec.file_path,
        )
        if rec.extends:
            parent_fqn = _resolve_target_fqn(rec.extends, rec.package, class_by_name)
            if parent_fqn:
                session.run(
                    "MERGE (p:Class {fqn: $parent_fqn}) "
                    "ON CREATE SET p.name = $parent_name, p.package = $parent_package "
                    "WITH p "
                    "MATCH (c:Class {fqn: $child_fqn}) "
                    "MERGE (c)-[:EXTENDS]->(p)",
                    parent_fqn=parent_fqn,
                    parent_name=parent_fqn.rsplit(".", 1)[-1],
                    parent_package=parent_fqn.rsplit(".", 1)[0] if "." in parent_fqn else "",
                    child_fqn=rec.fqn,
                )
        for interface_name in rec.implements:
            interface_fqn = _resolve_target_fqn(interface_name, rec.package, class_by_name)
            if not interface_fqn:
                continue
            session.run(
                "MERGE (i:Class {fqn: $interface_fqn}) "
                "ON CREATE SET i.name = $interface_name, i.package = $interface_package "
                "WITH i "
                "MATCH (c:Class {fqn: $child_fqn}) "
                "MERGE (c)-[:IMPLEMENTS]->(i)",
                interface_fqn=interface_fqn,
                interface_name=interface_fqn.rsplit(".", 1)[-1],
                interface_package=interface_fqn.rsplit(".", 1)[0] if "." in interface_fqn else "",
                child_fqn=rec.fqn,
            )


def _default_source_dirs(workspace_root: Path) -> List[str]:
    candidates = [
        "motadata/src/main/java",
        "src/main/java",
        "src",
    ]
    found = [c for c in candidates if (workspace_root / c).exists()]
    return found or ["."]


def index_class_graph(
    *,
    workspace_root: Path,
    source_dirs: List[str] | None = None,
    max_files: int = 100000,
    neo4j_uri: str = "",
    neo4j_user: str = "",
    neo4j_password: str = "",
    clear_existing: bool = False,
) -> Dict[str, Any]:
    """
    Index class inheritance/implementation graph into Neo4j and return summary stats.
    """
    if not workspace_root.exists() or not workspace_root.is_dir():
        raise ValueError(f"workspace root not found or not a directory: {workspace_root}")

    try:
        from neo4j import GraphDatabase  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "neo4j driver unavailable; install with `pip install neo4j` before indexing."
        ) from exc

    effective_sources = [str(x).strip() for x in (source_dirs or []) if str(x).strip()] or _default_source_dirs(
        workspace_root
    )
    java_files = _discover_java_files(workspace_root, effective_sources, max(1, int(max_files)))
    records: List[ClassRecord] = []
    for p in java_files:
        records.extend(_parse_java_file(p, workspace_root))

    uri = neo4j_uri.strip() or str(os.environ.get("MOTADATA_NEO4J_URI", "")).strip()
    user = neo4j_user.strip() or str(os.environ.get("MOTADATA_NEO4J_USER", "")).strip()
    password = neo4j_password.strip() or neo4j_password_from_env()
    if not uri:
        raise ValueError("missing Neo4j URI (set --neo4j-uri or MOTADATA_NEO4J_URI)")

    auth = (user, password) if user or password else None
    driver = GraphDatabase.driver(uri, auth=auth)
    try:
        with driver.session() as session:
            _upsert_graph(session, records, clear_existing=bool(clear_existing))
            rel_counts = session.run(
                "MATCH (c:Class) "
                "OPTIONAL MATCH (c)-[e:EXTENDS]->() "
                "OPTIONAL MATCH (c)-[i:IMPLEMENTS]->() "
                "RETURN count(DISTINCT c) AS classes, count(DISTINCT e) AS extends_edges, count(DISTINCT i) AS implements_edges"
            ).single()
    finally:
        driver.close()
    rel_counts = rel_counts or {}
    return {
        "files": len(java_files),
        "parsed_classes": len(records),
        "graph_classes": int(rel_counts.get("classes") or 0),
        "extends_edges": int(rel_counts.get("extends_edges") or 0),
        "implements_edges": int(rel_counts.get("implements_edges") or 0),
        "source_dirs": effective_sources,
        "workspace_root": str(workspace_root),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Index Java class relationships into Neo4j.")
    parser.add_argument("--workspace-root", required=True, help="Workspace root path.")
    parser.add_argument(
        "--source-dir",
        action="append",
        default=[],
        help="Source directory relative to workspace root (repeatable).",
    )
    parser.add_argument("--max-files", type=int, default=100000, help="Hard cap on processed Java files.")
    parser.add_argument("--neo4j-uri", default="", help="Neo4j bolt URI; defaults to MOTADATA_NEO4J_URI.")
    parser.add_argument("--neo4j-user", default="", help="Neo4j user; defaults to MOTADATA_NEO4J_USER.")
    parser.add_argument(
        "--neo4j-password",
        default="",
        help="Neo4j password; defaults to MOTADATA_NEO4J_PASSWORD.",
    )
    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Delete existing Class nodes before insert.",
    )
    args = parser.parse_args()

    workspace_root = Path(args.workspace_root).expanduser().resolve()
    try:
        stats = index_class_graph(
            workspace_root=workspace_root,
            source_dirs=[str(x).strip() for x in (args.source_dir or []) if str(x).strip()],
            max_files=max(1, int(args.max_files)),
            neo4j_uri=args.neo4j_uri,
            neo4j_user=args.neo4j_user,
            neo4j_password=args.neo4j_password,
            clear_existing=bool(args.clear_existing),
        )
    except Exception as exc:
        raise SystemExit(str(exc)) from exc

    print(
        "neo4j_class_graph_indexed "
        f"files={stats['files']} classes={stats['parsed_classes']} "
        f"graph_classes={stats['graph_classes']} "
        f"extends_edges={stats['extends_edges']} "
        f"implements_edges={stats['implements_edges']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

