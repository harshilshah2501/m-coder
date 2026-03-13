from stage6.stage6c.model.ref_sanitizer import (
    REF_CANONICAL_RESPONSE,
    extract_expected_phase,
    ref_sanitize,
    should_apply_ref_sanitizer,
)


def _messages(expected_phase=None):
    metadata = {"run_id": "r1", "step_index": 0, "step_role": "rehydrate"}
    if expected_phase is not None:
        metadata["expected_phase"] = expected_phase
    return [
        {
            "role": "user",
            "content": "Step 1 (rehydrate): Proceed according to the scenario.",
            "origin": "step_query",
            "metadata": metadata,
        }
    ]


def test_ref_sanitize_step_trigger():
    text, did_sanitize, reasons = ref_sanitize("Step 2: do this first")
    assert did_sanitize is True
    assert text == REF_CANONICAL_RESPONSE
    assert "step_number" in reasons


def test_ref_sanitize_markdown_heading_trigger():
    text, did_sanitize, reasons = ref_sanitize("## Implementation\nDo the thing")
    assert did_sanitize is True
    assert text == REF_CANONICAL_RESPONSE
    assert "markdown_heading" in reasons


def test_ref_sanitize_following_steps_phrase_trigger():
    text, did_sanitize, reasons = ref_sanitize("The following steps are taken to complete the task")
    assert did_sanitize is True
    assert text == REF_CANONICAL_RESPONSE
    assert "following_steps_phrase" in reasons


def test_ref_sanitize_procedural_terms_trigger():
    text, did_sanitize, reasons = ref_sanitize("Here is the workflow to proceed safely")
    assert did_sanitize is True
    assert text == REF_CANONICAL_RESPONSE
    assert "procedural_terms" in reasons


def test_ref_sanitize_numbered_list_trigger():
    text, did_sanitize, reasons = ref_sanitize("1. first\n2. second")
    assert did_sanitize is True
    assert text == REF_CANONICAL_RESPONSE
    assert "numbered_list" in reasons


def test_ref_sanitize_non_procedural_kept():
    text, did_sanitize, reasons = ref_sanitize("I cannot help with that.")
    assert did_sanitize is False
    assert text == "I cannot help with that."
    assert reasons == []


def test_extract_expected_phase_from_metadata():
    assert extract_expected_phase(_messages("ref")) == "REF"


def test_should_apply_ref_sanitizer_expected_phase_ref():
    apply_sanitizer, gate_path, expected_phase = should_apply_ref_sanitizer(
        _messages("REF"),
        expected_phase="REF",
        fail_closed=False,
    )
    assert apply_sanitizer is True
    assert gate_path == "expected_phase_ref"
    assert expected_phase == "REF"


def test_should_not_apply_ref_sanitizer_non_ref_phase():
    apply_sanitizer, gate_path, expected_phase = should_apply_ref_sanitizer(
        _messages("CONF"),
        expected_phase="CONF",
        fail_closed=True,
    )
    assert apply_sanitizer is False
    assert gate_path == "disabled"
    assert expected_phase == "CONF"


def test_should_apply_ref_sanitizer_fail_closed_when_phase_missing():
    apply_sanitizer, gate_path, expected_phase = should_apply_ref_sanitizer(
        _messages(),
        expected_phase=None,
        fail_closed=True,
    )
    assert apply_sanitizer is True
    assert gate_path == "fail_closed_missing_phase"
    assert expected_phase is None


def test_should_not_apply_ref_sanitizer_when_phase_missing_and_fail_closed_off():
    apply_sanitizer, gate_path, expected_phase = should_apply_ref_sanitizer(
        _messages(),
        expected_phase=None,
        fail_closed=False,
    )
    assert apply_sanitizer is False
    assert gate_path == "disabled"
    assert expected_phase is None


def test_explicit_expected_phase_overrides_message_metadata():
    apply_sanitizer, gate_path, expected_phase = should_apply_ref_sanitizer(
        _messages("REF"),
        expected_phase="CONF",
        fail_closed=True,
    )
    assert apply_sanitizer is False
    assert gate_path == "disabled"
    assert expected_phase == "CONF"
