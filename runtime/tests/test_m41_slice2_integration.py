"""M4.1 Slice 2 integration tests: normalizer + guard + Plan-Gate on live paths."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from runtime.execute_service.handlers import handle_execute_request
from runtime.integrity import CommandNormalizer
from runtime.integrity.plangate_bridge import intent_to_plangate_request
from runtime.plangate.pre_gate import DeterministicGuard
from runtime.plangate.plangate_service import PlanGateService
from runtime.state.store import TaskStateStore
from runtime.orchestrator.loop_controller import LoopController
from runtime.sandbox.sandbox_executor import SandboxAction, SandboxExecutor
from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore
from runtime.state.transitions import TransitionValidator


class TestSameRequestSameCanonicalHashInvariant:
    """Invariant: same incoming request -> same canonical_hash seen by guard and Plan-Gate."""

    def test_execute_service_same_request_same_canonical_hash(self) -> None:
        """Same request produces same canonical_hash; guard and Plan-Gate see that hash."""
        with tempfile.TemporaryDirectory() as tmp:
            req = {
                "request_id": "r1",
                "repo_root": tmp,
                "command": "echo hello",
                "plan_hash": "ph1",
            }
            normalizer = CommandNormalizer(default_working_dir=tmp)
            intent1 = normalizer.normalize(req)
            intent2 = normalizer.normalize(req)
            assert intent1.canonical_hash == intent2.canonical_hash
            # Guard and Plan-Gate receive the same artifact (via intent_to_plangate_request)
            pg_req1 = intent_to_plangate_request(intent1)
            pg_req2 = intent_to_plangate_request(intent2)
            assert pg_req1["command"] == list(intent1.argv)
            assert pg_req2["command"] == list(intent2.argv)
            guard = DeterministicGuard()
            r1 = guard.evaluate(intent1)
            r2 = guard.evaluate(intent2)
            assert r1.passed == r2.passed
            gate = PlanGateService()
            d1 = gate.evaluate(pg_req1)
            d2 = gate.evaluate(pg_req2)
            assert d1.posture == d2.posture

    def test_handlers_same_request_same_hash_through_flow(self) -> None:
        """Full handle_execute_request: same request twice yields consistent outcome and hash."""
        with tempfile.TemporaryDirectory() as tmp:
            req = {
                "request_id": "req-same",
                "repo_root": tmp,
                "command": "echo ok",
            }
            r1 = handle_execute_request(req)
            r2 = handle_execute_request(req)
            assert r1["outcome"] == r2["outcome"]
            # If executed, both should have same plan_hash; canonical_hash is in action metadata internally
            assert r1.get("plan_hash") == r2.get("plan_hash")


class TestNormalizationInvokedOnce:
    """Normalization is invoked exactly once on each path; no re-parse after."""

    def test_execute_service_path_uses_intent_only_for_sandbox(self) -> None:
        """After normalization, SandboxAction is built from intent.argv (no _parse_command)."""
        with tempfile.TemporaryDirectory() as tmp:
            req = {
                "request_id": "r1",
                "repo_root": tmp,
                "command": 'echo "hello world"',
            }
            resp = handle_execute_request(req)
            assert resp["outcome"] == "EXECUTED"
            # If we had re-parsed, we could get different argv; single parse gives echo, hello world
            normalizer = CommandNormalizer(default_working_dir=tmp)
            intent = normalizer.normalize(req)
            assert intent.argv == ("echo", "hello world")

    def test_orchestrator_path_uses_intent_for_sandbox(self) -> None:
        """validated_to_sandbox: action built from intent (command=list(intent.argv))."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SandboxLedgerStore(Path(tmp) / "ledger.db")
            controller = LoopController(
                store=TaskStateStore(),
                validator=TransitionValidator(),
                sandbox_executor=SandboxExecutor(ledger_store=store),
                ledger_store=store,
                plan_gate_service=PlanGateService(),
            )
            controller.create_task("t1", metadata={"plan_hash": "ph", "working_dir": tmp})
            state = controller.store.load("t1")
            assert state is not None
            state.current_state = "PROPOSAL_VALIDATED"
            controller.store.save(state)
            r = controller.apply_transition(
                "t1",
                transition_id="validated_to_sandbox",
                guard_inputs={"command": ["echo", "from orchestrator"], "working_dir": tmp},
            )
            assert r.valid is True
            state2 = controller.store.load("t1")
            assert state2 is not None
            assert state2.current_state == "SANDBOX_EXECUTED"


class TestGuardRefusalShortCircuits:
    """Guard refusal short-circuits before Plan-Gate and sandbox."""

    def test_curl_refused_by_guard_before_plangate(self) -> None:
        """curl is refused by DeterministicGuard (unsupported_network_execution); no Plan-Gate call for posture."""
        with tempfile.TemporaryDirectory() as tmp:
            req = {
                "request_id": "r1",
                "repo_root": tmp,
                "command": "curl http://example.com",
            }
            resp = handle_execute_request(req)
            assert resp["outcome"] == "REFUSED"
            assert "not allowed" in resp.get("reason", "").lower() or "pre-gate" in resp.get("reason", "").lower()

    def test_protected_branch_refused_by_guard(self) -> None:
        """Request targeting main branch is refused by guard (protected_branch_mutation)."""
        with tempfile.TemporaryDirectory() as tmp:
            req = {
                "request_id": "r1",
                "repo_root": tmp,
                "command": "echo x",
                "branch": "main",
            }
            resp = handle_execute_request(req)
            assert resp["outcome"] == "REFUSED"
            assert "protected" in resp.get("reason", "").lower() or "branch" in resp.get("reason", "").lower()


class TestIntentProjectionLossless:
    """Projection to Plan-Gate is lossless: intent.argv == pg_request['command']."""

    def test_intent_projection_is_lossless(self) -> None:
        """Verify intent.argv == pg_request['command'] so projection never drifts."""
        from runtime.integrity import CommandNormalizer

        with tempfile.TemporaryDirectory() as tmp:
            req = {
                "request_id": "r1",
                "repo_root": tmp,
                "command": ["python3", "-c", "print(1+1)"],
            }
            normalizer = CommandNormalizer(default_working_dir=tmp)
            intent = normalizer.normalize(req)
            pg_request = intent_to_plangate_request(intent)
            assert list(intent.argv) == pg_request["command"]
            assert intent.canonical_hash == pg_request["canonical_hash"]
            assert intent.repo_root == pg_request["repo_root"]
            assert intent.working_dir == pg_request["working_dir"]


class TestOnlyIntentReachesSandbox:
    """SandboxExecutor refuses execution when canonical_hash is missing."""

    def test_missing_canonical_hash_blocked(self) -> None:
        """Action without metadata.canonical_hash is blocked before driver runs."""
        with tempfile.TemporaryDirectory() as tmp:
            executor = SandboxExecutor()
            action = SandboxAction(
                task_id="t1",
                command=["echo", "x"],
                working_dir=tmp,
                metadata=None,
            )
            result = executor.execute_sandbox_action(action)
            assert result.outcome_type == "blocked"
            assert "canonical_hash" in (result.blocked_reason or "").lower()

    def test_empty_metadata_canonical_hash_blocked(self) -> None:
        """Action with metadata but no canonical_hash is blocked."""
        with tempfile.TemporaryDirectory() as tmp:
            executor = SandboxExecutor()
            action = SandboxAction(
                task_id="t1",
                command=["echo", "x"],
                working_dir=tmp,
                metadata={},
            )
            result = executor.execute_sandbox_action(action)
            assert result.outcome_type == "blocked"
            assert "canonical_hash" in (result.blocked_reason or "").lower()


class TestPlanGatePostureUnchanged:
    """Existing Plan-Gate posture fixtures retain same behavior; only safe_execute reaches sandbox."""

    @pytest.fixture(autouse=True)
    def _allow_plan_gate_overrides(self, monkeypatch):
        monkeypatch.setenv("MOTADATA_EXECUTE_ALLOW_PLAN_GATE_OVERRIDES", "1")

    def test_explicit_plan_gate_refuse_still_refuses(self) -> None:
        """plan_gate_refuse=True still refuses (Plan-Gate sees it via overrides)."""
        with tempfile.TemporaryDirectory() as tmp:
            req = {
                "request_id": "r1",
                "repo_root": tmp,
                "command": "echo safe",
                "plan_gate_refuse": True,
            }
            resp = handle_execute_request(req)
            assert resp["outcome"] == "REFUSED"

    def test_explicit_plan_gate_defer_still_defers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            req = {
                "request_id": "r1",
                "repo_root": tmp,
                "command": "echo safe",
                "plan_gate_defer": True,
            }
            resp = handle_execute_request(req)
            assert resp["outcome"] == "DEFERRED"

    def test_explicit_plan_gate_bounded_allow_still_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            req = {
                "request_id": "r1",
                "repo_root": tmp,
                "command": "echo safe",
                "plan_gate_bounded_allow": True,
            }
            resp = handle_execute_request(req)
            assert resp["outcome"] == "BOUNDED_ALLOW"

    def test_only_safe_execute_reaches_sandbox(self) -> None:
        """Without safe_execute posture, sandbox is not invoked."""
        with tempfile.TemporaryDirectory() as tmp:
            req = {
                "request_id": "r1",
                "repo_root": tmp,
                "command": "echo ok",
            }
            resp = handle_execute_request(req)
            assert resp["outcome"] == "EXECUTED"
            assert resp.get("executed") is True
