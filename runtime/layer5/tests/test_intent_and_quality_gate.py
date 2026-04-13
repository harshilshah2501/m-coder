from __future__ import annotations

from runtime.layer5.retrieval.intent import (
    CODE_INTENT,
    DEBUG_INTENT,
    GENERIC_INTENT,
    PLAN_INTENT,
    classify_intent,
)
from runtime.layer5.retrieval.quality_gate import (
    INSUFFICIENT,
    NO_MATCH,
    STRONG,
    WEAK,
    assess_evidence_quality,
    operator_hints_for_assessment,
)


def test_intent_camelcase_symbol_is_code_intent():
    r = classify_intent("Where is AlertCorrelationEngine implemented?")
    assert r.intent_type == CODE_INTENT
    assert r.has_symbol_signal is True


def test_intent_error_phrase_is_debug_intent():
    r = classify_intent("Why is this failing with timeout error?")
    assert r.intent_type == DEBUG_INTENT


def test_intent_change_phrase_is_plan_intent():
    r = classify_intent("Plan update to add retries to ingestion pipeline")
    assert r.intent_type == PLAN_INTENT


def test_intent_generic_question_is_generic_intent():
    r = classify_intent("What is this system?")
    assert r.intent_type == GENERIC_INTENT


def test_intent_which_files_implement_is_code_intent():
    r = classify_intent("Which files implement topology anomaly scoring pipeline?")
    assert r.intent_type == CODE_INTENT


def test_intent_sentence_period_does_not_create_false_symbol():
    """PR-5: trailing 'code.' must not be parsed as a dotted identifier."""
    r = classify_intent("Explain the highlighted code.")
    assert r.has_symbol_signal is False


def test_quality_gate_strong_for_core_aiops_heavy_paths():
    q = assess_evidence_quality(
        "where implemented alert correlation engine",
        [
            "src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java",
            "src/main/java/com/mindarray/aiops/alerting/AlertProcessor.java",
            "src/main/java/com/mindarray/aiops/correlation/CorrelationService.java",
        ],
    )
    assert q.evidence_quality == STRONG
    assert q.blocked is False


def test_quality_gate_weak_for_noise_dominated_with_some_code():
    q = assess_evidence_quality(
        "where implemented engine",
        [
            "tests/engine_test.py",
            "logs/engine.log",
            "vendor/engine.js",
            "src/main/java/com/mindarray/aiops/ingestion/EngineProcessor.java",
        ],
    )
    assert q.evidence_quality == WEAK
    assert "NOISE_DOMINATED" in q.quality_reasons or "LOW_CODE_RATIO" in q.quality_reasons
    assert q.blocked is False


def test_quality_gate_no_relevant_hits_is_weak_for_generic():
    q = assess_evidence_quality("in this system", [])
    assert q.evidence_quality == WEAK
    assert q.blocked is False


def test_quality_gate_generic_with_code_paths_stays_weak_not_strong():
    q = assess_evidence_quality(
        "why where fix engine parser issue",
        [
            "src/main/java/com/mindarray/visualization/VisualizationMetricManager.java",
            "src/main/java/com/mindarray/store/ObjectConfigStore.java",
            "src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java",
        ],
    )
    assert q.evidence_quality == WEAK
    assert "QUERY_TOO_GENERIC" in q.quality_reasons
    assert q.blocked is False


def test_operator_hints_query_too_generic_includes_explain_debug_guidance():
    q = assess_evidence_quality(
        "how does something work in this repo",
        ["src/main/java/com/mindarray/aiops/Foo.java"],
    )
    assert "QUERY_TOO_GENERIC" in q.quality_reasons
    hints = operator_hints_for_assessment(q)
    assert any("Explain/Debug" in h for h in hints)
    assert any("PLAN_ONLY" in h for h in hints)


def test_quality_gate_nonexistent_symbol_is_no_match():
    q = assess_evidence_quality("Where is FooBarMissingSymbol() implemented?", [])
    assert q.evidence_quality == NO_MATCH
    assert q.blocked is True


def test_quality_gate_concrete_code_location_empty_bundle_is_no_match():
    """PR-5: CODE_INTENT with no paths is absence of evidence, not INSUFFICIENT."""
    q = assess_evidence_quality("Where is quantum entanglement handler implemented?", [])
    assert q.evidence_quality == NO_MATCH
    assert q.blocked is True


def test_quality_gate_symbol_not_in_evidence_paths_is_no_match_not_weak():
    """PR-5: unrelated files do not downgrade symbol-miss to WEAK."""
    q = assess_evidence_quality(
        "Where is NonExistentCorrelationSymbol999() used?",
        ["src/main/java/com/mindarray/aiops/correlation/CorrelationService.java"],
    )
    assert q.evidence_quality == NO_MATCH
    assert "NO_SYMBOL_MATCH" in q.quality_reasons
    assert q.blocked is True


def test_quality_gate_noise_only_non_symbol_code_intent_is_insufficient():
    """Noise-only paths without symbol signal stay INSUFFICIENT (partial junk, not symbol miss)."""
    q = assess_evidence_quality(
        "Where is ingestion retry policy documented?",
        ["logs/retry.log", "tests/retry_test.py"],
    )
    assert q.evidence_quality == INSUFFICIENT
    assert q.blocked is True


def test_operator_hints_surface_low_core_and_noise():
    q = assess_evidence_quality(
        "where implemented engine",
        [
            "tests/engine_test.py",
            "logs/engine.log",
            "vendor/engine.js",
            "src/main/java/com/mindarray/aiops/ingestion/EngineProcessor.java",
        ],
    )
    hints = operator_hints_for_assessment(q)
    assert len(hints) >= 1
    joined = " ".join(hints).lower()
    assert "core" in joined or "noisy" in joined or "production" in joined or "top-3" in joined
