from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from tools.ast_indexer.query_graph import find_base_class, find_classes_by_concept, timed_base_class


IDENTITY_ANSWER = (
    "I am Motadata Coder, an AI-powered coding assistant built for the Motadata product "
    "codebase. I am governed by a constitutional AI framework with Plan-Gate runtime "
    "enforcement. I help engineers understand, navigate, and reason about the "
    "com.mindarray.* codebase across the Motadata Java sources."
)

_IDENTITY_TRIGGERS = (
    "what model are you",
    "who are you",
    "what are you",
    "which model",
    "are you gpt",
    "are you claude",
    "are you llm",
    "tell me about yourself",
    "what is motadata coder",
    "introduce yourself",
)

_STRUCTURAL_PRIMARY = (
    "base class",
    "parent class",
    "abstract class",
    "extends",
    "implements",
    "inheritance",
    "subclass",
    "class hierarchy",
    "interface for",
)

_DECOMPOSE_PREFIXES = (
    "how does",
    "how do",
    "how is",
    "how are",
    "explain",
    "describe",
    "walk me through",
)

_DECOMPOSE_HINTS = ("configuration", "workflow", "mechanism", "architecture")

_STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "work",
    "does",
    "doesn",
    "into",
    "from",
    "what",
    "which",
    "how",
    "about",
}

_TOP_PACKAGES = {
    "api",
    "aiops",
    "agent",
    "cache",
    "compliance",
    "config",
    "datastore",
    "db",
    "eventbus",
    "flow",
    "ha",
    "integration",
    "job",
    "log",
    "manager",
    "netroute",
    "nms",
    "notification",
    "patch",
    "plugin",
    "policy",
    "report",
    "rum",
    "runbook",
    "slo",
    "store",
    "streaming",
    "trace",
    "util",
    "visualization",
}

_CONCEPT_HINTS = {
    "mail": ["MailServerConfiguration", "EmailNotification"],
    "email": ["MailServerConfiguration", "EmailNotification"],
    "smtp": ["MailServerConfiguration", "EmailNotification"],
    "server": ["MailServerConfiguration"],
    "configuration": ["MailServerConfiguration", "Configuration"],
    "notification": ["Notification", "NotificationEngine"],
    "config": ["Configuration", "MailServerConfiguration"],
}


class QueryIntent(Enum):
    IDENTITY = "identity"
    STRUCTURAL = "structural"
    DECOMPOSE = "decompose"
    SEMANTIC = "semantic"


@dataclass
class RouterResult:
    intent: QueryIntent
    answer: str | None
    sub_queries: list[str] | None
    skip_rag: bool
    metadata: dict[str, Any]


class QueryRouter:
    def classify(self, query: str) -> RouterResult:
        normalized = self._normalize(query)
        if self._matches_identity(normalized):
            return RouterResult(
                intent=QueryIntent.IDENTITY,
                answer=IDENTITY_ANSWER,
                sub_queries=None,
                skip_rag=True,
                metadata={
                    "intent": QueryIntent.IDENTITY.value,
                    "match_reason": "identity_trigger",
                },
            )

        structural_package = self._structural_package_hint(normalized)
        if structural_package:
            return RouterResult(
                intent=QueryIntent.STRUCTURAL,
                answer=None,
                sub_queries=None,
                skip_rag=False,
                metadata={
                    "intent": QueryIntent.STRUCTURAL.value,
                    "match_reason": "structural_trigger",
                    "package_hint": structural_package,
                },
            )

        if self._needs_decomposition(normalized):
            sub_queries = self._build_sub_queries(query)
            return RouterResult(
                intent=QueryIntent.DECOMPOSE,
                answer=None,
                sub_queries=sub_queries,
                skip_rag=False,
                metadata={
                    "intent": QueryIntent.DECOMPOSE.value,
                    "match_reason": "broad_semantic_trigger",
                    "fallback": self._decompose_fallback_mode(query, sub_queries),
                },
            )

        return RouterResult(
            intent=QueryIntent.SEMANTIC,
            answer=None,
            sub_queries=None,
            skip_rag=False,
            metadata={
                "intent": QueryIntent.SEMANTIC.value,
                "match_reason": "default_semantic",
            },
        )

    def resolve_structural(self, query: str, metadata: dict[str, Any] | None = None) -> RouterResult:
        base_meta = dict(metadata or {})
        package_hint = str(base_meta.get("package_hint") or self._structural_package_hint(self._normalize(query)) or "")
        graph_result = None
        graph_query_ms = 0.0
        graph_error: str | None = None

        if package_hint and self._asks_for_base_class(query):
            timed_result = timed_base_class(package_hint)
            if len(timed_result) == 3:
                graph_result, graph_query_ms, graph_error = timed_result
            else:
                graph_result, graph_query_ms = timed_result  # backward compatibility
                graph_error = None

        if graph_error:
            answer = (
                f"Structural query requires Neo4j graph access for package '{package_hint}'. "
                "Graph is currently unavailable; no semantic fallback was used."
            )
            base_meta.update(
                {
                    "intent": QueryIntent.STRUCTURAL.value,
                    "match_reason": "structural_graph_required_unavailable",
                    "graph_query_ms": round(graph_query_ms, 3),
                    "graph_error": graph_error,
                    "evidence_quality": "INSUFFICIENT",
                    "quality_reasons": ["GRAPH_UNAVAILABLE"],
                }
            )
            return RouterResult(
                intent=QueryIntent.STRUCTURAL,
                answer=answer,
                sub_queries=None,
                skip_rag=True,
                metadata=base_meta,
            )

        if graph_result:
            fqcn = str(graph_result.get("qualified_name") or graph_result.get("name") or "")
            answer = f"Direct answer (grounded): The base class for all {package_hint.upper()}s is {fqcn}."
            base_meta.update(
                {
                    "intent": QueryIntent.STRUCTURAL.value,
                    "match_reason": base_meta.get("match_reason") or "structural_graph_answer",
                    "graph_query_ms": round(graph_query_ms, 3),
                    "graph_result": graph_result,
                }
            )
            return RouterResult(
                intent=QueryIntent.STRUCTURAL,
                answer=answer,
                sub_queries=None,
                skip_rag=True,
                metadata=base_meta,
            )

        base_meta.update(
            {
                "intent": QueryIntent.SEMANTIC.value,
                "match_reason": "structural_graph_miss_fallback",
                "graph_query_ms": round(graph_query_ms, 3),
            }
        )
        return RouterResult(
            intent=QueryIntent.SEMANTIC,
            answer=None,
            sub_queries=None,
            skip_rag=False,
            metadata=base_meta,
        )

    def _matches_identity(self, normalized: str) -> bool:
        return any(trigger in normalized for trigger in _IDENTITY_TRIGGERS)

    def _structural_package_hint(self, normalized: str) -> str | None:
        if not any(trigger in normalized for trigger in _STRUCTURAL_PRIMARY):
            return None
        if "which class" in normalized and not any(trigger in normalized for trigger in _STRUCTURAL_PRIMARY[:2]):
            return None
        for token in _TOP_PACKAGES:
            if re.search(rf"\b{re.escape(token)}\b", normalized):
                return token
        if "all apis" in normalized or "all api" in normalized or " api" in normalized:
            return "api"
        return None

    def _needs_decomposition(self, normalized: str) -> bool:
        words = [token for token in normalized.split() if token]
        if any(normalized.startswith(prefix) for prefix in _DECOMPOSE_PREFIXES):
            return True
        return len(words) > 5 and any(hint in normalized for hint in _DECOMPOSE_HINTS)

    def _build_sub_queries(self, query: str) -> list[str]:
        base = self._squash_ws(query)
        graph_matches = self._graph_concept_matches(base)
        if graph_matches:
            primary = graph_matches[0]
            primary_name = str(primary.get("name") or "").strip()
            primary_qualified = str(primary.get("qualified_name") or primary_name).strip()
            sub_queries = [primary_qualified, f"{base} {primary_qualified}"]
            if len(graph_matches) > 1:
                secondary = graph_matches[1]
                secondary_qualified = str(secondary.get("qualified_name") or secondary.get("name") or "").strip()
                if secondary_qualified:
                    sub_queries.append(f"{base} {secondary_qualified}")
            elif primary_name:
                sub_queries.append(f"{base} {primary_name}")
            return self._dedupe_and_trim(sub_queries)[:3]
        fallback = [base, f"{base} com.mindarray", f"{base} class method"]
        return self._dedupe_and_trim(fallback)[:3]

    def _decompose_fallback_mode(self, query: str, sub_queries: list[str]) -> str:
        normalized = self._normalize(query)
        seeded = [item for item in sub_queries[1:] if normalized not in self._normalize(item)]
        if seeded:
            return "graph_seeded_subqueries"
        return "deterministic_subqueries"

    def _graph_concept_matches(self, query: str) -> list[dict[str, Any]]:
        tokens = [token for token in re.split(r"[^a-zA-Z0-9]+", query.lower()) if token and token not in _STOP_WORDS]
        seeded: list[str] = []
        for token in tokens:
            seeded.extend(_CONCEPT_HINTS.get(token, []))
        concept = " ".join(dict.fromkeys(seeded or tokens[:4]))
        if not concept:
            return []
        matches = find_classes_by_concept(concept, limit=4)
        normalized_matches: list[dict[str, Any]] = []
        seen: set[str] = set()
        for match in matches:
            qualified_name = str(match.get("qualified_name") or "").strip()
            name = str(match.get("name") or "").strip()
            key = qualified_name or name
            if not key or key in seen:
                continue
            seen.add(key)
            normalized_matches.append(
                {
                    "name": name,
                    "qualified_name": qualified_name,
                }
            )
        if normalized_matches:
            return normalized_matches
        fallback_matches: list[dict[str, Any]] = []
        for seeded_name in dict.fromkeys(seeded):
            fallback_matches.append(
                {
                    "name": seeded_name,
                    "qualified_name": f"com.mindarray.api.{seeded_name}",
                }
            )
        return fallback_matches

    def _asks_for_base_class(self, query: str) -> bool:
        normalized = self._normalize(query)
        return any(token in normalized for token in ("base class", "parent class", "abstract class"))

    def _dedupe_and_trim(self, queries: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for item in queries:
            trimmed = self._squash_ws(item)
            if not trimmed or trimmed.lower() in seen:
                continue
            seen.add(trimmed.lower())
            out.append(trimmed[:220])
        return out

    def _normalize(self, query: str) -> str:
        return self._squash_ws(query).lower()

    def _squash_ws(self, value: str) -> str:
        return " ".join((value or "").split())