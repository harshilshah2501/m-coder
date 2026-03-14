"""
M4.2 Drift Baseline — Builder for deterministic baseline artifacts.

Builds baseline snapshots from ledger evidence. Read-only over ledger data.
No LLMs, no randomness, deterministic output.

Usage:
    builder = BaselineBuilder(ledger_path="/path/to/ledger.db")
    snapshot = builder.build_baseline()
    
    # Or with specific evidence source
    builder = BaselineBuilder(ledger_store=existing_store)
    snapshot = builder.build_baseline(
        time_range_start="2026-01-01T00:00:00Z",
        time_range_end="2026-03-01T00:00:00Z",
    )
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from runtime.observation.baseline_models import (
    BaselineDimension,
    BaselineMetadata,
    BaselineSnapshot,
    DimensionDistribution,
)


class BaselineBuildError(Exception):
    """Raised when baseline building fails."""
    pass


class BaselineBuilder:
    """
    Builds deterministic baseline snapshots from ledger evidence.
    
    Read-only over ledger data. Extracts distributions for all baseline
    dimensions from ledger rows.
    
    Supports both unified LedgerStore and SandboxLedgerStore formats.
    """
    
    RUNTIME_VERSION = "0.1.0"
    
    def __init__(
        self,
        ledger_path: Path | str | None = None,
        *,
        sandbox_ledger_path: Path | str | None = None,
        fixed_time: str | None = None,
    ):
        """
        Initialize baseline builder.
        
        Args:
            ledger_path: Path to unified LedgerStore SQLite database
            sandbox_ledger_path: Path to SandboxLedgerStore SQLite database
            fixed_time: Optional fixed timestamp for deterministic tests
            
        At least one ledger path must be provided.
        """
        self.ledger_path = Path(ledger_path) if ledger_path else None
        self.sandbox_ledger_path = Path(sandbox_ledger_path) if sandbox_ledger_path else None
        self.fixed_time = fixed_time
        
        if not self.ledger_path and not self.sandbox_ledger_path:
            raise BaselineBuildError("At least one ledger path must be provided")
    
    def _timestamp(self) -> str:
        """Get current timestamp or fixed time for tests."""
        return self.fixed_time or datetime.now(timezone.utc).isoformat()
    
    def _generate_baseline_id(self) -> str:
        """Generate deterministic baseline ID from timestamp and paths."""
        content = {
            "timestamp": self._timestamp(),
            "ledger_path": str(self.ledger_path) if self.ledger_path else "",
            "sandbox_ledger_path": str(self.sandbox_ledger_path) if self.sandbox_ledger_path else "",
        }
        content_bytes = json.dumps(content, sort_keys=True).encode("utf-8")
        return f"baseline-{hashlib.sha256(content_bytes).hexdigest()[:16]}"
    
    def _iter_unified_ledger_rows(
        self,
        time_start: str | None = None,
        time_end: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        """
        Iterate over unified ledger rows.
        
        Yields raw row data as dictionaries for dimension extraction.
        """
        if not self.ledger_path or not self.ledger_path.exists():
            return
        
        query = "SELECT event_type, request_id, plan_hash, timestamp_utc, payload FROM ledger_rows"
        conditions = []
        params: list[Any] = []
        
        if time_start:
            conditions.append("timestamp_utc >= ?")
            params.append(time_start)
        if time_end:
            conditions.append("timestamp_utc <= ?")
            params.append(time_end)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY timestamp_utc"
        
        try:
            with sqlite3.connect(self.ledger_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(query, params)
                for row in cur:
                    payload = json.loads(row["payload"]) if row["payload"] else {}
                    yield {
                        "source": "unified_ledger",
                        "event_type": row["event_type"],
                        "request_id": row["request_id"],
                        "plan_hash": row["plan_hash"],
                        "timestamp_utc": row["timestamp_utc"],
                        "payload": payload,
                    }
        except sqlite3.Error as e:
            raise BaselineBuildError(f"Failed to read unified ledger: {e}") from e
    
    def _iter_sandbox_ledger_rows(
        self,
        time_start: str | None = None,
        time_end: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        """
        Iterate over sandbox ledger rows.
        
        Yields raw row data as dictionaries for dimension extraction.
        """
        if not self.sandbox_ledger_path or not self.sandbox_ledger_path.exists():
            return
        
        query = """
            SELECT ledger_row_id, event_type, outcome_type, request_id, 
                   plan_hash, sandbox_id, timestamp_utc, payload, canonical_hash
            FROM sandbox_ledger
        """
        conditions = []
        params: list[Any] = []
        
        if time_start:
            conditions.append("timestamp_utc >= ?")
            params.append(time_start)
        if time_end:
            conditions.append("timestamp_utc <= ?")
            params.append(time_end)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY timestamp_utc"
        
        try:
            with sqlite3.connect(self.sandbox_ledger_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(query, params)
                for row in cur:
                    payload = json.loads(row["payload"]) if row["payload"] else {}
                    yield {
                        "source": "sandbox_ledger",
                        "ledger_row_id": row["ledger_row_id"],
                        "event_type": row["event_type"],
                        "outcome_type": row["outcome_type"],
                        "request_id": row["request_id"],
                        "plan_hash": row["plan_hash"],
                        "sandbox_id": row["sandbox_id"],
                        "timestamp_utc": row["timestamp_utc"],
                        "payload": payload,
                        "canonical_hash": row["canonical_hash"] or "",
                    }
        except sqlite3.Error as e:
            raise BaselineBuildError(f"Failed to read sandbox ledger: {e}") from e
    
    def _extract_event_type(self, row: dict[str, Any]) -> str | None:
        """Extract event_type from a ledger row."""
        return row.get("event_type")
    
    def _extract_outcome_type(self, row: dict[str, Any]) -> str | None:
        """Extract outcome_type from a ledger row."""
        if row.get("source") == "sandbox_ledger":
            return row.get("outcome_type")
        return None
    
    def _extract_decision_posture(self, row: dict[str, Any]) -> str | None:
        """Extract decision_posture from a ledger row payload."""
        payload = row.get("payload", {})
        posture = payload.get("decision_posture")
        if posture:
            return posture
        
        event_type = row.get("event_type", "")
        if "plangate_refused" in event_type:
            return "refuse"
        elif "plangate_deferred" in event_type:
            return "defer"
        elif "plangate_bounded_allow" in event_type:
            return "bounded_allow"
        elif "plangate_safe_execute" in event_type:
            return "safe_execute"
        
        return None
    
    def _extract_refusal_reason(self, row: dict[str, Any]) -> str | None:
        """Extract refusal reason from a ledger row."""
        payload = row.get("payload", {})
        
        reason = payload.get("reason")
        if reason:
            return reason
        
        reason_codes = payload.get("reason_codes", [])
        if reason_codes:
            return reason_codes[0]
        
        return None
    
    def _extract_backend(self, row: dict[str, Any]) -> str | None:
        """Extract backend from a ledger row payload."""
        payload = row.get("payload", {})
        return payload.get("backend")
    
    def _extract_execution_surface(self, row: dict[str, Any]) -> str | None:
        """Extract execution_surface from a ledger row payload."""
        payload = row.get("payload", {})
        return payload.get("execution_surface")
    
    def _extract_canonical_hash(self, row: dict[str, Any]) -> str | None:
        """Extract canonical_hash from a ledger row."""
        if row.get("source") == "sandbox_ledger":
            ch = row.get("canonical_hash")
            if ch:
                return ch
        
        payload = row.get("payload", {})
        return payload.get("canonical_hash")
    
    def build_baseline(
        self,
        *,
        time_range_start: str | None = None,
        time_range_end: str | None = None,
    ) -> BaselineSnapshot:
        """
        Build a baseline snapshot from ledger evidence.
        
        Args:
            time_range_start: Optional ISO timestamp to filter rows (inclusive)
            time_range_end: Optional ISO timestamp to filter rows (inclusive)
            
        Returns:
            BaselineSnapshot with distributions for all dimensions
            
        Raises:
            BaselineBuildError: If baseline building fails
        """
        distributions: dict[str, DimensionDistribution] = {}
        for dim in BaselineDimension:
            distributions[dim.value] = DimensionDistribution(dimension=dim)
        
        request_id_counts: Counter[str] = Counter()
        canonical_hash_counts: Counter[str] = Counter()
        
        row_count = 0
        timestamps: list[str] = []
        ledger_path_str = ""
        
        for row in self._iter_unified_ledger_rows(time_range_start, time_range_end):
            row_count += 1
            if row.get("timestamp_utc"):
                timestamps.append(row["timestamp_utc"])
            if not ledger_path_str and self.ledger_path:
                ledger_path_str = str(self.ledger_path)
            
            event_type = self._extract_event_type(row)
            if event_type:
                distributions[BaselineDimension.EVENT_TYPE.value].add(event_type)
            
            decision_posture = self._extract_decision_posture(row)
            if decision_posture:
                distributions[BaselineDimension.DECISION_POSTURE.value].add(decision_posture)
            
            refusal_reason = self._extract_refusal_reason(row)
            if refusal_reason:
                distributions[BaselineDimension.REFUSAL_REASON.value].add(refusal_reason)
            
            backend = self._extract_backend(row)
            if backend:
                distributions[BaselineDimension.BACKEND.value].add(backend)
            
            execution_surface = self._extract_execution_surface(row)
            if execution_surface:
                distributions[BaselineDimension.EXECUTION_SURFACE.value].add(execution_surface)
            
            request_id = row.get("request_id")
            if request_id:
                request_id_counts[request_id] += 1
            
            canonical_hash = self._extract_canonical_hash(row)
            if canonical_hash:
                canonical_hash_counts[canonical_hash] += 1
        
        for row in self._iter_sandbox_ledger_rows(time_range_start, time_range_end):
            row_count += 1
            if row.get("timestamp_utc"):
                timestamps.append(row["timestamp_utc"])
            if not ledger_path_str and self.sandbox_ledger_path:
                ledger_path_str = str(self.sandbox_ledger_path)
            
            event_type = self._extract_event_type(row)
            if event_type:
                distributions[BaselineDimension.EVENT_TYPE.value].add(event_type)
            
            outcome_type = self._extract_outcome_type(row)
            if outcome_type:
                distributions[BaselineDimension.OUTCOME_TYPE.value].add(outcome_type)
            
            decision_posture = self._extract_decision_posture(row)
            if decision_posture:
                distributions[BaselineDimension.DECISION_POSTURE.value].add(decision_posture)
            
            refusal_reason = self._extract_refusal_reason(row)
            if refusal_reason:
                distributions[BaselineDimension.REFUSAL_REASON.value].add(refusal_reason)
            
            backend = self._extract_backend(row)
            if backend:
                distributions[BaselineDimension.BACKEND.value].add(backend)
            
            execution_surface = self._extract_execution_surface(row)
            if execution_surface:
                distributions[BaselineDimension.EXECUTION_SURFACE.value].add(execution_surface)
            
            request_id = row.get("request_id")
            if request_id:
                request_id_counts[request_id] += 1
            
            canonical_hash = self._extract_canonical_hash(row)
            if canonical_hash:
                canonical_hash_counts[canonical_hash] += 1
        
        for request_id, count in request_id_counts.items():
            bucket = self._bucket_replay_count(count)
            distributions[BaselineDimension.REPLAY_FREQUENCY.value].add(bucket)
        
        for canonical_hash, count in canonical_hash_counts.items():
            bucket = self._bucket_hash_reuse(count)
            distributions[BaselineDimension.CANONICAL_HASH_REUSE.value].add(bucket)
        
        timestamps.sort()
        time_start = timestamps[0] if timestamps else ""
        time_end = timestamps[-1] if timestamps else ""
        
        if time_range_start:
            time_start = time_range_start
        if time_range_end:
            time_end = time_range_end
        
        metadata = BaselineMetadata(
            baseline_id=self._generate_baseline_id(),
            created_utc=self._timestamp(),
            ledger_path=ledger_path_str,
            row_count=row_count,
            time_range_start=time_start,
            time_range_end=time_end,
            runtime_version=self.RUNTIME_VERSION,
        )
        
        snapshot = BaselineSnapshot(
            metadata=metadata,
            distributions=distributions,
        )
        
        return snapshot
    
    def _bucket_replay_count(self, count: int) -> str:
        """Bucket replay counts into meaningful categories."""
        if count == 1:
            return "single"
        elif count == 2:
            return "two"
        elif count <= 5:
            return "3-5"
        elif count <= 10:
            return "6-10"
        else:
            return "10+"
    
    def _bucket_hash_reuse(self, count: int) -> str:
        """Bucket canonical_hash reuse into meaningful categories."""
        if count == 1:
            return "unique"
        elif count == 2:
            return "reused_once"
        elif count <= 5:
            return "reused_2-4"
        elif count <= 10:
            return "reused_5-9"
        else:
            return "reused_10+"
