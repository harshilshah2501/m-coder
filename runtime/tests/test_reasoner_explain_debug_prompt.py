"""Tests for explain_debug prompt construction (fragment selections, bundle order)."""

from __future__ import annotations

from runtime.ask_service.reasoner import (
    ExplainDebugResult,
    _build_prompt,
    _debug_control_flow_marker_count,
    _extract_method_clues,
    _has_control_flow_cues,
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


def test_build_prompt_includes_explain_debug_contract_guards():
    b = _bundle_two_files()
    p = _build_prompt(
        "How does this fail?",
        "motadata/src/AgentCacheManager.java",
        "getAgentCacheFileChunks()",
        b,
    )
    assert "Explain/debug contract (must follow)" in p
    assert "Do not invent symbols, methods, files" in p
    assert "insufficiently grounded" in p
    assert "avoid definitive root-cause claims without evidence" in p


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


def test_ensure_selected_grounding_uses_selection_tokens_when_methods_absent():
    b = ContextBundle(
        task_id="t2",
        revision="r2",
        created_at_utc="2026-01-01T00:00:00Z",
        items=[
            ContextItem(
                path="app/handler.py",
                content="cache_value = cache.get(key)\nreturn cache_value\n",
                byte_size=64,
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
    parsed = ExplainDebugResult(summary="Potential cache issue.", evidence=[])
    out = _ensure_selected_grounding(
        parsed,
        selected_file="app/handler.py",
        selection="cache.get(key)",
        bundle=b,
    )
    assert out.error is None
    assert out.evidence
    assert "app/handler.py:cache" in out.evidence[0]
    assert "selection-linked clues" in (out.logic_flow or "").lower()


def test_ensure_selected_grounding_uses_current_bundle_content_for_method_clues():
    b = ContextBundle(
        task_id="t3",
        revision="r3",
        created_at_utc="2026-01-01T00:00:00Z",
        items=[
            ContextItem(
                path="src/main.py",
                content="def overlay_hotfix():\n    return 99\n",
                byte_size=48,
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
    parsed = ExplainDebugResult(summary="Potential issue.", evidence=[])
    out = _ensure_selected_grounding(
        parsed,
        selected_file="src/main.py",
        selection="overlay_hotfix()",
        bundle=b,
    )
    assert out.error is None
    assert out.evidence
    assert "src/main.py:overlay_hotfix" in out.evidence[0]


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


def test_has_control_flow_cues_detects_for_and_try_blocks():
    text = """
public void parse() {
    for (Trap t : traps) {
        try {
            handle(t);
        } catch (Exception e) {
            throw e;
        }
    }
}
"""
    assert _has_control_flow_cues(text) is True


def test_ensure_selected_grounding_injects_branching_markers_when_linear():
    b = ContextBundle(
        task_id="t4",
        revision="r4",
        created_at_utc="2026-01-01T00:00:00Z",
        items=[
            ContextItem(
                path="motadata/src/main/java/com/mindarray/nms/SNMPTrapProcessor.java",
                content=(
                    "public void loadTrapTypes() {\n"
                    "  for (Trap t : traps) {\n"
                    "    try { parse(t); } catch (Exception e) { throw e; }\n"
                    "  }\n"
                    "}\n"
                ),
                byte_size=180,
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
    parsed = ExplainDebugResult(
        summary="The code reads config and parses entries.",
        logic_flow="The flow is read then parse then iterate entries.",
        likely_bug_risk="Potential file/decryption failure.",
        evidence=[],
    )
    out = _ensure_selected_grounding(
        parsed,
        selected_file="motadata/src/main/java/com/mindarray/nms/SNMPTrapProcessor.java",
        selection="parse trap-types",
        bundle=b,
    )
    assert out.error is None
    combined = f"{out.summary} {out.logic_flow} {out.likely_bug_risk}"
    assert _debug_control_flow_marker_count(combined) >= 2


def test_ensure_selected_grounding_tightens_wording_when_executable():
    b = ContextBundle(
        task_id="t5",
        revision="r5",
        created_at_utc="2026-01-01T00:00:00Z",
        items=[
            ContextItem(
                path="motadata/src/main/java/com/mindarray/api/MailServerConfiguration.java",
                content=(
                    "public class MailServerConfiguration {\n"
                    "  public void beforeUpdate() {\n"
                    "    if (authEnabled) { return; }\n"
                    "    else { throw new RuntimeException(); }\n"
                    "  }\n"
                    "}\n"
                ),
                byte_size=220,
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
    parsed = ExplainDebugResult(
        summary="Behavior is not directly visible without more context.",
        logic_flow="",
        likely_bug_risk="",
        evidence=[],
        confidence_limits="",
    )
    out = _ensure_selected_grounding(
        parsed,
        selected_file="motadata/src/main/java/com/mindarray/api/MailServerConfiguration.java",
        selection="beforeUpdate",
        bundle=b,
    )
    assert out.error is None
    assert "not directly visible" not in out.summary.lower()
    assert "without more context" not in out.summary.lower()
    assert "executable grounding" in out.logic_flow.lower()
    assert any(tok in out.likely_bug_risk.lower() for tok in ("branch", "early-return", "exception"))
    assert "insufficient_for_precise_trace" not in out.confidence_limits.lower()
