"""Test message ordering: governance -> seed -> wrappers -> carryover -> step_query via origin tags."""
from phase6c.loop.runner import build_step_messages
from phase6c.seeds.registry import SeedView


def _make_seed():
    return SeedView(
        seed_id="TEST-SEED",
        governance_system_messages=["gov1"],
        seed_system_messages=["seed_sys1"],
        seed_user_messages=["seed_user1"],
        seed_metadata={"expected_phase": "REF"},
    )


def test_ordering_governance_then_seed_then_carryover_then_step_query():
    seed = _make_seed()
    messages = build_step_messages(
        seed, 0, "rehydrate", "Proceed.", [], "run-1", "none", horizon_N=3, shape="linear"
    )
    origins = [m["origin"] for m in messages]
    assert origins[0] == "governance"
    assert origins[-1] == "step_query"
    idx_g = next(i for i, o in enumerate(origins) if o == "governance")
    idx_s = next(i for i, o in enumerate(origins) if o == "seed")
    idx_q = next(i for i, o in enumerate(origins) if o == "step_query")
    assert idx_g < idx_s < idx_q


def test_ordering_with_carryover():
    seed = _make_seed()
    carryover = [
        {"role": "user", "content": "prior user", "origin": "carryover"},
        {"role": "assistant", "content": "prior asst", "origin": "carryover"},
    ]
    messages = build_step_messages(
        seed, 1, "plan", "Step 2 query.", carryover, "run-1", "none", horizon_N=3, shape="linear"
    )
    origins = [m["origin"] for m in messages]
    assert sum(1 for o in origins if o == "carryover") == 2
    assert sum(1 for o in origins if o == "step_query") == 1
    first_carry = next(i for i, o in enumerate(origins) if o == "carryover")
    first_sq = next(i for i, o in enumerate(origins) if o == "step_query")
    assert first_carry < first_sq


def test_ordering_with_wrapper_between_seed_and_carryover():
    seed = _make_seed()
    carryover = [{"role": "user", "content": "prior", "origin": "carryover"}]
    messages = build_step_messages(
        seed, 0, "plan", "Proceed.", carryover, "run-1", "deadline_squeeze",
        horizon_N=3, shape="linear",
    )
    origins = [m["origin"] for m in messages]
    idx_seed = max(i for i, o in enumerate(origins) if o == "seed")
    idx_wrapper = next((i for i, o in enumerate(origins) if o == "wrapper"), None)
    idx_carry = next((i for i, o in enumerate(origins) if o == "carryover"), None)
    idx_sq = next(i for i, o in enumerate(origins) if o == "step_query")
    assert idx_wrapper is not None
    assert idx_seed < idx_wrapper < idx_sq
    if idx_carry is not None:
        assert idx_wrapper < idx_carry


def test_step_query_has_metadata_for_dummy():
    seed = _make_seed()
    messages = build_step_messages(
        seed, 2, "act_proposal", "Proceed.", [], "run-42", "none", horizon_N=3, shape="linear"
    )
    step_query_msg = [m for m in messages if m["origin"] == "step_query"][0]
    assert step_query_msg.get("metadata", {}).get("run_id") == "run-42"
    assert step_query_msg.get("metadata", {}).get("step_index") == 2
    assert step_query_msg.get("metadata", {}).get("step_role") == "act_proposal"
