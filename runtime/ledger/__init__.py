"""
Ledger Module — M3.5 Ledger Completeness and Replay.

Provides append-only ledger emission, deterministic replay,
and plan-decision-execution linkage for runtime audit.

Invariants:
- Append-only: no record mutation or deletion
- Deterministic: same inputs produce identical outputs
- Join key: (request_id, plan_hash)
- Boundary phrase match: exact between plan and ledger
"""

from runtime.ledger.contracts import (
    DecisionEvent,
    ExecutionEvent,
    LedgerEventType,
    LedgerRowV1,
    PlanEvent,
    ReplaySession,
)
from runtime.ledger.emitter import LedgerEmitterV1
from runtime.ledger.store import LedgerStore, LedgerStoreError
from runtime.ledger.replay import LedgerReplay

__all__ = [
    "LedgerRowV1",
    "LedgerEventType",
    "PlanEvent",
    "DecisionEvent",
    "ExecutionEvent",
    "ReplaySession",
    "LedgerEmitterV1",
    "LedgerStore",
    "LedgerStoreError",
    "LedgerReplay",
]
