"""Neo4j-backed structural queries over the Java AST graph."""

from __future__ import annotations

import logging
import os
from time import perf_counter
from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError


LOG = logging.getLogger(__name__)


def _neo4j_settings() -> tuple[str, str, str | None]:
    return (
        os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7687"),
        os.environ.get("NEO4J_USER", "neo4j"),
        os.environ.get("NEO4J_PASSWORD"),
    )


def _driver():
    uri, user, password = _neo4j_settings()
    if not password:
        raise RuntimeError("NEO4J_PASSWORD is required")
    return GraphDatabase.driver(uri, auth=(user, password))


def _class_record_to_dict(record: Any) -> dict[str, Any]:
    return {
        "name": record.get("name"),
        "qualified_name": record.get("qualified_name"),
        "package": record.get("package"),
        "top_package": record.get("top_package"),
        "is_abstract": bool(record.get("is_abstract")),
        "is_interface": bool(record.get("is_interface")),
        "file_path": record.get("file_path"),
        "extends": record.get("extends"),
        "implements": record.get("implements") or [],
    }


def find_base_class(top_package: str) -> dict[str, Any] | None:
    """Return the most likely abstract root for a top-level package."""
    query = """
    MATCH (candidate:Class {topPackage: $top_package})
    WHERE candidate.isAbstract = true
    OPTIONAL MATCH (child:Class {topPackage: $top_package})-[:EXTENDS*1..]->(candidate)
    WITH candidate,
         count(DISTINCT child) AS descendant_count,
         CASE WHEN candidate.name STARTS WITH 'Abstract' THEN 1 ELSE 0 END AS named_root_score,
         CASE WHEN candidate.package = $preferred_package THEN 1 ELSE 0 END AS package_score
    ORDER BY descendant_count DESC, named_root_score DESC, package_score DESC, candidate.qualifiedName ASC
    LIMIT 1
    OPTIONAL MATCH (candidate)-[ext:EXTENDS]->(parent:Class)
    OPTIONAL MATCH (candidate)-[impl:IMPLEMENTS]->(iface:Class)
    RETURN candidate.name AS name,
           candidate.qualifiedName AS qualified_name,
           candidate.package AS package,
           candidate.topPackage AS top_package,
           candidate.isAbstract AS is_abstract,
           candidate.isInterface AS is_interface,
           candidate.filePath AS file_path,
           parent.qualifiedName AS extends,
           collect(DISTINCT iface.qualifiedName) AS implements,
           descendant_count AS descendant_count
    """
    preferred_package = f"com.mindarray.{top_package.strip().lower()}"
    try:
        with _driver() as driver, driver.session() as session:
            record = session.run(
                query,
                top_package=top_package.strip().lower(),
                preferred_package=preferred_package,
            ).single()
    except (RuntimeError, Neo4jError) as exc:
        LOG.warning("find_base_class failed for %s: %s", top_package, exc)
        return None
    if record is None or record.get("qualified_name") is None:
        return None
    payload = _class_record_to_dict(record)
    payload["descendant_count"] = int(record.get("descendant_count") or 0)
    return payload


def find_implementors(interface_name: str, limit: int = 25) -> list[dict[str, Any]]:
    query = """
    MATCH (iface:Class)
    WHERE iface.qualifiedName = $name OR iface.name = $name
    MATCH (impl:Class)-[:IMPLEMENTS|EXTENDS*1..]->(iface)
    OPTIONAL MATCH (impl)-[:EXTENDS]->(parent:Class)
    RETURN DISTINCT impl.name AS name,
           impl.qualifiedName AS qualified_name,
           impl.package AS package,
           impl.topPackage AS top_package,
           impl.isAbstract AS is_abstract,
           impl.isInterface AS is_interface,
           impl.filePath AS file_path,
           parent.qualifiedName AS extends,
           [] AS implements
    ORDER BY impl.qualifiedName ASC
    LIMIT $limit
    """
    try:
        with _driver() as driver, driver.session() as session:
            return [_class_record_to_dict(record) for record in session.run(query, name=interface_name, limit=limit)]
    except (RuntimeError, Neo4jError) as exc:
        LOG.warning("find_implementors failed for %s: %s", interface_name, exc)
        return []


def find_classes_by_concept(concept: str, limit: int = 10) -> list[dict[str, Any]]:
    cleaned = " ".join(part for part in concept.split() if part)
    if not cleaned:
        return []
    query = """
    CALL db.index.fulltext.queryNodes('class_fulltext', $query) YIELD node, score
    OPTIONAL MATCH (node)-[:EXTENDS]->(parent:Class)
    RETURN node.name AS name,
           node.qualifiedName AS qualified_name,
           node.package AS package,
           node.topPackage AS top_package,
           node.isAbstract AS is_abstract,
           node.isInterface AS is_interface,
           node.filePath AS file_path,
           parent.qualifiedName AS extends,
           [] AS implements,
           score AS score
    ORDER BY score DESC, node.qualifiedName ASC
    LIMIT $limit
    """
    try:
        with _driver() as driver, driver.session() as session:
            return [
                {
                    **_class_record_to_dict(record),
                    "score": float(record.get("score") or 0.0),
                }
                for record in session.run(query, query=cleaned, limit=limit)
            ]
    except (RuntimeError, Neo4jError) as exc:
        LOG.warning("find_classes_by_concept failed for %s: %s", concept, exc)
        return []


def get_class_detail(class_name: str) -> dict[str, Any] | None:
    query = """
    MATCH (node:Class)
    WHERE node.qualifiedName = $name OR node.name = $name
    OPTIONAL MATCH (node)-[:EXTENDS]->(parent:Class)
    OPTIONAL MATCH (node)-[:IMPLEMENTS]->(iface:Class)
    RETURN node.name AS name,
           node.qualifiedName AS qualified_name,
           node.package AS package,
           node.topPackage AS top_package,
           node.isAbstract AS is_abstract,
           node.isInterface AS is_interface,
           node.filePath AS file_path,
           parent.qualifiedName AS extends,
           collect(DISTINCT iface.qualifiedName) AS implements
    LIMIT 1
    """
    try:
        with _driver() as driver, driver.session() as session:
            record = session.run(query, name=class_name).single()
    except (RuntimeError, Neo4jError) as exc:
        LOG.warning("get_class_detail failed for %s: %s", class_name, exc)
        return None
    if record is None:
        return None
    return _class_record_to_dict(record)


def timed_base_class(top_package: str) -> tuple[dict[str, Any] | None, float]:
    started = perf_counter()
    result = find_base_class(top_package)
    return result, (perf_counter() - started) * 1000.0
