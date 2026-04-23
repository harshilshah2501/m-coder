from __future__ import annotations

from runtime.ask_service.context_budget import (
    apply_context_budget,
    apply_context_budget_for_surface,
    build_context_budget_metadata,
    evaluate_context_budget_policy,
)
from runtime.context.contracts import ContextBundle, ContextBundleLimits, ContextBundleProvenance, ContextItem


def _bundle(items: list[ContextItem]) -> ContextBundle:
    return ContextBundle(
        task_id="t1",
        revision="r1",
        created_at_utc="2026-01-01T00:00:00Z",
        items=items,
        limits=ContextBundleLimits(max_files=50, max_bytes=500_000, truncated=False),
        provenance=ContextBundleProvenance(
            root_path="/repo",
            selectors=["direct_file"],
            requested_files=[],
            symbol_hints=[],
        ),
    )


def test_apply_context_budget_sets_truncation_flags_and_limits():
    b = _bundle(
        [
            ContextItem(path="a.py", content="a" * 40, byte_size=40, selection_reason="direct:file"),
            ContextItem(path="b.py", content="b" * 40, byte_size=40, selection_reason="direct:file"),
            ContextItem(path="c.py", content="c" * 40, byte_size=40, selection_reason="direct:file"),
        ]
    )
    out, flags, used = apply_context_budget(b, max_files=2, max_bytes=70)
    assert len(out.items) == 1
    assert "context_file_cap_reached" in flags
    assert "context_bytes_cap_reached" in flags
    assert out.limits.truncated is True
    assert used == 40


def test_build_context_budget_metadata_emits_required_telemetry_keys():
    b = _bundle([ContextItem(path="a.py", content="def run(x):\n    return x\n", byte_size=24, selection_reason="direct:file")])
    evidence_entries = [{"snippet": {"text": "public void run() {\n if (x == null) return;\n}\n"}}]
    meta = build_context_budget_metadata(
        query="how does run work",
        bundle=b,
        evidence_entries=evidence_entries,
        selected_file="a.py",
        selection="run",
        plan_steps=["Execution-path stitch: run -> validate -> save"],
        truncation_flags=["context_file_cap_reached"],
    )
    for key in (
        "prompt_input_tokens",
        "evidence_entry_count",
        "evidence_file_count",
        "method_snippet_count",
        "snippet_total_bytes",
        "tool_output_bytes",
        "loop_context_bytes",
        "truncation_flags",
        "truncation_applied",
    ):
        assert key in meta
    assert meta["evidence_entry_count"] == 1
    assert meta["evidence_file_count"] == 1
    assert meta["method_snippet_count"] == 1
    assert meta["truncation_flags"] == ["context_file_cap_reached"]
    assert meta["truncation_applied"] is True


def test_apply_context_budget_for_surface_uses_declared_caps():
    b = _bundle(
        [
            ContextItem(path=f"f{i}.py", content="x" * 20_000, byte_size=20_000, selection_reason="direct:file")
            for i in range(30)
        ]
    )
    out, flags, _, policy = apply_context_budget_for_surface(b, surface="plan")
    assert policy["surface"] == "plan"
    assert policy["max_files"] == 24
    assert policy["max_bytes"] == 220_000
    assert len(out.items) <= 24
    assert "truncation_order" in policy
    assert flags  # capped in this synthetic case


def test_evaluate_context_budget_policy_emits_warnings_and_caps():
    telemetry = {
        "prompt_input_tokens": 8_000,
        "bundle_context_bytes": 260_000,
        "truncation_applied": True,
    }
    policy = {
        "max_files": 40,
        "max_bytes": 350_000,
        "warn_prompt_input_tokens": 7_500,
        "warn_bundle_context_bytes": 240_000,
        "truncation_order": ["bundle_items_order", "max_files", "max_bytes"],
    }
    out = evaluate_context_budget_policy(surface="ask", telemetry=telemetry, policy_config=policy)
    assert out["policy_version"] == "context_budget_policy.v1"
    assert out["surface"] == "ask"
    assert out["hard_caps"]["max_files"] == 40
    assert out["hard_caps"]["max_bytes"] == 350_000
    assert "warn_prompt_input_tokens_exceeded" in out["warnings"]
    assert "warn_bundle_context_bytes_exceeded" in out["warnings"]
    assert "hard_cap_truncation_applied" in out["warnings"]
