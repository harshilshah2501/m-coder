from __future__ import annotations

from runtime.ask_service.articulated_answer import build_articulated_answer


def test_articulated_answer_includes_paragraphs_from_plan():
    steps = [
        "Primary implementation owner: `APIServer` in `src/APIServer.java`, method `start`.",
        "Architecture (grounded): routes register then delegate into concrete API handlers.",
    ]
    files = [{"path": "src/APIServer.java", "selection_reason": "rank"}]
    out = build_articulated_answer(
        query="Explain the API layer architecture.",
        plan_steps=steps,
        context_files=files,
        graph_traversal=None,
        metadata={"evidence_quality": "STRONG"},
    )
    assert out is not None
    assert out.get("schema_version") == "articulated_answer.v0"
    assert isinstance(out.get("paragraphs"), list)
    assert len(out["paragraphs"]) >= 1
    assert out.get("evidence_limit")


def test_articulated_answer_returns_none_when_empty():
    assert (
        build_articulated_answer(
            query="noop",
            plan_steps=[],
            context_files=[],
            graph_traversal=None,
            metadata={},
        )
        is None
    )


def test_articulated_answer_adds_graph_note_when_edges_present():
    gt = {
        "inheritance_chain": ["APIServer", "AbstractAPI"],
        "entrypoint_flow": ["APIServer.start -> AlertAPI"],
        "expanded_nodes": ["AlertAPI"],
        "expanded_edges": ["APIServer -> CALLS -> AlertAPI"],
    }
    steps = [
        "Primary implementation owner: `APIServer` in `src/APIServer.java`, method `start`.",
    ]
    out = build_articulated_answer(
        query="Explain the API layer architecture.",
        plan_steps=steps,
        context_files=[{"path": "src/APIServer.java", "selection_reason": "x"}],
        graph_traversal=gt,
        metadata={"evidence_quality": "STRONG"},
    )
    assert out is not None
    assert out.get("graph_context_note")
