"""
Loop Controller — M3.1 orchestration substrate.

Deterministic transition executor that obeys transition_matrix.v0.1.json.
Integrates ContextEngine (governance_to_context) and SandboxExecutor (validated_to_sandbox).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from runtime.state.store import TaskState, TaskStateStore
from runtime.state.transitions import TransitionResult, TransitionValidator
from runtime.context.contracts import ContextRequest
from runtime.context.engine import ContextEngine, ContextEngineError, MissingExplicitFilesError

try:
    from runtime.sandbox.sandbox_executor import SandboxAction, SandboxExecutor
    from runtime.sandbox.sandbox_errors import SandboxError
    from runtime.sandbox.sandbox_ledger_store import (
        EVENT_PLANGATE_BOUNDED_ALLOW,
        EVENT_PLANGATE_DEFERRED,
        EVENT_PLANGATE_REFUSED,
        EVENT_PLANGATE_SAFE_EXECUTE,
        EVENT_REFUSED,
        SandboxLedgerStore,
    )
    from runtime.plangate.plangate_service import PlanGateService
except ImportError:
    SandboxAction = None  # type: ignore[misc, assignment]
    SandboxExecutor = None  # type: ignore[misc, assignment]
    SandboxError = Exception  # type: ignore[misc, assignment]
    EVENT_REFUSED = "sandbox_refused"  # type: str
    SandboxLedgerStore = None  # type: ignore[misc, assignment]
    EVENT_PLANGATE_REFUSED = "plangate_refused"  # type: str
    EVENT_PLANGATE_DEFERRED = "plangate_deferred"  # type: str
    EVENT_PLANGATE_BOUNDED_ALLOW = "plangate_bounded_allow"  # type: str
    EVENT_PLANGATE_SAFE_EXECUTE = "plangate_safe_execute"  # type: str
    PlanGateService = None  # type: ignore[misc, assignment]


@dataclass
class TransitionJournalEntry:
    """Record of an applied transition for audit/replay."""

    task_id: str
    transition_id: str
    from_state: str
    to_state: str
    timestamp_utc: str
    plan_gate_required: bool
    decision_boundary: bool


class LoopController:
    """
    Deterministic loop executor.

    - Load current state
    - Validate transition against transition_matrix.v0.1.json
    - Apply transition
    - Persist state
    - Emit transition journal entry
    - Refuse invalid transitions
    """

    def __init__(
        self,
        store: TaskStateStore | None = None,
        validator: TransitionValidator | None = None,
        journal_callback: Callable[[TransitionJournalEntry], None] | None = None,
        context_engine: ContextEngine | None = None,
        sandbox_executor: Any = None,
        ledger_store: Any = None,
        plan_gate_service: Any = None,
    ):
        """
        Initialize loop controller.

        Args:
            store: Task state store. If None, create in-memory store.
            validator: Transition validator. If None, load default matrix.
            journal_callback: Optional callback for each applied transition.
            context_engine: Used for governance_to_context transition.
            sandbox_executor: Optional SandboxExecutor for validated_to_sandbox (PROPOSAL_VALIDATED -> SANDBOX_EXECUTED).
            ledger_store: Optional SandboxLedgerStore; when set, refusal/plan-gate rows are persisted.
            plan_gate_service: Optional PlanGateService; when set, validated_to_sandbox requires Plan-Gate approval (safe_execute).
        """
        self.store = store or TaskStateStore()
        self.validator = validator or TransitionValidator()
        self.context_engine = context_engine or ContextEngine()
        self.sandbox_executor = sandbox_executor
        self.ledger_store = ledger_store
        self.plan_gate_service = plan_gate_service
        self.journal_callback = journal_callback
        self._journal: list[TransitionJournalEntry] = []
        self.max_consecutive_same_transition_id = 5
        # NOTE (scaffold): repetition guard is intentionally coarse (transition_id only).
        # Later revisions may need state-aware or phase-aware repetition logic to avoid
        # blocking legitimate repeated transitions in distinct contexts.

    def create_task(
        self,
        task_id: str,
        metadata: dict[str, Any] | None = None,
        *,
        max_iterations: int = 10,
    ) -> TaskState:
        """Create a new task in TASK_RECEIVED state."""
        return self.store.create(task_id, metadata, max_iterations=max_iterations)

    def apply_transition(
        self,
        task_id: str,
        *,
        transition_id: str,
        to_state: str | None = None,
        guard_inputs: dict[str, Any] | None = None,
    ) -> TransitionResult:
        """
        Execute a transition by transition_id from the current state.

        Returns TransitionResult. If valid, applies transition, persists,
        and emits journal entry. If invalid, refuses and returns result with valid=False.
        """
        state = self.store.load(task_id)
        if not state:
            return TransitionResult(
                valid=False,
                transition_id=transition_id,
                to_state=to_state,
                reason=f"Task not found: {task_id}",
            )

        from_state = state.current_state

        if self.validator.is_terminal(from_state):
            return TransitionResult(
                valid=False,
                transition_id=transition_id,
                from_state=from_state,
                to_state=to_state,
                reason=f"Cannot transition from terminal state: {from_state}",
            )

        guard_inputs = guard_inputs or {}

        # Resolve transition (supports transition_id-based execution).
        resolved = self.validator.resolve_by_transition_id(from_state, transition_id, to_state=to_state)
        if not resolved.valid:
            return resolved

        # Reject no-op transitions unless explicitly defined in matrix.
        if resolved.from_state == resolved.to_state:
            # resolve_by_transition_id() delegates to validate(), so this is explicitly defined.
            # Still refuse if caller attempted a no-op via implicit to_state mismatch.
            pass

        # Evaluate guards from matrix (fail-closed).
        ok, guard_reason = self.validator.guards_satisfied(transition_id, from_state, guard_inputs)
        if not ok:
            return TransitionResult(
                valid=False,
                transition_id=transition_id,
                from_state=from_state,
                to_state=resolved.to_state,
                stop_reason="validation_failed",
                reason=guard_reason,
            )

        # Loop safety guard: retry iteration cap.
        # NOTE (scaffold): iteration budget currently applies to retry-path transitions only.
        is_retry = transition_id == "review_to_proposal"
        if is_retry and state.loop_iteration >= state.max_iterations:
            return TransitionResult(
                valid=False,
                transition_id=transition_id,
                from_state=from_state,
                to_state=resolved.to_state,
                stop_reason="iteration_limit",
                reason=f"Iteration limit reached: {state.loop_iteration} >= {state.max_iterations}",
            )

        # Loop safety guard: excessive repetition of same transition_id.
        if state.last_transition_id == transition_id:
            if state.consecutive_same_transition_id + 1 > self.max_consecutive_same_transition_id:
                return TransitionResult(
                    valid=False,
                    transition_id=transition_id,
                    from_state=from_state,
                    to_state=resolved.to_state,
                    stop_reason="iteration_limit",
                    reason=(
                        "Excessive consecutive repetition of transition_id "
                        f"{transition_id} (limit {self.max_consecutive_same_transition_id})"
                    ),
                )

        # NOTE (scaffold): when a loop guard blocks progression (iteration_limit, repetition),
        # we return an explicit stop_reason but do not force a terminal state transition yet.
        # Later orchestration may convert these into explicit runtime-owned terminal transitions
        # (e.g., REVIEW_DECIDED -> BLOCKED with stop_reason=iteration_limit) when such transitions
        # are added to the transition matrix.

        # If this is the GOVERNANCE_CLASSIFIED -> CONTEXT_FETCHED path, invoke ContextEngine
        # before applying the transition, so that CONTEXT_FETCHED implies a context bundle
        # has been constructed and persisted.
        if transition_id == "governance_to_context":
            try:
                self._attach_context_bundle(task_id, state)
            except (ContextEngineError, MissingExplicitFilesError) as e:
                return TransitionResult(
                    valid=False,
                    transition_id=transition_id,
                    from_state=from_state,
                    to_state=resolved.to_state,
                    stop_reason="validation_failed",
                    reason=str(e),
                )

        # If this is PROPOSAL_VALIDATED -> SANDBOX_EXECUTED, Plan-Gate must approve before sandbox (M3.3).
        if transition_id == "validated_to_sandbox":
            # Plan-Gate: mandatory gate; no execution path may bypass.
            pg_request = {
                "request_id": task_id,
                "plan_hash": (state.metadata or {}).get("plan_hash", ""),
                "command": guard_inputs.get("command"),
                "plan_gate_defer": guard_inputs.get("plan_gate_defer"),
                "plan_gate_refuse": guard_inputs.get("plan_gate_refuse"),
                "plan_gate_bounded_allow": guard_inputs.get("plan_gate_bounded_allow"),
            }
            if self.plan_gate_service is None or PlanGateService is None:
                err = "Plan-Gate not configured; execution path must not bypass Plan-Gate"
                lid_val, res = self._apply_plangate_refusal(
                    task_id, state, transition_id, from_state, resolved, err
                )
                if res is not None:
                    return res
                return TransitionResult(
                    valid=False,
                    transition_id=transition_id,
                    from_state=from_state,
                    to_state=resolved.to_state,
                    stop_reason="validation_failed",
                    reason=err,
                    ledger_row_id=lid_val,
                )
            decision = self.plan_gate_service.evaluate(pg_request)
            # Persist Plan-Gate decision to ledger (linkage via request_id).
            lid_pg = self._persist_plangate_decision(task_id, state, decision)
            if decision.posture == "refuse":
                err = decision.reason or "Plan-Gate refused"
                _, res = self._apply_plangate_refusal(task_id, state, transition_id, from_state, resolved, err)
                if res is not None:
                    return res
                return TransitionResult(
                    valid=False,
                    transition_id=transition_id,
                    from_state=from_state,
                    to_state=resolved.to_state,
                    stop_reason="validation_failed",
                    reason=err,
                    ledger_row_id=lid_pg,
                )
            if decision.posture == "defer":
                reason = decision.reason or "deferred"
                return TransitionResult(
                    valid=False,
                    transition_id=transition_id,
                    from_state=from_state,
                    to_state=resolved.to_state,
                    stop_reason="deferred",
                    reason=reason,
                    ledger_row_id=lid_pg,
                )
            if decision.posture == "bounded_allow":
                reason = decision.reason or "bounded_allow"
                return TransitionResult(
                    valid=False,
                    transition_id=transition_id,
                    from_state=from_state,
                    to_state=resolved.to_state,
                    stop_reason="bounded_allow",
                    reason=reason,
                    ledger_row_id=lid_pg,
                )
            # safe_execute: proceed to sandbox.
            err = self._run_sandbox_and_persist(task_id, state, guard_inputs)
            if err:
                ledger_row_id_val: str | None = None
                if self.ledger_store and SandboxLedgerStore is not None:
                    plan_hash_val = (state.metadata or {}).get("plan_hash", "")
                    lid = f"refused-{task_id}-{hashlib.sha256((err + plan_hash_val + transition_id).encode()).hexdigest()[:16]}"
                    payload = {
                        "outcome_type": "refused",
                        "request_id": task_id,
                        "plan_hash": plan_hash_val,
                        "refusal_reason": err,
                        "transition_id": transition_id,
                    }
                    try:
                        self.ledger_store.append(
                            ledger_row_id=lid,
                            event_type=EVENT_REFUSED,
                            outcome_type="refused",
                            request_id=task_id,
                            plan_hash=plan_hash_val,
                            sandbox_id="",
                            payload=payload,
                        )
                        ledger_row_id_val = lid
                    except Exception as e:
                        return TransitionResult(
                            valid=False,
                            transition_id=transition_id,
                            from_state=from_state,
                            to_state=resolved.to_state,
                            stop_reason="validation_failed",
                            reason=err + "; refusal evidence could not be persisted: " + str(e),
                            ledger_row_id=None,
                        )
                return TransitionResult(
                    valid=False,
                    transition_id=transition_id,
                    from_state=from_state,
                    to_state=resolved.to_state,
                    stop_reason="validation_failed",
                    reason=err,
                    ledger_row_id=ledger_row_id_val,
                )

        to_state_final = resolved.to_state or ""

        # Apply transition.
        state.current_state = to_state_final

        # Update loop counters (retry increments).
        if is_retry:
            state.loop_iteration += 1

        # Update repetition tracking.
        if state.last_transition_id == transition_id:
            state.consecutive_same_transition_id += 1
        else:
            state.last_transition_id = transition_id
            state.consecutive_same_transition_id = 1

        timestamp = datetime.now(timezone.utc).isoformat()
        state.transition_journal.append(
            {
                "transition_id": transition_id,
                "from_state": from_state,
                "to_state": to_state_final,
                "timestamp_utc": timestamp,
            }
        )
        self.store.save(state)

        entry = TransitionJournalEntry(
            task_id=task_id,
            transition_id=transition_id,
            from_state=from_state,
            to_state=to_state_final,
            timestamp_utc=timestamp,
            plan_gate_required=resolved.plan_gate_required,
            decision_boundary=resolved.decision_boundary,
        )
        self._journal.append(entry)
        if self.journal_callback:
            self.journal_callback(entry)

        return resolved

    def get_journal(self) -> list[TransitionJournalEntry]:
        """Return journal of applied transitions for this controller instance."""
        return list(self._journal)

    def _persist_plangate_decision(
        self, task_id: str, state: TaskState, decision: Any
    ) -> str | None:
        """Persist Plan-Gate decision to ledger. Returns ledger_row_id or None."""
        if not self.ledger_store or SandboxLedgerStore is None:
            return None
        plan_hash_val = (state.metadata or {}).get("plan_hash", "")
        posture = getattr(decision, "posture", "safe_execute")
        event_type = {
            "refuse": EVENT_PLANGATE_REFUSED,
            "defer": EVENT_PLANGATE_DEFERRED,
            "bounded_allow": EVENT_PLANGATE_BOUNDED_ALLOW,
            "safe_execute": EVENT_PLANGATE_SAFE_EXECUTE,
        }.get(posture, EVENT_PLANGATE_SAFE_EXECUTE)
        payload = {
            "request_id": task_id,
            "plan_hash": plan_hash_val,
            "decision_posture": posture,
            "reason": getattr(decision, "reason", ""),
        }
        if hasattr(decision, "to_dict"):
            payload.update(decision.to_dict())
        lid = f"plangate-{task_id}-{posture}-{hashlib.sha256(str(payload).encode()).hexdigest()[:12]}"
        try:
            self.ledger_store.append(
                ledger_row_id=lid,
                event_type=event_type,
                outcome_type=posture,
                request_id=task_id,
                plan_hash=plan_hash_val,
                sandbox_id="",
                payload=payload,
            )
            return lid
        except Exception:
            return None

    def _apply_plangate_refusal(
        self,
        task_id: str,
        state: TaskState,
        transition_id: str,
        from_state: str,
        resolved: TransitionResult,
        err: str,
    ) -> tuple[str | None, TransitionResult | None]:
        """Persist refusal row; return (ledger_row_id, None) on success, (None, TransitionResult) on persistence failure."""
        ledger_row_id_val: str | None = None
        if self.ledger_store and SandboxLedgerStore is not None:
            plan_hash_val = (state.metadata or {}).get("plan_hash", "")
            lid = f"refused-{task_id}-{hashlib.sha256((err + plan_hash_val + transition_id).encode()).hexdigest()[:16]}"
            payload = {
                "outcome_type": "refused",
                "request_id": task_id,
                "plan_hash": plan_hash_val,
                "refusal_reason": err,
                "transition_id": transition_id,
            }
            try:
                self.ledger_store.append(
                    ledger_row_id=lid,
                    event_type=EVENT_REFUSED,
                    outcome_type="refused",
                    request_id=task_id,
                    plan_hash=plan_hash_val,
                    sandbox_id="",
                    payload=payload,
                )
                ledger_row_id_val = lid
            except Exception as e:
                return (
                    None,
                    TransitionResult(
                        valid=False,
                        transition_id=transition_id,
                        from_state=from_state,
                        to_state=resolved.to_state,
                        stop_reason="validation_failed",
                        reason=err + "; refusal evidence could not be persisted: " + str(e),
                        ledger_row_id=None,
                    ),
                )
        return (ledger_row_id_val, None)

    def _run_sandbox_and_persist(
        self, task_id: str, state: TaskState, guard_inputs: dict[str, Any]
    ) -> str | None:
        """
        Run sandbox for validated_to_sandbox transition and persist result in state.metadata.

        guard_inputs must contain:
        - command: list[str]
        - working_dir: str | Path

        Optional: timeout_seconds, env.
        Persists last_sandbox_success and last_sandbox_ledger_id for downstream guards.
        Returns error message string on failure, None on success.
        """
        if self.sandbox_executor is None or SandboxAction is None:
            return "Sandbox executor not configured for PROPOSAL_VALIDATED -> SANDBOX_EXECUTED"
        command = guard_inputs.get("command")
        working_dir = guard_inputs.get("working_dir") or state.metadata.get("working_dir")
        if not command or not isinstance(command, list):
            return "guard_inputs must provide command (list[str]) for validated_to_sandbox"
        if not working_dir:
            return "guard_inputs must provide working_dir for validated_to_sandbox"
        working_dir = Path(working_dir) if isinstance(working_dir, str) else working_dir
        action = SandboxAction(
            task_id=task_id,
            command=command,
            working_dir=working_dir,
            timeout_seconds=guard_inputs.get("timeout_seconds"),
            env=guard_inputs.get("env"),
            metadata=state.metadata,
        )
        try:
            result = self.sandbox_executor.execute_sandbox_action(action)
        except SandboxError as e:
            return str(e)
        meta = state.metadata or {}
        meta["last_sandbox_success"] = result.success
        meta["last_sandbox_ledger_id"] = result.ledger_row_id or ""
        state.metadata = meta
        return None

    def _build_context_request(self, task_id: str, state: TaskState) -> ContextRequest:
        """
        Construct a ContextRequest from TaskState metadata.

        Expected metadata keys:
        - root_path or repo_root
        - revision (optional; defaults to 'unknown-revision')
        - context_files (optional list[str])
        - symbol_hints (optional list[str])
        - context_max_files (optional int)
        - context_max_bytes (optional int)
        - context_selectors (optional list[str])
        """
        meta = state.metadata or {}
        root_path = meta.get("root_path") or meta.get("repo_root")
        if not root_path:
            raise ContextEngineError("Missing root_path/repo_root in task metadata for context engine")

        revision = str(meta.get("revision", "unknown-revision"))
        files = list(meta.get("context_files", []))
        symbol_hints = list(meta.get("symbol_hints", []))
        max_files = int(meta.get("context_max_files", 50))
        max_bytes = int(meta.get("context_max_bytes", 512_000))
        selectors = list(meta.get("context_selectors", ["direct", "siblings", "imports", "symbols"]))

        return ContextRequest(
            task_id=task_id,
            revision=revision,
            root_path=str(root_path),
            files=files,
            symbol_hints=symbol_hints,
            max_files=max_files,
            max_bytes=max_bytes,
            selectors=selectors,
        )

    def _attach_context_bundle(self, task_id: str, state: TaskState) -> None:
        """
        Build a context bundle via ContextEngine and persist minimal metadata into task state.

        Persisted metadata (under metadata['context_bundle']):
        - bundle_id (deterministic hash of revision, paths, truncated)
        - revision
        - paths
        - truncated
        """
        request = self._build_context_request(task_id, state)
        bundle = self.context_engine.build_context_bundle(request)

        paths = [item.path for item in bundle.items]
        info = {
            "task_id": bundle.task_id,
            "revision": bundle.revision,
            "paths": paths,
            "truncated": bundle.limits.truncated,
        }
        bundle_id = hashlib.sha256(
            json.dumps(info, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()

        meta = state.metadata or {}
        meta["context_bundle"] = {
            "bundle_id": bundle_id,
            **info,
        }
        state.metadata = meta
