from runtime.ask_service.debug_output_finalize import finalize_explain_debug_prose
from runtime.ask_service.reasoner import ExplainDebugResult


def test_finalize_strips_async_speculation():
    raw = ExplainDebugResult(
        summary="The update might be asynchronous; user sees stale data.",
        logic_flow=(
            "The code calls updateStore(). If the update is asynchronous, observers may lag. "
            "This could involve several steps involving the network."
        ),
        likely_bug_risk=(
            "Possibly timing: if persistence is asynchronous, reads may return stale values without knowing the specifics."
        ),
        evidence=["motadata/a/Mail.java:analysis_anchor"],
        confidence_limits="Snippet is narrow.",
    )
    out = finalize_explain_debug_prose(
        raw,
        query="why stale mail",
        selected_file="motadata/a/MailServerConfiguration.java",
    )
    assert "asynchronous" not in out.summary.lower()
    assert "might be asynchronous" not in out.logic_flow.lower()
    assert "several steps" not in out.logic_flow.lower()
    lines = [ln.strip() for ln in out.logic_flow.splitlines() if ln.strip()]
    assert 1 <= len(lines) <= 3
    assert not out.likely_bug_risk.lower().startswith("possibly")


def test_finalize_preserves_unknown_likelihood():
    raw = ExplainDebugResult(
        summary="Grounded hypothesis.",
        logic_flow="Trace branches.",
        likely_bug_risk="Unknown based on provided evidence.",
        evidence=["x:y"],
        confidence_limits="narrow",
    )
    out = finalize_explain_debug_prose(raw, query="debug", selected_file="a/B.java")
    assert "unknown based on provided evidence" in out.likely_bug_risk.lower()


def test_finalize_api_route_keeps_route_summary():
    raw = ExplainDebugResult(
        summary=(
            "Route visibility should be verified at API wiring points: "
            "`APIServer.start`, `/api/v1/*`, `APIRouter.init`, `AbstractAPI.init`."
        ),
        logic_flow="Trace mounts and registrations.\nSecond line.\nThird line filler.",
        likely_bug_risk="Likely failure is route registration mismatch across wiring points.",
        evidence=["apiserver:x"],
        confidence_limits="narrow",
    )
    out = finalize_explain_debug_prose(
        raw,
        selected_file="src/main/java/com/mindarray/api/APIServer.java",
        query="Why might routes not appear at runtime?",
    )
    assert "APIServer.start" in out.summary
    assert "mismatch" in out.likely_bug_risk.lower()
