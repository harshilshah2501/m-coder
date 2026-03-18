"""
Sandbox Ledger Store — M3.2 deterministic local persistence for runtime evidence.

Append-only SQLite store for REFUSED, BLOCKED, and EXECUTED outcomes.
No fail-open: if persistence is required and append fails, the failure is surfaced.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Event types for the three canonical outcomes.
EVENT_REFUSED = "sandbox_refused"
EVENT_BLOCKED = "sandbox_blocked"
EVENT_EXECUTED = "sandbox_executed"

# Plan-Gate decision events (M3.3).
EVENT_PLANGATE_REFUSED = "plangate_refused"
EVENT_PLANGATE_DEFERRED = "plangate_deferred"
EVENT_PLANGATE_BOUNDED_ALLOW = "plangate_bounded_allow"
EVENT_PLANGATE_SAFE_EXECUTE = "plangate_safe_execute"


@dataclass
class LedgerRow:
    """One row in the local evidence store."""

    ledger_row_id: str
    event_type: str
    outcome_type: str  # refused | blocked | executed
    request_id: str
    plan_hash: str
    sandbox_id: str
    timestamp_utc: str
    payload: dict[str, Any]
    artifact_manifest_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ledger_row_id": self.ledger_row_id,
            "event_type": self.event_type,
            "outcome_type": self.outcome_type,
            "request_id": self.request_id,
            "plan_hash": self.plan_hash,
            "sandbox_id": self.sandbox_id,
            "timestamp_utc": self.timestamp_utc,
            "payload": self.payload,
            "artifact_manifest_ref": self.artifact_manifest_ref,
        }


class LedgerStoreError(Exception):
    """Raised when persistence fails (fail-closed)."""

    pass


class SandboxLedgerStore:
    """
    Append-only local SQLite store for sandbox/runtime evidence.
    WAL mode for durability. Deterministic row creation per outcome.

    Supports two schema shapes (read-only compatibility):
    - Full schema: top-level canonical_hash column + index.
    - Legacy/spool schema: canonical_hash only in payload JSON (no column).
    """

    SCHEMA_TABLE = """
    CREATE TABLE IF NOT EXISTS sandbox_ledger (
        ledger_row_id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        outcome_type TEXT NOT NULL,
        request_id TEXT NOT NULL,
        plan_hash TEXT NOT NULL,
        sandbox_id TEXT NOT NULL,
        timestamp_utc TEXT NOT NULL,
        payload TEXT NOT NULL,
        artifact_manifest_ref TEXT NOT NULL DEFAULT '',
        canonical_hash TEXT NOT NULL DEFAULT ''
    );
    """

    def __init__(self, path: Path | str, *, fixed_time: str | None = None):
        """
        Args:
            path: SQLite database file path.
            fixed_time: Optional fixed timestamp for deterministic tests.
        """
        self.path = Path(path)
        self.fixed_time = fixed_time
        self._has_canonical_hash_column: bool = False
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        try:
            with sqlite3.connect(self.path) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.executescript(self.SCHEMA_TABLE)
                cur = conn.execute("PRAGMA table_info(sandbox_ledger)")
                columns = [row[1] for row in cur.fetchall()]
                self._has_canonical_hash_column = "canonical_hash" in columns
                if self._has_canonical_hash_column:
                    conn.execute(
                        "CREATE INDEX IF NOT EXISTS idx_canonical_hash ON sandbox_ledger(canonical_hash)"
                    )
        except sqlite3.Error as e:
            raise LedgerStoreError(f"Failed to initialize ledger store: {e}") from e

    def _timestamp(self) -> str:
        return self.fixed_time or datetime.now(timezone.utc).isoformat()

    def append(
        self,
        *,
        ledger_row_id: str,
        event_type: str,
        outcome_type: str,
        request_id: str,
        plan_hash: str = "",
        sandbox_id: str = "",
        payload: dict[str, Any],
        artifact_manifest_ref: str = "",
    ) -> LedgerRow:
        """
        Append one row. Raises LedgerStoreError on failure (no silent success).
        Rows without canonical_hash in payload store empty string (backward compatible).
        """
        timestamp = self._timestamp()
        canonical_hash = payload.get("canonical_hash", "") or ""
        payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        row = LedgerRow(
            ledger_row_id=ledger_row_id,
            event_type=event_type,
            outcome_type=outcome_type,
            request_id=request_id,
            plan_hash=plan_hash or "",
            sandbox_id=sandbox_id or "",
            timestamp_utc=timestamp,
            payload=payload,
            artifact_manifest_ref=artifact_manifest_ref or "",
        )
        try:
            with sqlite3.connect(self.path) as conn:
                conn.execute(
                    """
                    INSERT INTO sandbox_ledger (
                        ledger_row_id, event_type, outcome_type,
                        request_id, plan_hash, sandbox_id, timestamp_utc,
                        payload, artifact_manifest_ref, canonical_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ledger_row_id,
                        event_type,
                        outcome_type,
                        request_id,
                        plan_hash or "",
                        sandbox_id or "",
                        timestamp,
                        payload_json,
                        artifact_manifest_ref or "",
                        canonical_hash,
                    ),
                )
        except sqlite3.Error as e:
            raise LedgerStoreError(f"Ledger append failed: {e}") from e
        return row

    def get_by_ledger_row_id(self, ledger_row_id: str) -> LedgerRow | None:
        """Return one row by id, or None."""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT * FROM sandbox_ledger WHERE ledger_row_id = ?",
                    (ledger_row_id,),
                )
                row = cur.fetchone()
        except sqlite3.Error:
            return None
        if row is None:
            return None
        payload = json.loads(row["payload"])
        return LedgerRow(
            ledger_row_id=row["ledger_row_id"],
            event_type=row["event_type"],
            outcome_type=row["outcome_type"],
            request_id=row["request_id"],
            plan_hash=row["plan_hash"] or "",
            sandbox_id=row["sandbox_id"] or "",
            timestamp_utc=row["timestamp_utc"],
            payload=payload,
            artifact_manifest_ref=row["artifact_manifest_ref"] or "",
        )

    def get_by_request_id(self, request_id: str) -> list[LedgerRow]:
        """Return all rows for a request_id (order by timestamp)."""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT * FROM sandbox_ledger WHERE request_id = ? ORDER BY timestamp_utc",
                    (request_id,),
                )
                rows = cur.fetchall()
        except sqlite3.Error:
            return []
        out = []
        for row in rows:
            payload = json.loads(row["payload"])
            out.append(
                LedgerRow(
                    ledger_row_id=row["ledger_row_id"],
                    event_type=row["event_type"],
                    outcome_type=row["outcome_type"],
                    request_id=row["request_id"],
                    plan_hash=row["plan_hash"] or "",
                    sandbox_id=row["sandbox_id"] or "",
                    timestamp_utc=row["timestamp_utc"],
                    payload=payload,
                    artifact_manifest_ref=row["artifact_manifest_ref"] or "",
                )
            )
        return out

    def get_by_canonical_hash(self, canonical_hash: str) -> list[LedgerRow]:
        """Return all rows with the given canonical_hash (order by timestamp).
        Works with both top-level canonical_hash column and payload-only (legacy) schema.
        """
        if not canonical_hash:
            return []
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                if self._has_canonical_hash_column:
                    cur = conn.execute(
                        "SELECT * FROM sandbox_ledger WHERE canonical_hash = ? ORDER BY timestamp_utc",
                        (canonical_hash,),
                    )
                else:
                    cur = conn.execute(
                        """SELECT * FROM sandbox_ledger
                           WHERE json_extract(payload, '$.canonical_hash') = ?
                           ORDER BY timestamp_utc""",
                        (canonical_hash,),
                    )
                rows = cur.fetchall()
        except sqlite3.Error:
            return []
        out = []
        for row in rows:
            payload = json.loads(row["payload"])
            out.append(
                LedgerRow(
                    ledger_row_id=row["ledger_row_id"],
                    event_type=row["event_type"],
                    outcome_type=row["outcome_type"],
                    request_id=row["request_id"],
                    plan_hash=row["plan_hash"] or "",
                    sandbox_id=row["sandbox_id"] or "",
                    timestamp_utc=row["timestamp_utc"],
                    payload=payload,
                    artifact_manifest_ref=row["artifact_manifest_ref"] or "",
                )
            )
        return out

    def list_all(self) -> list[LedgerRow]:
        """Return all rows (for tests/demo)."""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT * FROM sandbox_ledger ORDER BY timestamp_utc"
                )
                rows = cur.fetchall()
        except sqlite3.Error:
            return []
        out = []
        for row in rows:
            payload = json.loads(row["payload"])
            out.append(
                LedgerRow(
                    ledger_row_id=row["ledger_row_id"],
                    event_type=row["event_type"],
                    outcome_type=row["outcome_type"],
                    request_id=row["request_id"],
                    plan_hash=row["plan_hash"] or "",
                    sandbox_id=row["sandbox_id"] or "",
                    timestamp_utc=row["timestamp_utc"],
                    payload=payload,
                    artifact_manifest_ref=row["artifact_manifest_ref"] or "",
                )
            )
        return out
