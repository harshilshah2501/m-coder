"""
Ledger Store — M3.5 append-only persistent storage for ledger rows.

Unified store that consolidates ledger emission from all runtime decision points.
Uses SQLite with WAL mode for durability. Append-only semantics enforced.

Invariants:
- No deletion or mutation of existing rows
- Fail-closed: persistence failure raises LedgerStoreError
- Join key: (request_id, plan_hash)
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from runtime.ledger.contracts import LedgerEventType, LedgerRowV1


class LedgerStoreError(Exception):
    """Raised when ledger persistence fails (fail-closed semantics)."""
    pass


class LedgerStore:
    """
    Append-only SQLite store for ledger rows.
    
    WAL mode for durability. Deterministic row creation.
    No mutation or deletion operations.
    """
    
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS ledger_rows (
        event_id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        request_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        plan_hash TEXT NOT NULL,
        timestamp_utc TEXT NOT NULL,
        mode TEXT NOT NULL DEFAULT 'shadow',
        payload TEXT NOT NULL
    );
    
    CREATE INDEX IF NOT EXISTS idx_ledger_request_id ON ledger_rows(request_id);
    CREATE INDEX IF NOT EXISTS idx_ledger_plan_hash ON ledger_rows(plan_hash);
    CREATE INDEX IF NOT EXISTS idx_ledger_request_plan ON ledger_rows(request_id, plan_hash);
    CREATE INDEX IF NOT EXISTS idx_ledger_timestamp ON ledger_rows(timestamp_utc);
    CREATE INDEX IF NOT EXISTS idx_ledger_event_type ON ledger_rows(event_type);
    """
    
    def __init__(
        self,
        path: Path | str,
        *,
        fixed_time: str | None = None,
        runtime_version: str = "0.1.0",
    ):
        """
        Initialize ledger store.
        
        Args:
            path: SQLite database file path
            fixed_time: Optional fixed timestamp for deterministic tests
            runtime_version: Runtime version for ledger rows
        """
        self.path = Path(path)
        self.fixed_time = fixed_time
        self.runtime_version = runtime_version
        self._ensure_schema()
    
    def _ensure_schema(self) -> None:
        """Initialize database schema."""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.executescript(self.SCHEMA)
        except sqlite3.Error as e:
            raise LedgerStoreError(f"Failed to initialize ledger store: {e}") from e
    
    def _timestamp(self) -> str:
        """Get current timestamp or fixed time for tests."""
        return self.fixed_time or datetime.now(timezone.utc).isoformat()
    
    def append_row(self, row: LedgerRowV1, event_type: LedgerEventType | str) -> str:
        """
        Append a ledger row to the store.
        
        Args:
            row: The LedgerRowV1 to persist
            event_type: The event type for indexing
            
        Returns:
            The event_id of the persisted row
            
        Raises:
            LedgerStoreError: If persistence fails (including duplicate event_id)
        """
        if isinstance(event_type, LedgerEventType):
            event_type = event_type.value
        
        payload = json.dumps(row.to_dict(), sort_keys=True, ensure_ascii=False)
        
        try:
            with sqlite3.connect(self.path) as conn:
                conn.execute(
                    """
                    INSERT INTO ledger_rows (
                        event_id, event_type, request_id, session_id,
                        plan_hash, timestamp_utc, mode, payload
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row.event_id,
                        event_type,
                        row.request_id,
                        row.session_id,
                        row.plan_hash,
                        row.timestamp_utc,
                        row.mode,
                        payload,
                    ),
                )
        except sqlite3.IntegrityError as e:
            raise LedgerStoreError(f"Duplicate event_id: {row.event_id}") from e
        except sqlite3.Error as e:
            raise LedgerStoreError(f"Ledger append failed: {e}") from e
        
        return row.event_id
    
    def append_raw(
        self,
        *,
        event_id: str,
        event_type: str,
        request_id: str,
        session_id: str,
        plan_hash: str,
        mode: str = "shadow",
        payload: dict[str, Any],
    ) -> str:
        """
        Append a raw ledger entry (for compatibility with existing code).
        
        Returns event_id on success.
        Raises LedgerStoreError on failure.
        """
        timestamp = self._timestamp()
        payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        
        try:
            with sqlite3.connect(self.path) as conn:
                conn.execute(
                    """
                    INSERT INTO ledger_rows (
                        event_id, event_type, request_id, session_id,
                        plan_hash, timestamp_utc, mode, payload
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        event_type,
                        request_id,
                        session_id,
                        plan_hash,
                        timestamp,
                        mode,
                        payload_json,
                    ),
                )
        except sqlite3.IntegrityError as e:
            raise LedgerStoreError(f"Duplicate event_id: {event_id}") from e
        except sqlite3.Error as e:
            raise LedgerStoreError(f"Ledger append failed: {e}") from e
        
        return event_id
    
    def get_by_event_id(self, event_id: str) -> LedgerRowV1 | None:
        """Get a ledger row by event_id."""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT payload FROM ledger_rows WHERE event_id = ?",
                    (event_id,),
                )
                row = cur.fetchone()
        except sqlite3.Error:
            return None
        
        if row is None:
            return None
        
        payload = json.loads(row["payload"])
        return LedgerRowV1.from_dict(payload)
    
    def get_by_request_id(self, request_id: str) -> list[LedgerRowV1]:
        """Get all ledger rows for a request_id, ordered by timestamp."""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT payload FROM ledger_rows WHERE request_id = ? ORDER BY timestamp_utc",
                    (request_id,),
                )
                rows = cur.fetchall()
        except sqlite3.Error:
            return []
        
        return [LedgerRowV1.from_dict(json.loads(r["payload"])) for r in rows]
    
    def get_by_plan_hash(self, plan_hash: str) -> list[LedgerRowV1]:
        """Get all ledger rows for a plan_hash, ordered by timestamp."""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT payload FROM ledger_rows WHERE plan_hash = ? ORDER BY timestamp_utc",
                    (plan_hash,),
                )
                rows = cur.fetchall()
        except sqlite3.Error:
            return []
        
        return [LedgerRowV1.from_dict(json.loads(r["payload"])) for r in rows]
    
    def get_by_join_key(self, request_id: str, plan_hash: str) -> list[LedgerRowV1]:
        """
        Get all ledger rows by join key (request_id, plan_hash).
        
        This is the primary reconciliation query for audit.
        """
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    """
                    SELECT payload FROM ledger_rows 
                    WHERE request_id = ? AND plan_hash = ?
                    ORDER BY timestamp_utc
                    """,
                    (request_id, plan_hash),
                )
                rows = cur.fetchall()
        except sqlite3.Error:
            return []
        
        return [LedgerRowV1.from_dict(json.loads(r["payload"])) for r in rows]
    
    def get_by_event_type(
        self,
        event_type: LedgerEventType | str,
        limit: int | None = None,
    ) -> list[LedgerRowV1]:
        """Get ledger rows by event type."""
        if isinstance(event_type, LedgerEventType):
            event_type = event_type.value
        
        query = "SELECT payload FROM ledger_rows WHERE event_type = ? ORDER BY timestamp_utc"
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(query, (event_type,))
                rows = cur.fetchall()
        except sqlite3.Error:
            return []
        
        return [LedgerRowV1.from_dict(json.loads(r["payload"])) for r in rows]
    
    def get_by_session_id(self, session_id: str) -> list[LedgerRowV1]:
        """Get all ledger rows for a session_id, ordered by timestamp."""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT payload FROM ledger_rows WHERE session_id = ? ORDER BY timestamp_utc",
                    (session_id,),
                )
                rows = cur.fetchall()
        except sqlite3.Error:
            return []
        
        return [LedgerRowV1.from_dict(json.loads(r["payload"])) for r in rows]
    
    def list_all(self, limit: int | None = None) -> list[LedgerRowV1]:
        """List all ledger rows, ordered by timestamp."""
        query = "SELECT payload FROM ledger_rows ORDER BY timestamp_utc"
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(query)
                rows = cur.fetchall()
        except sqlite3.Error:
            return []
        
        return [LedgerRowV1.from_dict(json.loads(r["payload"])) for r in rows]
    
    def count(self) -> int:
        """Get total number of ledger rows."""
        try:
            with sqlite3.connect(self.path) as conn:
                cur = conn.execute("SELECT COUNT(*) FROM ledger_rows")
                return cur.fetchone()[0]
        except sqlite3.Error:
            return 0
    
    def count_by_request_id(self, request_id: str) -> int:
        """Get count of ledger rows for a request_id."""
        try:
            with sqlite3.connect(self.path) as conn:
                cur = conn.execute(
                    "SELECT COUNT(*) FROM ledger_rows WHERE request_id = ?",
                    (request_id,),
                )
                return cur.fetchone()[0]
        except sqlite3.Error:
            return 0
    
    def iter_all(self, batch_size: int = 100) -> Iterator[LedgerRowV1]:
        """
        Iterate over all ledger rows in timestamp order.
        
        Memory-efficient for large ledgers.
        """
        offset = 0
        while True:
            try:
                with sqlite3.connect(self.path) as conn:
                    conn.row_factory = sqlite3.Row
                    cur = conn.execute(
                        "SELECT payload FROM ledger_rows ORDER BY timestamp_utc LIMIT ? OFFSET ?",
                        (batch_size, offset),
                    )
                    rows = cur.fetchall()
            except sqlite3.Error:
                break
            
            if not rows:
                break
            
            for r in rows:
                yield LedgerRowV1.from_dict(json.loads(r["payload"]))
            
            offset += batch_size
    
    def get_unique_request_ids(self) -> list[str]:
        """Get all unique request_ids in the ledger."""
        try:
            with sqlite3.connect(self.path) as conn:
                cur = conn.execute(
                    "SELECT DISTINCT request_id FROM ledger_rows ORDER BY request_id"
                )
                return [r[0] for r in cur.fetchall()]
        except sqlite3.Error:
            return []
    
    def get_unique_session_ids(self) -> list[str]:
        """Get all unique session_ids in the ledger."""
        try:
            with sqlite3.connect(self.path) as conn:
                cur = conn.execute(
                    "SELECT DISTINCT session_id FROM ledger_rows ORDER BY session_id"
                )
                return [r[0] for r in cur.fetchall()]
        except sqlite3.Error:
            return []
