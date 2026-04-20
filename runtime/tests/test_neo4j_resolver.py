from __future__ import annotations

import types
import sys
from typing import Any

from runtime.ask_service.neo4j_resolver import resolve_relationship


class _FakeResult:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self._row = row

    def single(self) -> dict[str, Any] | None:
        return self._row


class _FakeSession:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self._row = row

    def __enter__(self) -> "_FakeSession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def run(self, _cypher: str) -> _FakeResult:
        return _FakeResult(self._row)


class _FakeDriver:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self._row = row

    def session(self) -> _FakeSession:
        return _FakeSession(self._row)

    def close(self) -> None:
        return None


def test_resolve_relationship_returns_disabled_meta_when_feature_off(monkeypatch):
    monkeypatch.delenv("MOTADATA_NEO4J_ENABLED", raising=False)
    out = resolve_relationship("Which class is the base class for all APIs?", capability="ask")
    assert out["schema_version"] == "graph_resolution_meta.v1"
    assert out["used"] is False
    assert out["fallback_reason"] == "neo4j_disabled"


def test_resolve_relationship_uses_graph_result_for_high_confidence(monkeypatch):
    monkeypatch.setenv("MOTADATA_NEO4J_ENABLED", "1")
    monkeypatch.setenv("MOTADATA_NEO4J_ASK_ENABLED", "1")
    monkeypatch.setenv("MOTADATA_NEO4J_URI", "bolt://mock:7687")
    monkeypatch.setenv("MOTADATA_NEO4J_USER", "neo4j")
    monkeypatch.setenv("MOTADATA_NEO4J_PASSWORD", "secret")
    row = {"base": "AbstractAPI", "support": 6, "total": 8, "samples": ["UserAPI", "MetricAPI"]}

    class _FakeGraphDatabase:
        @staticmethod
        def driver(uri: str, auth=None):
            assert uri == "bolt://mock:7687"
            assert auth == ("neo4j", "secret")
            return _FakeDriver(row)

    fake_module = types.SimpleNamespace(GraphDatabase=_FakeGraphDatabase)
    monkeypatch.setitem(sys.modules, "neo4j", fake_module)

    out = resolve_relationship("Which class is the base class for all APIs?", capability="ask")
    assert out["used"] is True
    assert out["answer_type"] == "common_base"
    assert out["candidate_base"] == "AbstractAPI"
    assert out["confidence"] == "high"
    assert out["support_count"] == 6


def test_resolve_relationship_returns_fallback_meta_for_low_support(monkeypatch):
    monkeypatch.setenv("MOTADATA_NEO4J_ENABLED", "1")
    monkeypatch.setenv("MOTADATA_NEO4J_ASK_ENABLED", "1")
    monkeypatch.setenv("MOTADATA_NEO4J_URI", "bolt://mock:7687")
    row = {"base": "AbstractAPI", "support": 1, "total": 2, "samples": ["OnlyOne"]}

    class _FakeGraphDatabase:
        @staticmethod
        def driver(_uri: str, auth=None):
            return _FakeDriver(row)

    fake_module = types.SimpleNamespace(GraphDatabase=_FakeGraphDatabase)
    monkeypatch.setitem(sys.modules, "neo4j", fake_module)

    out = resolve_relationship("Which class is the base class for all APIs?", capability="ask")
    assert out["used"] is False
    assert out["candidate_base"] == "AbstractAPI"
    assert out["fallback_reason"] == "insufficient_graph_support"

