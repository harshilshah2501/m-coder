"""Post–Phase 4: authority → bounded coding reasoning bridge."""

from __future__ import annotations

from pathlib import Path

from runtime.ask_service.authority_synthesis import synthesize_authority_plan_steps
from runtime.context.contracts import (
    ContextBundle,
    ContextBundleLimits,
    ContextBundleProvenance,
    ContextItem,
)
from runtime.layer5.authority.authority_code_reasoning import (
    extract_target,
    generate_change_reasoning,
    infer_intent,
)
from runtime.layer5.authority.registry_loader import load_registry


REG = Path(__file__).resolve().parents[1] / "layer5" / "authority" / "product_authority_registry.yaml"


def _bundle(paths: list[str]) -> ContextBundle:
    from datetime import datetime, timezone

    items = [
        ContextItem(path=p, content="", byte_size=0, selection_reason="query_token_substring_anchor")
        for p in paths
    ]
    return ContextBundle(
        task_id="t",
        revision="t",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        items=items,
        limits=ContextBundleLimits(max_files=len(items), max_bytes=0, truncated=False),
        provenance=ContextBundleProvenance(
            root_path="",
            selectors=["t"],
            requested_files=paths,
            symbol_hints=[],
        ),
    )


def _base_ar() -> dict:
    registry = load_registry(REG)
    from runtime.layer5.authority.authority_evidence import build_authority_resolution

    ar = build_authority_resolution("incident deduplication", registry, None)
    assert ar
    return dict(ar)


def test_infer_intent_debug_and_modify():
    assert infer_intent("why is deduplication failing") == "debug"
    assert infer_intent("fix the incident dedup bug") == "debug"  # debug patterns checked first
    assert infer_intent("please change the correlation threshold") == "modify"
    assert infer_intent("where is deduplication implemented") == "explore"


def test_extract_target_owner_only():
    ar = _base_ar()
    t = extract_target(ar)
    assert t
    assert "DependencyQueryProcessor" in t["class"]
    assert t["file"].endswith("DependencyQueryProcessor.java")


def test_debug_scenario_validated_strong_action():
    ar = _base_ar()
    ar["authority_status"] = "validated"
    ar["authority_confidence"] = "high"
    steps, meta = synthesize_authority_plan_steps(
        "debug why deduplication fails for incidents",
        _bundle([ar["primary_owner"]["file"]]),
        ar,
    )
    assert meta.get("intent") == "debug"
    cr = meta.get("change_reasoning")
    assert cr and cr["action_level"] == "strong"
    blob = " ".join(steps).lower()
    assert "bounded reasoning" in blob
    assert "dependencyqueryprocessor" in blob.replace("_", "") or "DependencyQueryProcessor" in " ".join(steps)


def test_fix_scenario_stale_candidate_cautious():
    ar = _base_ar()
    ar["authority_status"] = "stale_candidate"
    steps, meta = synthesize_authority_plan_steps(
        "modify the code to add logging in deduplication",
        _bundle([ar["primary_owner"]["file"]]),
        ar,
    )
    assert meta.get("intent") == "modify"
    cr = meta.get("change_reasoning")
    assert cr and cr["action_level"] == "cautious"
    assert "cautious" in " ".join(steps).lower() or "cautious" in cr["action_level"]


def test_weak_authority_stale_no_fake_fix():
    ar = _base_ar()
    ar["authority_status"] = "stale"
    steps, meta = synthesize_authority_plan_steps(
        "fix deduplication now",
        _bundle([ar["primary_owner"]["file"]]),
        ar,
    )
    cr = meta.get("change_reasoning")
    assert cr and cr["action_level"] == "none"
    text = " ".join(steps).lower()
    assert "do not apply" in text or "do not apply an automated" in text


def test_distractor_does_not_change_target():
    ar = _base_ar()
    ar["authority_status"] = "validated"
    distractor = "src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java"
    owner = ar["primary_owner"]["file"]
    cr = generate_change_reasoning(
        _bundle([distractor, owner]),
        ar,
        "modify",
    )
    assert cr
    assert cr["target_file"] == owner
    assert distractor not in cr["proposed_action"]
    assert cr.get("distractor_in_bundle") is True


def test_generate_change_reasoning_skips_explore():
    ar = _base_ar()
    assert generate_change_reasoning(_bundle([]), ar, "explore") is None


def test_no_regression_phase4_explore_no_change_block():
    """Explore intent should not add change-reasoning steps."""
    ar = _base_ar()
    steps, meta = synthesize_authority_plan_steps(
        "incident deduplication",
        _bundle([ar["primary_owner"]["file"]]),
        ar,
    )
    assert meta.get("intent") == "explore"
    assert meta.get("change_reasoning") is None
    assert not any("bounded reasoning" in s.lower() for s in steps)
