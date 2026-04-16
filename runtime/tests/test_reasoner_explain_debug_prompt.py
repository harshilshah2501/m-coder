"""Tests for explain_debug prompt construction (fragment selections, bundle order)."""

from __future__ import annotations

from runtime.ask_service.reasoner import (
    ExplainDebugResult,
    _build_prompt,
    _extract_method_clues,
    _ensure_selected_grounding,
)
from runtime.context.contracts import (
    ContextBundle,
    ContextBundleLimits,
    ContextBundleProvenance,
    ContextItem,
)


def _bundle_two_files() -> ContextBundle:
    return ContextBundle(
        task_id="t1",
        revision="r1",
        created_at_utc="2026-01-01T00:00:00Z",
        items=[
            ContextItem(
                path="motadata/other/Other.java",
                content="class Other {}",
                byte_size=20,
                selection_reason="retrieval",
            ),
            ContextItem(
                path="motadata/src/AgentCacheManager.java",
                content="class AgentCacheManager { int getAgentCacheFileChunks() { return 3; } }",
                byte_size=80,
                selection_reason="retrieval",
            ),
        ],
        limits=ContextBundleLimits(max_files=10, max_bytes=10000, truncated=False),
        provenance=ContextBundleProvenance(
            root_path="/tmp",
            selectors=["direct"],
            requested_files=[],
            symbol_hints=[],
        ),
    )


def test_build_prompt_minimal_selection_includes_full_context_instructions():
    b = _bundle_two_files()
    p = _build_prompt(
        "What does this do?",
        "motadata/src/AgentCacheManager.java",
        "getAgentCacheFileChunks()",
        b,
    )
    assert "fragment" in p.lower()
    assert "Do **not** answer that the code" in p
    first = p.find("### motadata/src/AgentCacheManager.java")
    second = p.find("### motadata/other/Other.java")
    assert first != -1 and second != -1
    assert first < second


def test_build_prompt_long_selection_omits_minimal_block():
    b = _bundle_two_files()
    long_sel = "\n".join([f"line {i} // padding" for i in range(30)])
    p = _build_prompt("q", "motadata/src/AgentCacheManager.java", long_sel, b)
    assert "Instructions for minimal" not in p


def test_ensure_selected_grounding_adds_selected_file_evidence_first():
    b = _bundle_two_files()
    parsed = ExplainDebugResult(
        summary="Potential issue.",
        logic_flow="Flow described.",
        likely_bug_risk="Might skip work.",
        evidence=["motadata/other/Other.java:foo"],
    )
    out = _ensure_selected_grounding(
        parsed,
        selected_file="motadata/src/AgentCacheManager.java",
        selection="getAgentCacheFileChunks()",
        bundle=b,
    )
    assert out.error is None
    assert out.evidence
    assert "AgentCacheManager.java".lower() in out.evidence[0].lower()


def test_ensure_selected_grounding_returns_insufficient_when_selected_missing():
    b = _bundle_two_files()
    parsed = ExplainDebugResult(summary="ok")
    out = _ensure_selected_grounding(
        parsed,
        selected_file="motadata/src/MissingFile.java",
        selection="foo()",
        bundle=b,
    )
    assert out.error is None
    assert "insufficiently grounded" in out.summary.lower()
    assert any("missing_in_context" in e for e in out.evidence)


def test_extract_method_clues_ignores_constructor_calls_and_prefers_declarations():
    text = """
public class AvailabilityCorrelationEngine {
    public void processAlerts() {
        JsonArray probes = new JsonArray();
        if (probes != null) {
            return;
        }
    }
}
"""
    clues = _extract_method_clues(text, cap=5)
    assert "processAlerts" in clues
    assert "JsonArray" not in clues
