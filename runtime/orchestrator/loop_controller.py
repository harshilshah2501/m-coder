"""
Loop Controller — M3.1 orchestration substrate.

Deterministic transition executor that obeys transition_matrix.v0.1.json.
No model calls. No sandbox. Just state load, validate, apply, persist, journal.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Callable

from runtime.state.store import TaskState, TaskStateStore
from runtime.state.transitions import TransitionResult, TransitionValidator
from runtime.context.contracts import ContextRequest
from runtime.context.engine import ContextEngine, ContextEngineError, MissingExplicitFilesError


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
    ):
        """
        Initialize loop controller.

        Args:
            store: Task state store. If None, create in-memory store.
            validator: Transition validator. If None, load default matrix.
            journal_callback: Optional callback for each applied transition.
        """
        self.store = store or TaskStateStore()
        self.validator = validator or TransitionValidator()
        self.context_engine = context_engine or ContextEngine()
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
