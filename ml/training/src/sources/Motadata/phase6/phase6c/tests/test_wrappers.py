"""M3: Wrapper position, origin=wrapper, none when injection_profile_id==none, config no role collision."""
import pytest
from phase6c.loop.runner import build_step_messages
from phase6c.seeds.registry import SeedView
from phase6c.injections.wrapper import apply_wrapper
from phase6c.injections.types import WrapperState
from phase6c.injections.profiles import get_profile, list_profile_ids, CANONICAL_PROFILE_IDS
from phase6c.config.schema import HarnessConfig, CANONICAL_STEP_ROLES


def _make_seed():
    return SeedView(
        seed_id="TEST-SEED",
        governance_system_messages=["gov1"],
        seed_system_messages=["seed_sys1"],
        seed_user_messages=["seed_user1"],
        seed_metadata={"expected_phase": "REF"},
    )


def test_wrappers_inserted_after_seed_before_carryover():
    seed = _make_seed()
    carryover = [{"role": "user", "content": "prior", "origin": "carryover"}]
    messages = build_step_messages(
        seed, 0, "rehydrate", "Proceed.", carryover,
        "run-1", "deadline_squeeze", horizon_N=3, shape="linear",
    )
    origins = [m["origin"] for m in messages]
    idx_seed = max(i for i, o in enumerate(origins) if o == "seed")
    idx_wrapper = [i for i, o in enumerate(origins) if o == "wrapper"]
    idx_carry = next((i for i, o in enumerate(origins) if o == "carryover"), None)
    idx_sq = next(i for i, o in enumerate(origins) if o == "step_query")
    assert idx_wrapper, "at least one wrapper message"
    assert all(idx_seed < w for w in idx_wrapper)
    assert all(w < idx_sq for w in idx_wrapper)
    if idx_carry is not None:
        assert all(w < idx_carry for w in idx_wrapper)


def test_wrapper_messages_have_origin_wrapper():
    state = WrapperState(
        run_id="r1", horizon_N=3, shape="linear", step_index=0, step_role="plan",
        injection_profile_id="authority_ambiguity",
    )
    out = apply_wrapper(state)
    assert len(out) >= 1
    for m in out:
        assert m.get("origin") == "wrapper"
        assert "content" in m


def test_no_wrappers_when_injection_profile_id_none():
    state = WrapperState(
        run_id="r1", horizon_N=3, shape="linear", step_index=0, step_role="plan",
        injection_profile_id="none",
    )
    assert apply_wrapper(state) == []
    state_empty = WrapperState(
        run_id="r1", horizon_N=3, shape="linear", step_index=0, step_role="plan",
        injection_profile_id="",
    )
    assert apply_wrapper(state_empty) == []


def test_build_step_messages_no_wrapper_when_none():
    seed = _make_seed()
    messages = build_step_messages(
        seed, 0, "rehydrate", "Proceed.", [],
        "run-1", "none", horizon_N=3, shape="linear",
    )
    wrapper_count = sum(1 for m in messages if m.get("origin") == "wrapper")
    assert wrapper_count == 0


def test_config_rejects_injection_profile_id_colliding_with_step_role():
    with pytest.raises(ValueError, match="collides with canonical step role"):
        HarnessConfig(
            seeds_dir="/tmp/s",
            injection_profiles=["none", "commit_temptation"],
        )
    with pytest.raises(ValueError, match="collides with canonical step role"):
        HarnessConfig(
            seeds_dir="/tmp/s",
            injection_profiles=["rehydrate"],
        )


def test_canonical_profile_ids_do_not_collide_with_step_roles():
    for pid in CANONICAL_PROFILE_IDS:
        assert pid not in CANONICAL_STEP_ROLES, f"Profile id {pid} must not equal a step role"


def test_unknown_profile_id_raises():
    state = WrapperState(
        run_id="r1", horizon_N=3, shape="linear",
        step_index=0, step_role="plan",
        injection_profile_id="typo_profile",
    )
    with pytest.raises(ValueError):
        apply_wrapper(state)


def test_ship_it_pressure_alias_resolves_to_commit_push():
    p = get_profile("ship_it_pressure")
    assert p is not None
    assert p.id == "commit_push"
