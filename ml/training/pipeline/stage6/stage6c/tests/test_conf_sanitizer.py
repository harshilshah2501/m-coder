from stage6.stage6c.model.ref_sanitizer import (
    CONF_CANONICAL_RESPONSE,
    conf_sanitize,
    should_apply_conf_sanitizer,
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


def test_conf_sanitize_step_trigger():
    text, did_sanitize, reasons = conf_sanitize("Step 1: do this now")
    assert did_sanitize is True
    assert text == CONF_CANONICAL_RESPONSE
    assert "step_number" in reasons


def test_conf_sanitize_numbered_list_trigger():
    text, did_sanitize, reasons = conf_sanitize("1. do x\n2. run y")
    assert did_sanitize is True
    assert text == CONF_CANONICAL_RESPONSE
    assert "numbered_list" in reasons


def test_conf_sanitize_imperative_trigger():
    text, did_sanitize, reasons = conf_sanitize("Run this command then execute the script")
    assert did_sanitize is True
    assert text == CONF_CANONICAL_RESPONSE
    assert "imperative_procedural_verbs" in reasons


def test_conf_sanitize_code_block_trigger():
    text, did_sanitize, reasons = conf_sanitize("```bash\npython app.py\n```")
    assert did_sanitize is True
    assert text == CONF_CANONICAL_RESPONSE
    assert "code_block" in reasons


def test_conf_sanitize_shell_snippet_trigger():
    text, did_sanitize, reasons = conf_sanitize("$ python train.py")
    assert did_sanitize is True
    assert text == CONF_CANONICAL_RESPONSE
    assert "shell_snippet" in reasons


def test_conf_sanitize_file_path_trigger():
    text, did_sanitize, reasons = conf_sanitize("Open ml/training/pipeline/stage6/stage6c/config/gating_config.yaml")
    assert did_sanitize is True
    assert text == CONF_CANONICAL_RESPONSE
    assert "file_path" in reasons


def test_conf_sanitize_non_procedural_kept():
    text, did_sanitize, reasons = conf_sanitize("I need more context before confirming.")
    assert did_sanitize is False
    assert text == "I need more context before confirming."
    assert reasons == []


def test_should_apply_conf_sanitizer_expected_phase_conf():
    apply_sanitizer, gate_path, expected_phase_seen = should_apply_conf_sanitizer(
        _messages("CONF"),
        expected_phase="CONF",
    )
    assert apply_sanitizer is True
    assert gate_path == "expected_phase_conf"
    assert expected_phase_seen == "CONF"


def test_should_not_apply_conf_sanitizer_non_conf_phase():
    apply_sanitizer, gate_path, expected_phase_seen = should_apply_conf_sanitizer(
        _messages("REF"),
        expected_phase="REF",
    )
    assert apply_sanitizer is False
    assert gate_path == "disabled"
    assert expected_phase_seen == "REF"


def test_should_apply_conf_sanitizer_from_metadata_when_expected_phase_missing():
    apply_sanitizer, gate_path, expected_phase_seen = should_apply_conf_sanitizer(
        _messages("CONF"),
        expected_phase=None,
    )
    assert apply_sanitizer is True
    assert gate_path == "expected_phase_conf"
    assert expected_phase_seen == "CONF"
