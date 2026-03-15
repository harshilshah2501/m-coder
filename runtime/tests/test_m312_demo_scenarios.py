"""
M3.12 demo scenario validation — deterministic pass/fail for runbook §7.

Runs the three runbook scenarios against the repo and asserts:
- contract (plan_only_response.v0.1, PLAN_ONLY, execution false)
- shape (context_bundle.files with path/selection_reason, plan_summary.steps)
- determinism (same request twice -> same context_bundle.files)
- repo-aware (at least one scenario has non-empty files and manifest selection reason)
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from runtime.ask_service.handlers import handle_ask_request


def _repo_root() -> Path:
    """Repository root: parent of runtime/."""
    return Path(__file__).resolve().parents[2]


def _ask(repo_root: Path, request_id: str, query: str) -> dict:
    return handle_ask_request({
        "schema_version": "ask_request.v0.1",
        "request_id": request_id,
        "timestamp_utc": "2026-03-15T12:00:00Z",
        "repo_root": str(repo_root),
        "revision": "HEAD",
        "query": query,
    })


def _files_signature(resp: dict) -> list[tuple[str, str]]:
    """Deterministic (path, selection_reason) for comparison."""
    return [(f["path"], f["selection_reason"]) for f in resp["context_bundle"]["files"]]


class TestDemoScenario1ContextSelection:
    """Scenario 1: How does context selection work?"""

    def test_contract_and_shape(self):
        root = _repo_root()
        r = _ask(root, "demo-1", "How does context selection work?")
        assert r["schema_version"] == "plan_only_response.v0.1"
        assert r["governance_posture"] == "PLAN_ONLY"
        assert r["execution"] is False
        assert "context_bundle" in r and "files" in r["context_bundle"]
        assert "plan_summary" in r and "steps" in r["plan_summary"]
        for f in r["context_bundle"]["files"]:
            assert "path" in f and "selection_reason" in f
        assert 1 <= len(r["plan_summary"]["steps"]) <= 10

    def test_determinism(self):
        root = _repo_root()
        r1 = _ask(root, "demo-1a", "How does context selection work?")
        r2 = _ask(root, "demo-1b", "How does context selection work?")
        assert _files_signature(r1) == _files_signature(r2)


class TestDemoScenario2RepositoryContextEngine:
    """Scenario 2: Where is the repository context engine documented?"""

    def test_contract_and_shape(self):
        root = _repo_root()
        r = _ask(root, "demo-2", "Where is the repository context engine documented?")
        assert r["schema_version"] == "plan_only_response.v0.1"
        assert r["governance_posture"] == "PLAN_ONLY"
        assert r["execution"] is False
        assert "context_bundle" in r and "files" in r["context_bundle"]
        for f in r["context_bundle"]["files"]:
            assert "path" in f and "selection_reason" in f

    def test_determinism(self):
        root = _repo_root()
        r1 = _ask(root, "demo-2a", "Where is the repository context engine documented?")
        r2 = _ask(root, "demo-2b", "Where is the repository context engine documented?")
        assert _files_signature(r1) == _files_signature(r2)


class TestDemoScenario3PlanGate:
    """Scenario 3: How does Plan-Gate work?"""

    def test_contract_and_shape(self):
        root = _repo_root()
        r = _ask(root, "demo-3", "How does Plan-Gate work?")
        assert r["schema_version"] == "plan_only_response.v0.1"
        assert r["governance_posture"] == "PLAN_ONLY"
        assert r["execution"] is False
        assert "context_bundle" in r and "files" in r["context_bundle"]
        for f in r["context_bundle"]["files"]:
            assert "path" in f and "selection_reason" in f

    def test_determinism(self):
        root = _repo_root()
        r1 = _ask(root, "demo-3a", "How does Plan-Gate work?")
        r2 = _ask(root, "demo-3b", "How does Plan-Gate work?")
        assert _files_signature(r1) == _files_signature(r2)


class TestDemoRepoAwareEvidence:
    """At least one scenario must show repo-aware selection (non-empty files + notes or manifest reason)."""

    def test_at_least_one_scenario_has_repo_aware_selection(self):
        root = _repo_root()
        scenarios = [
            "How does context selection work?",
            "Where is the repository context engine documented?",
            "How does Plan-Gate work?",
        ]
        any_non_empty = False
        any_manifest_evidence = False
        for i, q in enumerate(scenarios):
            r = _ask(root, f"evidence-{i}", q)
            files = r["context_bundle"]["files"]
            if files:
                any_non_empty = True
            for f in files:
                reason = f.get("selection_reason", "")
                if "path_match" in reason or "heading_match" in reason or "symbol:hint" in reason or "adjacent" in reason:
                    any_manifest_evidence = True
                    break
            notes = r.get("plan_summary") or {}
            for note in (notes.get("notes") or []):
                if "Repo-aware selection" in note:
                    any_manifest_evidence = True
                    break
        assert any_non_empty, "At least one scenario should return non-empty context_bundle.files"
        assert any_manifest_evidence, "At least one scenario should show repo-aware evidence (manifest reason or plan_summary.notes)"
