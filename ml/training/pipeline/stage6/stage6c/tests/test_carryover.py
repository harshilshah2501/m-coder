"""Test carryover modes and full_transcript_policy."""
import pytest
from stage6.stage6c.loop.carryover import get_carryover_messages

def test_cold_start_empty():
    assert get_carryover_messages("cold_start", 0, []) == []
    assert get_carryover_messages("cold_start", 2, [{"prompt_messages": [], "response": {"content": "x"}}]) == []

def test_full_transcript_empty_for_step_0():
    assert get_carryover_messages("full_transcript", 0, []) == []

def test_full_transcript_includes_prior_steps_in_order():
    step_history = [
        {"prompt_messages": [{"role": "user", "content": "query1", "origin": "step_query"}], "response": {"content": "response1"}},
        {"prompt_messages": [{"role": "user", "content": "query2", "origin": "step_query"}], "response": {"content": "response2"}},
    ]
    messages = get_carryover_messages("full_transcript", 2, step_history)
    assert len(messages) == 4
    assert messages[0]["role"] == "user" and messages[0]["content"] == "query1" and messages[0]["origin"] == "carryover"
    assert messages[1]["role"] == "assistant" and messages[1]["content"] == "response1"
    assert messages[2]["role"] == "user" and messages[2]["content"] == "query2"
    assert messages[3]["role"] == "assistant" and messages[3]["content"] == "response2"

def test_full_transcript_policy_step_query_only_no_wrapper_replay():
    """step_query_only: only step_query and assistant; no wrapper-origin messages in carryover."""
    step_history = [
        {
            "prompt_messages": [
                {"role": "user", "content": "injected wrapper", "origin": "wrapper"},
                {"role": "user", "content": "query1", "origin": "step_query"},
            ],
            "response": {"content": "response1"},
        },
    ]
    messages = get_carryover_messages("full_transcript", 1, step_history, full_transcript_policy="step_query_only")
    assert len(messages) == 2
    assert messages[0]["content"] == "query1" and messages[0]["origin"] == "carryover"
    assert messages[1]["content"] == "response1" and messages[1]["origin"] == "carryover"
    contents = [m["content"] for m in messages]
    assert "injected wrapper" not in contents

def test_full_transcript_policy_include_wrappers_wrapper_in_order():
    """include_wrappers: wrapper-origin messages from prior steps appear in carryover in chronological order."""
    step_history = [
        {
            "prompt_messages": [
                {"role": "user", "content": "wrap1", "origin": "wrapper"},
                {"role": "user", "content": "query1", "origin": "step_query"},
            ],
            "response": {"content": "response1"},
        },
        {
            "prompt_messages": [
                {"role": "user", "content": "wrap2", "origin": "wrapper"},
                {"role": "user", "content": "query2", "origin": "step_query"},
            ],
            "response": {"content": "response2"},
        },
    ]
    messages = get_carryover_messages("full_transcript", 2, step_history, full_transcript_policy="include_wrappers")
    assert all(m.get("origin") == "carryover" for m in messages)
    contents = [m["content"] for m in messages]
    expected_order = ["wrap1", "query1", "response1", "wrap2", "query2", "response2"]
    assert contents == expected_order

def test_summary_compressed_raises():
    with pytest.raises(NotImplementedError, match="summary_compressed"):
        get_carryover_messages("summary_compressed", 0, [])


def test_full_transcript_saturated_includes_same_semantics_with_filler():
    """Saturated mode includes prior turns plus deterministic filler between them; origins remain carryover."""
    step_history = [
        {
            "prompt_messages": [
                {"role": "user", "content": "wrap1", "origin": "wrapper"},
                {"role": "user", "content": "query1", "origin": "step_query"},
            ],
            "response": {"content": "response1"},
        },
        {
            "prompt_messages": [
                {"role": "user", "content": "wrap2", "origin": "wrapper"},
                {"role": "user", "content": "query2", "origin": "step_query"},
            ],
            "response": {"content": "response2"},
        },
    ]
    messages = get_carryover_messages(
        "full_transcript_saturated", 2, step_history, full_transcript_policy="include_wrappers"
    )
    assert all(m.get("origin") == "carryover" for m in messages)
    contents = [m["content"] for m in messages]
    assert "wrap1" in contents
    assert "query1" in contents
    assert "response1" in contents
    assert "wrap2" in contents
    assert "query2" in contents
    assert "response2" in contents
    # Filler block inserted between step 0 and step 1
    assert any("saturation simulation" in c for c in contents)
