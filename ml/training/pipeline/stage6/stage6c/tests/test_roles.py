"""Test step role schedules."""
import pytest
from stage6.stage6c.loop.roles import get_step_role_schedule, CANONICAL_STEP_ROLES

def test_canonical_roles_fixed():
    assert CANONICAL_STEP_ROLES == frozenset({"rehydrate", "plan", "act_proposal", "retry", "pressure_escalation", "commit_temptation"})

def test_n3_linear():
    assert get_step_role_schedule(3, "linear") == ["rehydrate", "plan", "act_proposal"]

def test_n4_linear():
    assert get_step_role_schedule(4, "linear") == ["rehydrate", "plan", "act_proposal", "commit_temptation"]

def test_n6_linear():
    got = get_step_role_schedule(6, "linear")
    assert got == ["rehydrate", "plan", "act_proposal", "pressure_escalation", "retry", "commit_temptation"]

def test_n3_retry_biased():
    schedule = get_step_role_schedule(3, "retry_biased")
    assert len(schedule) == 3
    assert "retry" in schedule or "pressure_escalation" in schedule

def test_n6_retry_biased():
    schedule = get_step_role_schedule(6, "retry_biased")
    assert len(schedule) == 6
    assert "retry" in schedule
    assert "pressure_escalation" in schedule

def test_override_valid():
    override = ["rehydrate", "plan", "act_proposal"]
    assert get_step_role_schedule(3, "linear", step_role_sequence_override=override) == override


def test_override_invalid_role_rejected():
    with pytest.raises(ValueError, match="Unknown step role"):
        get_step_role_schedule(3, "linear", step_role_sequence_override=["rehydrate", "plan", "invalid_role"])


def test_override_wrong_length_rejected():
    with pytest.raises(ValueError, match="length must be"):
        get_step_role_schedule(3, "linear", step_role_sequence_override=["rehydrate", "plan"])


def test_invalid_n_or_shape():
    with pytest.raises(ValueError):
        get_step_role_schedule(5, "linear")
    with pytest.raises(ValueError):
        get_step_role_schedule(3, "unknown_shape")
