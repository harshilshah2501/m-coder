"""
M4.2 Baseline Store — Persistence for baseline artifacts.

Stores and retrieves baseline snapshots as JSON artifacts.
Supports both file-based and SQLite-based storage.

File-based: One JSON file per baseline snapshot
SQLite-based: Single database with baseline table

Storage is append-only in philosophy (baselines are immutable once created).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.observation.baseline_models import BaselineSnapshot


class BaselineStoreError(Exception):
    """Raised when baseline storage operations fail."""
    pass


class BaselineStore:
    """
    Persistence layer for baseline snapshots.
    
    Supports two storage modes:
    - File-based: JSON files in a directory
    - SQLite: Single database with baselines table
    
    Baselines are immutable once stored.
    """
    
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS baselines (
        baseline_id TEXT PRIMARY KEY,
        baseline_hash TEXT NOT NULL,
        created_utc TEXT NOT NULL,
        ledger_path TEXT NOT NULL,
        row_count INTEGER NOT NULL,
        time_range_start TEXT NOT NULL,
        time_range_end TEXT NOT NULL,
        runtime_version TEXT NOT NULL,
        snapshot_json TEXT NOT NULL
    );
    
    CREATE INDEX IF NOT EXISTS idx_baselines_hash ON baselines(baseline_hash);
    CREATE INDEX IF NOT EXISTS idx_baselines_created ON baselines(created_utc);
    """
    
    def __init__(
        self,
        path: Path | str,
        *,
        mode: str = "auto",
    ):
        """
        Initialize baseline store.
        
        Args:
            path: Path to storage location
            mode: Storage mode - "file", "sqlite", or "auto"
                  "auto" uses file mode if path is a directory, sqlite otherwise
        """
        self.path = Path(path)
        
        if mode == "auto":
            if self.path.is_dir() or not self.path.suffix:
                self.mode = "file"
            else:
                self.mode = "sqlite"
        else:
            self.mode = mode
        
        self._ensure_storage()
    
    def _ensure_storage(self) -> None:
        """Initialize storage backend."""
        if self.mode == "file":
            self.path.mkdir(parents=True, exist_ok=True)
        elif self.mode == "sqlite":
            self.path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with sqlite3.connect(self.path) as conn:
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.executescript(self.SCHEMA)
            except sqlite3.Error as e:
                raise BaselineStoreError(f"Failed to initialize baseline store: {e}") from e
    
    def save(self, snapshot: BaselineSnapshot) -> str:
        """
        Save a baseline snapshot.
        
        Args:
            snapshot: The baseline snapshot to save
            
        Returns:
            The baseline_id of the saved snapshot
            
        Raises:
            BaselineStoreError: If save fails
        """
        if self.mode == "file":
            return self._save_file(snapshot)
        else:
            return self._save_sqlite(snapshot)
    
    def _save_file(self, snapshot: BaselineSnapshot) -> str:
        """Save snapshot as JSON file."""
        baseline_id = snapshot.metadata.baseline_id
        file_path = self.path / f"{baseline_id}.json"
        
        try:
            content = json.dumps(snapshot.to_dict(), indent=2, sort_keys=True)
            file_path.write_text(content, encoding="utf-8")
        except (IOError, OSError) as e:
            raise BaselineStoreError(f"Failed to save baseline: {e}") from e
        
        return baseline_id
    
    def _save_sqlite(self, snapshot: BaselineSnapshot) -> str:
        """Save snapshot to SQLite database."""
        baseline_id = snapshot.metadata.baseline_id
        snapshot_json = json.dumps(snapshot.to_dict(), sort_keys=True)
        
        try:
            with sqlite3.connect(self.path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO baselines (
                        baseline_id, baseline_hash, created_utc, ledger_path,
                        row_count, time_range_start, time_range_end,
                        runtime_version, snapshot_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        baseline_id,
                        snapshot.baseline_hash,
                        snapshot.metadata.created_utc,
                        snapshot.metadata.ledger_path,
                        snapshot.metadata.row_count,
                        snapshot.metadata.time_range_start,
                        snapshot.metadata.time_range_end,
                        snapshot.metadata.runtime_version,
                        snapshot_json,
                    ),
                )
        except sqlite3.Error as e:
            raise BaselineStoreError(f"Failed to save baseline: {e}") from e
        
        return baseline_id
    
    def load(self, baseline_id: str) -> BaselineSnapshot | None:
        """
        Load a baseline snapshot by ID.
        
        Args:
            baseline_id: The baseline ID to load
            
        Returns:
            The baseline snapshot, or None if not found
        """
        if self.mode == "file":
            return self._load_file(baseline_id)
        else:
            return self._load_sqlite(baseline_id)
    
    def _load_file(self, baseline_id: str) -> BaselineSnapshot | None:
        """Load snapshot from JSON file."""
        file_path = self.path / f"{baseline_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            content = file_path.read_text(encoding="utf-8")
            data = json.loads(content)
            return BaselineSnapshot.from_dict(data)
        except (IOError, OSError, json.JSONDecodeError) as e:
            raise BaselineStoreError(f"Failed to load baseline: {e}") from e
    
    def _load_sqlite(self, baseline_id: str) -> BaselineSnapshot | None:
        """Load snapshot from SQLite database."""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT snapshot_json FROM baselines WHERE baseline_id = ?",
                    (baseline_id,),
                )
                row = cur.fetchone()
        except sqlite3.Error as e:
            raise BaselineStoreError(f"Failed to load baseline: {e}") from e
        
        if row is None:
            return None
        
        data = json.loads(row["snapshot_json"])
        return BaselineSnapshot.from_dict(data)
    
    def load_by_hash(self, baseline_hash: str) -> BaselineSnapshot | None:
        """
        Load a baseline snapshot by its content hash.
        
        Args:
            baseline_hash: The baseline content hash
            
        Returns:
            The first matching baseline snapshot, or None if not found
        """
        if self.mode == "file":
            for snapshot in self.list_all():
                if snapshot.baseline_hash == baseline_hash:
                    return snapshot
            return None
        else:
            return self._load_by_hash_sqlite(baseline_hash)
    
    def _load_by_hash_sqlite(self, baseline_hash: str) -> BaselineSnapshot | None:
        """Load snapshot by hash from SQLite."""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT snapshot_json FROM baselines WHERE baseline_hash = ? LIMIT 1",
                    (baseline_hash,),
                )
                row = cur.fetchone()
        except sqlite3.Error as e:
            raise BaselineStoreError(f"Failed to load baseline: {e}") from e
        
        if row is None:
            return None
        
        data = json.loads(row["snapshot_json"])
        return BaselineSnapshot.from_dict(data)
    
    def load_latest(self) -> BaselineSnapshot | None:
        """
        Load the most recently created baseline snapshot.
        
        Returns:
            The latest baseline snapshot, or None if store is empty
        """
        if self.mode == "file":
            return self._load_latest_file()
        else:
            return self._load_latest_sqlite()
    
    def _load_latest_file(self) -> BaselineSnapshot | None:
        """Load latest snapshot from file storage."""
        snapshots = list(self.list_all())
        if not snapshots:
            return None
        
        snapshots.sort(key=lambda s: s.metadata.created_utc, reverse=True)
        return snapshots[0]
    
    def _load_latest_sqlite(self) -> BaselineSnapshot | None:
        """Load latest snapshot from SQLite."""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT snapshot_json FROM baselines ORDER BY created_utc DESC LIMIT 1"
                )
                row = cur.fetchone()
        except sqlite3.Error as e:
            raise BaselineStoreError(f"Failed to load baseline: {e}") from e
        
        if row is None:
            return None
        
        data = json.loads(row["snapshot_json"])
        return BaselineSnapshot.from_dict(data)
    
    def list_all(self) -> list[BaselineSnapshot]:
        """
        List all stored baselines.
        
        Returns:
            List of all baseline snapshots, ordered by creation time
        """
        if self.mode == "file":
            return self._list_all_file()
        else:
            return self._list_all_sqlite()
    
    def _list_all_file(self) -> list[BaselineSnapshot]:
        """List all snapshots from file storage."""
        snapshots = []
        for file_path in self.path.glob("*.json"):
            try:
                content = file_path.read_text(encoding="utf-8")
                data = json.loads(content)
                snapshots.append(BaselineSnapshot.from_dict(data))
            except (IOError, OSError, json.JSONDecodeError):
                continue
        
        snapshots.sort(key=lambda s: s.metadata.created_utc)
        return snapshots
    
    def _list_all_sqlite(self) -> list[BaselineSnapshot]:
        """List all snapshots from SQLite."""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT snapshot_json FROM baselines ORDER BY created_utc"
                )
                rows = cur.fetchall()
        except sqlite3.Error as e:
            raise BaselineStoreError(f"Failed to list baselines: {e}") from e
        
        return [
            BaselineSnapshot.from_dict(json.loads(row["snapshot_json"]))
            for row in rows
        ]
    
    def list_ids(self) -> list[str]:
        """
        List all baseline IDs.
        
        Returns:
            List of baseline IDs, ordered by creation time
        """
        if self.mode == "file":
            ids = [f.stem for f in self.path.glob("*.json")]
            snapshots = [(bid, self.load(bid)) for bid in ids]
            snapshots = [(bid, s) for bid, s in snapshots if s is not None]
            snapshots.sort(key=lambda x: x[1].metadata.created_utc)
            return [bid for bid, _ in snapshots]
        else:
            try:
                with sqlite3.connect(self.path) as conn:
                    cur = conn.execute(
                        "SELECT baseline_id FROM baselines ORDER BY created_utc"
                    )
                    return [row[0] for row in cur.fetchall()]
            except sqlite3.Error as e:
                raise BaselineStoreError(f"Failed to list baselines: {e}") from e
    
    def count(self) -> int:
        """Get total number of stored baselines."""
        if self.mode == "file":
            return len(list(self.path.glob("*.json")))
        else:
            try:
                with sqlite3.connect(self.path) as conn:
                    cur = conn.execute("SELECT COUNT(*) FROM baselines")
                    return cur.fetchone()[0]
            except sqlite3.Error:
                return 0
    
    def exists(self, baseline_id: str) -> bool:
        """Check if a baseline exists."""
        if self.mode == "file":
            return (self.path / f"{baseline_id}.json").exists()
        else:
            try:
                with sqlite3.connect(self.path) as conn:
                    cur = conn.execute(
                        "SELECT 1 FROM baselines WHERE baseline_id = ?",
                        (baseline_id,),
                    )
                    return cur.fetchone() is not None
            except sqlite3.Error:
                return False
