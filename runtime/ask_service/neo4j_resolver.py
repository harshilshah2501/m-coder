from __future__ import annotations

import os
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List

from runtime.neo4j_credentials import neo4j_password_from_env


@dataclass(frozen=True)
class GraphResolutionMeta:
    schema_version: str
    capability: str
    enabled: bool
    attempted: bool
    used: bool
    source: str
    answer_type: str
    confidence: str
    candidate_base: str
    support_count: int
    sample_classes: List[str]
    fallback_reason: str
    error: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _env_bool(name: str, default: bool) -> bool:
    raw = str(os.environ.get(name, "1" if default else "0")).strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _query_mentions_api(query: str) -> bool:
    return re.search(r"\bapis?\b", query.lower()) is not None


def _is_class_relationship_query(query: str) -> bool:
    q = query.lower()
    triggers = ("base class", "parent class", "extends", "implements", "which class", "inheritance")
    return any(t in q for t in triggers)


def _is_universal_api_base_query(query: str) -> bool:
    q = f" {query.lower()} "
    phrases = (
        " base class for all ",
        " parent class for all ",
        " all apis ",
        " all api ",
        " every api ",
    )
    return any(p in q for p in phrases)


def _meta(
    *,
    capability: str,
    enabled: bool,
    attempted: bool = False,
    used: bool = False,
    source: str = "none",
    answer_type: str = "none",
    confidence: str = "none",
    candidate_base: str = "",
    support_count: int = 0,
    sample_classes: List[str] | None = None,
    fallback_reason: str = "",
    error: str = "",
) -> Dict[str, Any]:
    m = GraphResolutionMeta(
        schema_version="graph_resolution_meta.v1",
        capability=capability,
        enabled=enabled,
        attempted=attempted,
        used=used,
        source=source,
        answer_type=answer_type,
        confidence=confidence,
        candidate_base=candidate_base,
        support_count=support_count,
        sample_classes=sample_classes or [],
        fallback_reason=fallback_reason,
        error=error,
    )
    return m.to_dict()


def resolve_relationship(query: str, *, capability: str = "ask") -> Dict[str, Any]:
    """
    Task-agnostic relationship resolver; currently configured for Ask rollout.

    Returns a stable metadata envelope used by ingest/planner layers.
    """
    base_enabled = _env_bool("MOTADATA_NEO4J_ENABLED", False)
    cap_name = capability.strip().upper() if capability else "ASK"
    cap_enabled = _env_bool(f"MOTADATA_NEO4J_{cap_name}_ENABLED", capability.lower() == "ask")
    enabled = bool(base_enabled and cap_enabled)
    if not enabled:
        return _meta(
            capability=capability,
            enabled=False,
            attempted=False,
            used=False,
            fallback_reason="neo4j_disabled",
        )
    if not _is_class_relationship_query(query):
        return _meta(
            capability=capability,
            enabled=True,
            attempted=False,
            used=False,
            source="neo4j",
            fallback_reason="non_class_relationship_query",
        )
    if not (_query_mentions_api(query) and _is_universal_api_base_query(query)):
        return _meta(
            capability=capability,
            enabled=True,
            attempted=False,
            used=False,
            source="neo4j",
            fallback_reason="unsupported_relationship_shape",
        )

    uri = str(os.environ.get("MOTADATA_NEO4J_URI", "")).strip()
    user = str(os.environ.get("MOTADATA_NEO4J_USER", "")).strip()
    password = neo4j_password_from_env()
    if not uri:
        return _meta(
            capability=capability,
            enabled=True,
            attempted=False,
            used=False,
            source="neo4j",
            fallback_reason="missing_neo4j_uri",
        )
    try:
        from neo4j import GraphDatabase  # type: ignore
    except Exception as exc:  # pragma: no cover - env dependent
        return _meta(
            capability=capability,
            enabled=True,
            attempted=False,
            used=False,
            source="neo4j",
            fallback_reason="neo4j_driver_unavailable",
            error=str(exc),
        )

    cypher = (
        "MATCH (c:Class) "
        "WHERE toLower(c.package) CONTAINS 'com.mindarray.api' "
        "  AND NOT toLower(c.name) CONTAINS 'server' "
        "WITH collect(c) AS classes, size(collect(c)) AS total "
        "UNWIND classes AS c "
        "MATCH (c)-[:EXTENDS]->(b:Class) "
        "RETURN b.name AS base, count(*) AS support, total AS total, collect(c.name)[0..10] AS samples "
        "ORDER BY support DESC LIMIT 1"
    )
    attempted = True
    try:
        auth = (user, password) if user or password else None
        driver = GraphDatabase.driver(uri, auth=auth)
        with driver.session() as session:
            row = session.run(cypher).single()
        driver.close()
    except Exception as exc:  # pragma: no cover - env dependent
        return _meta(
            capability=capability,
            enabled=True,
            attempted=attempted,
            used=False,
            source="neo4j",
            fallback_reason="neo4j_query_failed",
            error=str(exc),
        )

    if row is None:
        return _meta(
            capability=capability,
            enabled=True,
            attempted=attempted,
            used=False,
            source="neo4j",
            fallback_reason="graph_no_match",
        )

    base = str(row.get("base") or "").strip()
    support = int(row.get("support") or 0)
    total = int(row.get("total") or 0)
    samples_raw = row.get("samples") or []
    samples = [str(x) for x in samples_raw if str(x).strip()]

    if not base or support < 2 or total < 2:
        return _meta(
            capability=capability,
            enabled=True,
            attempted=attempted,
            used=False,
            source="neo4j",
            answer_type="common_base",
            confidence="low",
            candidate_base=base,
            support_count=support,
            sample_classes=samples,
            fallback_reason="insufficient_graph_support",
        )
    if support * 2 < total:
        return _meta(
            capability=capability,
            enabled=True,
            attempted=attempted,
            used=False,
            source="neo4j",
            answer_type="common_base",
            confidence="medium",
            candidate_base=base,
            support_count=support,
            sample_classes=samples,
            fallback_reason="no_majority_common_base",
        )
    return _meta(
        capability=capability,
        enabled=True,
        attempted=attempted,
        used=True,
        source="neo4j",
        answer_type="common_base",
        confidence="high",
        candidate_base=base,
        support_count=support,
        sample_classes=samples,
        fallback_reason="",
    )

