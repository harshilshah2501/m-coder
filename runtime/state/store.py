"""
Task State Store — M3.1 orchestration substrate.

Persists agent loop state for deterministic replay and audit.

Requirements:
- Deterministic file-backed JSON storage is acceptable
- Persist current task state
- Persist transition journal entries
- Use sorted JSON serialization
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class TaskState:
    """Current state of a task in the agent loop."""

    task_id: str
    current_state: str
    created_at: str
    updated_at: str
    loop_iteration: int
    max_iterations: int
    last_transition_id: str | None = None
    consecutive_same_transition_id: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    transition_journal: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TaskState:
        return cls(
            task_id=d["task_id"],
            current_state=d["current_state"],
            created_at=d["created_at"],
            updated_at=d["updated_at"],
            loop_iteration=int(d.get("loop_iteration", 0)),
            max_iterations=int(d.get("max_iterations", 10)),
            last_transition_id=d.get("last_transition_id"),
            consecutive_same_transition_id=int(d.get("consecutive_same_transition_id", 0)),
            metadata=d.get("metadata", {}),
            transition_journal=d.get("transition_journal", []),
        )


INITIAL_STATE = "TASK_RECEIVED"


class TaskStateStore:
    """
    Persistent store for task state.

    In-memory by default; can persist to JSON files for replay/audit.
    """

    def __init__(self, base_path: Path | str | None = None):
        """
        Initialize store.

        Args:
            base_path: If set, persist task state to JSON files under this path.
                       If None, use in-memory only.
        """
        self.base_path = Path(base_path) if base_path else None
        self._memory: dict[str, TaskState] = {}

    def load(self, task_id: str) -> TaskState | None:
        """Load task state by id. Returns None if not found."""
        if self.base_path:
            path = self.base_path / f"{task_id}.json"
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                state = TaskState.from_dict(data)
                # Keep in-memory view consistent with persisted view for long-lived processes.
                self._memory[task_id] = state
                return state
        return self._memory.get(task_id)

    def save(self, state: TaskState) -> None:
        """Persist task state."""
        now = datetime.now(timezone.utc).isoformat()
        state.updated_at = now
        if self.base_path:
            path = self.base_path / f"{state.task_id}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(state.to_dict(), indent=2, sort_keys=True),
                encoding="utf-8",
            )
        self._memory[state.task_id] = state

    def create(
        self,
        task_id: str,
        metadata: dict[str, Any] | None = None,
        *,
        max_iterations: int = 10,
    ) -> TaskState:
        """Create a new task in TASK_RECEIVED state."""
        now = datetime.now(timezone.utc).isoformat()
        state = TaskState(
            task_id=task_id,
            current_state=INITIAL_STATE,
            created_at=now,
            updated_at=now,
            loop_iteration=0,
            max_iterations=max_iterations,
            last_transition_id=None,
            consecutive_same_transition_id=0,
            metadata=metadata or {},
            transition_journal=[],
        )
        self.save(state)
        return state

    def is_terminal(self, state: str, terminal_states: list[str]) -> bool:
        """Check if state is terminal (non-escaping)."""
        return state in terminal_states
