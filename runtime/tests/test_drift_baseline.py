"""
M4.2 Drift Baseline Tests — Comprehensive test suite for baseline artifacts.

Tests:
- DimensionDistribution: counts, frequencies, serialization
- BaselineSnapshot: construction, comparison, serialization
- BaselineBuilder: deterministic baseline construction from ledger
- BaselineStore: persistence and retrieval
- End-to-end: build → store → load → compare
"""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from runtime.observation.baseline_models import (
    BaselineDimension,
    BaselineMetadata,
    BaselineSnapshot,
    DimensionDistribution,
)
from runtime.observation.drift_baseline import (
    BaselineBuilder,
    BaselineBuildError,
)
from runtime.observation.baseline_store import (
    BaselineStore,
    BaselineStoreError,
)


# -----------------------------------------------------------------------------
# DimensionDistribution Tests
# -----------------------------------------------------------------------------

class TestDimensionDistribution:
    """Tests for DimensionDistribution data structure."""
    
    def test_add_increments_count(self):
        """Adding a value increments its count."""
        dist = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
        dist.add("plangate_refused")
        dist.add("plangate_refused")
        dist.add("sandbox_executed")
        
        assert dist.counts["plangate_refused"] == 2
        assert dist.counts["sandbox_executed"] == 1
        assert dist.total == 3
    
    def test_add_with_count(self):
        """Adding with explicit count works."""
        dist = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
        dist.add("event_a", count=5)
        dist.add("event_b", count=3)
        
        assert dist.counts["event_a"] == 5
        assert dist.counts["event_b"] == 3
        assert dist.total == 8
    
    def test_get_frequency(self):
        """Frequencies are correctly computed."""
        dist = DimensionDistribution(dimension=BaselineDimension.OUTCOME_TYPE)
        dist.add("executed", count=8)
        dist.add("refused", count=2)
        
        assert dist.get_frequency("executed") == 0.8
        assert dist.get_frequency("refused") == 0.2
        assert dist.get_frequency("blocked") == 0.0
    
    def test_get_frequency_empty(self):
        """Empty distribution returns 0.0 frequency."""
        dist = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
        assert dist.get_frequency("any") == 0.0
    
    def test_get_all_frequencies(self):
        """All frequencies sum to approximately 1.0."""
        dist = DimensionDistribution(dimension=BaselineDimension.DECISION_POSTURE)
        dist.add("safe_execute", count=50)
        dist.add("refuse", count=30)
        dist.add("defer", count=20)
        
        freqs = dist.get_all_frequencies()
        assert freqs == {"defer": 0.2, "refuse": 0.3, "safe_execute": 0.5}
        assert abs(sum(freqs.values()) - 1.0) < 1e-9
    
    def test_to_dict_deterministic(self):
        """Serialization is deterministic (sorted keys)."""
        dist1 = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
        dist1.add("b_event")
        dist1.add("a_event")
        
        dist2 = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
        dist2.add("a_event")
        dist2.add("b_event")
        
        assert dist1.to_dict() == dist2.to_dict()
        assert json.dumps(dist1.to_dict(), sort_keys=True) == json.dumps(dist2.to_dict(), sort_keys=True)
    
    def test_from_dict_roundtrip(self):
        """Serialization roundtrip preserves data."""
        dist = DimensionDistribution(dimension=BaselineDimension.BACKEND)
        dist.add("local_process", count=10)
        dist.add("container", count=5)
        
        data = dist.to_dict()
        restored = DimensionDistribution.from_dict(data)
        
        assert restored.dimension == dist.dimension
        assert restored.counts == dist.counts
        assert restored.total == dist.total


# -----------------------------------------------------------------------------
# BaselineSnapshot Tests
# -----------------------------------------------------------------------------

class TestBaselineSnapshot:
    """Tests for BaselineSnapshot data structure."""
    
    def _make_metadata(self, baseline_id: str = "test-baseline") -> BaselineMetadata:
        return BaselineMetadata(
            baseline_id=baseline_id,
            created_utc="2026-03-13T12:00:00Z",
            ledger_path="/test/ledger.db",
            row_count=100,
            time_range_start="2026-03-01T00:00:00Z",
            time_range_end="2026-03-13T00:00:00Z",
            runtime_version="0.1.0",
        )
    
    def test_baseline_hash_computed(self):
        """Baseline hash is computed on construction."""
        dist = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
        dist.add("test_event", count=10)
        
        snapshot = BaselineSnapshot(
            metadata=self._make_metadata(),
            distributions={BaselineDimension.EVENT_TYPE.value: dist},
        )
        
        assert snapshot.baseline_hash != ""
        assert len(snapshot.baseline_hash) == 64  # SHA-256 hex
    
    def test_same_distributions_same_hash(self):
        """Same distributions produce same hash (deterministic)."""
        def make_snapshot():
            dist = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
            dist.add("event_a", count=5)
            dist.add("event_b", count=3)
            return BaselineSnapshot(
                metadata=self._make_metadata(),
                distributions={BaselineDimension.EVENT_TYPE.value: dist},
            )
        
        s1 = make_snapshot()
        s2 = make_snapshot()
        
        assert s1.baseline_hash == s2.baseline_hash
    
    def test_different_distributions_different_hash(self):
        """Different distributions produce different hashes."""
        dist1 = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
        dist1.add("event_a", count=5)
        
        dist2 = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
        dist2.add("event_a", count=6)  # Different count
        
        s1 = BaselineSnapshot(
            metadata=self._make_metadata(),
            distributions={BaselineDimension.EVENT_TYPE.value: dist1},
        )
        s2 = BaselineSnapshot(
            metadata=self._make_metadata(),
            distributions={BaselineDimension.EVENT_TYPE.value: dist2},
        )
        
        assert s1.baseline_hash != s2.baseline_hash
    
    def test_compare_identical(self):
        """Comparing identical baselines shows no drift."""
        dist = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
        dist.add("event_a", count=10)
        
        snapshot = BaselineSnapshot(
            metadata=self._make_metadata(),
            distributions={BaselineDimension.EVENT_TYPE.value: dist},
        )
        
        drift = snapshot.compare(snapshot)
        
        assert drift["hash_match"] is True
        assert drift["overall_drift_score"] == 0.0
        assert drift["new_values"] == {}
        assert drift["missing_values"] == {}
    
    def test_compare_different_distributions(self):
        """Comparing different distributions shows drift."""
        dist1 = DimensionDistribution(dimension=BaselineDimension.OUTCOME_TYPE)
        dist1.add("executed", count=80)
        dist1.add("refused", count=20)
        
        dist2 = DimensionDistribution(dimension=BaselineDimension.OUTCOME_TYPE)
        dist2.add("executed", count=60)
        dist2.add("refused", count=40)
        
        s1 = BaselineSnapshot(
            metadata=self._make_metadata("baseline-1"),
            distributions={BaselineDimension.OUTCOME_TYPE.value: dist1},
        )
        s2 = BaselineSnapshot(
            metadata=self._make_metadata("baseline-2"),
            distributions={BaselineDimension.OUTCOME_TYPE.value: dist2},
        )
        
        drift = s1.compare(s2)
        
        assert drift["hash_match"] is False
        assert drift["overall_drift_score"] > 0.0
        dim_drift = drift["dimension_drifts"][BaselineDimension.OUTCOME_TYPE.value]
        assert dim_drift["status"] == "compared"
        assert dim_drift["drift_score"] > 0.0
    
    def test_compare_new_values(self):
        """Comparing detects new values in other baseline."""
        dist1 = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
        dist1.add("event_a", count=10)
        
        dist2 = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
        dist2.add("event_a", count=8)
        dist2.add("event_b", count=2)  # New value
        
        s1 = BaselineSnapshot(
            metadata=self._make_metadata("baseline-1"),
            distributions={BaselineDimension.EVENT_TYPE.value: dist1},
        )
        s2 = BaselineSnapshot(
            metadata=self._make_metadata("baseline-2"),
            distributions={BaselineDimension.EVENT_TYPE.value: dist2},
        )
        
        drift = s1.compare(s2)
        
        assert BaselineDimension.EVENT_TYPE.value in drift["new_values"]
        assert "event_b" in drift["new_values"][BaselineDimension.EVENT_TYPE.value]
    
    def test_compare_missing_values(self):
        """Comparing detects missing values in other baseline."""
        dist1 = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
        dist1.add("event_a", count=8)
        dist1.add("event_b", count=2)
        
        dist2 = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
        dist2.add("event_a", count=10)  # event_b missing
        
        s1 = BaselineSnapshot(
            metadata=self._make_metadata("baseline-1"),
            distributions={BaselineDimension.EVENT_TYPE.value: dist1},
        )
        s2 = BaselineSnapshot(
            metadata=self._make_metadata("baseline-2"),
            distributions={BaselineDimension.EVENT_TYPE.value: dist2},
        )
        
        drift = s1.compare(s2)
        
        assert BaselineDimension.EVENT_TYPE.value in drift["missing_values"]
        assert "event_b" in drift["missing_values"][BaselineDimension.EVENT_TYPE.value]
    
    def test_to_dict_roundtrip(self):
        """Serialization roundtrip preserves snapshot."""
        dist = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
        dist.add("event_a", count=10)
        dist.add("event_b", count=5)
        
        snapshot = BaselineSnapshot(
            metadata=self._make_metadata(),
            distributions={BaselineDimension.EVENT_TYPE.value: dist},
        )
        
        data = snapshot.to_dict()
        restored = BaselineSnapshot.from_dict(data)
        
        assert restored.baseline_hash == snapshot.baseline_hash
        assert restored.metadata.baseline_id == snapshot.metadata.baseline_id
        assert restored.metadata.row_count == snapshot.metadata.row_count


# -----------------------------------------------------------------------------
# BaselineBuilder Tests
# -----------------------------------------------------------------------------

class TestBaselineBuilder:
    """Tests for BaselineBuilder."""
    
    def _create_unified_ledger(self, path: Path, rows: list[dict]) -> None:
        """Create a test unified ledger with given rows."""
        with sqlite3.connect(path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ledger_rows (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    plan_hash TEXT NOT NULL,
                    timestamp_utc TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'shadow',
                    payload TEXT NOT NULL
                )
            """)
            for i, row in enumerate(rows):
                conn.execute(
                    """
                    INSERT INTO ledger_rows (
                        event_id, event_type, request_id, session_id,
                        plan_hash, timestamp_utc, mode, payload
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"event-{i}",
                        row.get("event_type", "test_event"),
                        row.get("request_id", f"req-{i}"),
                        row.get("session_id", "session-1"),
                        row.get("plan_hash", "hash-1"),
                        row.get("timestamp_utc", "2026-03-13T12:00:00Z"),
                        row.get("mode", "shadow"),
                        json.dumps(row.get("payload", {})),
                    ),
                )
    
    def _create_sandbox_ledger(self, path: Path, rows: list[dict]) -> None:
        """Create a test sandbox ledger with given rows."""
        with sqlite3.connect(path) as conn:
            conn.execute("""
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
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_canonical_hash ON sandbox_ledger(canonical_hash)")
            for i, row in enumerate(rows):
                conn.execute(
                    """
                    INSERT INTO sandbox_ledger (
                        ledger_row_id, event_type, outcome_type, request_id,
                        plan_hash, sandbox_id, timestamp_utc, payload,
                        artifact_manifest_ref, canonical_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"row-{i}",
                        row.get("event_type", "sandbox_executed"),
                        row.get("outcome_type", "executed"),
                        row.get("request_id", f"req-{i}"),
                        row.get("plan_hash", "hash-1"),
                        row.get("sandbox_id", "sandbox-1"),
                        row.get("timestamp_utc", "2026-03-13T12:00:00Z"),
                        json.dumps(row.get("payload", {})),
                        row.get("artifact_manifest_ref", ""),
                        row.get("canonical_hash", ""),
                    ),
                )
    
    def test_builder_requires_ledger_path(self):
        """Builder requires at least one ledger path."""
        with pytest.raises(BaselineBuildError):
            BaselineBuilder()
    
    def test_build_from_unified_ledger(self):
        """Build baseline from unified ledger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.db"
            
            self._create_unified_ledger(ledger_path, [
                {"event_type": "plangate_refused", "request_id": "req-1"},
                {"event_type": "plangate_refused", "request_id": "req-2"},
                {"event_type": "plangate_safe_execute", "request_id": "req-3"},
                {"event_type": "plangate_safe_execute", "request_id": "req-4"},
                {"event_type": "plangate_safe_execute", "request_id": "req-5"},
            ])
            
            builder = BaselineBuilder(
                ledger_path=ledger_path,
                fixed_time="2026-03-13T12:00:00Z",
            )
            snapshot = builder.build_baseline()
            
            assert snapshot.metadata.row_count == 5
            
            event_dist = snapshot.get_distribution(BaselineDimension.EVENT_TYPE)
            assert event_dist is not None
            assert event_dist.counts.get("plangate_refused", 0) == 2
            assert event_dist.counts.get("plangate_safe_execute", 0) == 3
    
    def test_build_from_sandbox_ledger(self):
        """Build baseline from sandbox ledger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "sandbox_ledger.db"
            
            self._create_sandbox_ledger(ledger_path, [
                {"event_type": "sandbox_executed", "outcome_type": "executed"},
                {"event_type": "sandbox_executed", "outcome_type": "executed"},
                {"event_type": "sandbox_refused", "outcome_type": "refused"},
                {"event_type": "sandbox_blocked", "outcome_type": "blocked"},
            ])
            
            builder = BaselineBuilder(
                sandbox_ledger_path=ledger_path,
                fixed_time="2026-03-13T12:00:00Z",
            )
            snapshot = builder.build_baseline()
            
            assert snapshot.metadata.row_count == 4
            
            outcome_dist = snapshot.get_distribution(BaselineDimension.OUTCOME_TYPE)
            assert outcome_dist is not None
            assert outcome_dist.counts.get("executed", 0) == 2
            assert outcome_dist.counts.get("refused", 0) == 1
            assert outcome_dist.counts.get("blocked", 0) == 1
    
    def test_build_extracts_decision_posture(self):
        """Builder extracts decision_posture from event types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.db"
            
            self._create_unified_ledger(ledger_path, [
                {"event_type": "plangate_refused"},
                {"event_type": "plangate_deferred"},
                {"event_type": "plangate_bounded_allow"},
                {"event_type": "plangate_safe_execute"},
                {"event_type": "plangate_safe_execute"},
            ])
            
            builder = BaselineBuilder(ledger_path=ledger_path, fixed_time="2026-03-13T12:00:00Z")
            snapshot = builder.build_baseline()
            
            posture_dist = snapshot.get_distribution(BaselineDimension.DECISION_POSTURE)
            assert posture_dist is not None
            assert posture_dist.counts.get("refuse", 0) == 1
            assert posture_dist.counts.get("defer", 0) == 1
            assert posture_dist.counts.get("bounded_allow", 0) == 1
            assert posture_dist.counts.get("safe_execute", 0) == 2
    
    def test_build_extracts_backend(self):
        """Builder extracts backend from payload."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "sandbox_ledger.db"
            
            self._create_sandbox_ledger(ledger_path, [
                {"event_type": "sandbox_executed", "outcome_type": "executed", "payload": {"backend": "local_process"}},
                {"event_type": "sandbox_executed", "outcome_type": "executed", "payload": {"backend": "local_process"}},
                {"event_type": "sandbox_executed", "outcome_type": "executed", "payload": {"backend": "container"}},
            ])
            
            builder = BaselineBuilder(sandbox_ledger_path=ledger_path, fixed_time="2026-03-13T12:00:00Z")
            snapshot = builder.build_baseline()
            
            backend_dist = snapshot.get_distribution(BaselineDimension.BACKEND)
            assert backend_dist is not None
            assert backend_dist.counts.get("local_process", 0) == 2
            assert backend_dist.counts.get("container", 0) == 1
    
    def test_build_extracts_canonical_hash_reuse(self):
        """Builder extracts canonical_hash reuse patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "sandbox_ledger.db"
            
            self._create_sandbox_ledger(ledger_path, [
                {"event_type": "sandbox_executed", "outcome_type": "executed", "canonical_hash": "hash-unique-1"},
                {"event_type": "sandbox_executed", "outcome_type": "executed", "canonical_hash": "hash-unique-2"},
                {"event_type": "sandbox_executed", "outcome_type": "executed", "canonical_hash": "hash-reused"},
                {"event_type": "sandbox_executed", "outcome_type": "executed", "canonical_hash": "hash-reused"},
            ])
            
            builder = BaselineBuilder(sandbox_ledger_path=ledger_path, fixed_time="2026-03-13T12:00:00Z")
            snapshot = builder.build_baseline()
            
            reuse_dist = snapshot.get_distribution(BaselineDimension.CANONICAL_HASH_REUSE)
            assert reuse_dist is not None
            assert reuse_dist.counts.get("unique", 0) == 2  # hash-unique-1, hash-unique-2
            assert reuse_dist.counts.get("reused_once", 0) == 1  # hash-reused (count=2)
    
    def test_build_extracts_replay_frequency(self):
        """Builder extracts replay frequency (same request_id count)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.db"
            
            self._create_unified_ledger(ledger_path, [
                {"event_type": "event", "request_id": "req-single"},
                {"event_type": "event", "request_id": "req-two"},
                {"event_type": "event", "request_id": "req-two"},
                {"event_type": "event", "request_id": "req-multi"},
                {"event_type": "event", "request_id": "req-multi"},
                {"event_type": "event", "request_id": "req-multi"},
                {"event_type": "event", "request_id": "req-multi"},
            ])
            
            builder = BaselineBuilder(ledger_path=ledger_path, fixed_time="2026-03-13T12:00:00Z")
            snapshot = builder.build_baseline()
            
            replay_dist = snapshot.get_distribution(BaselineDimension.REPLAY_FREQUENCY)
            assert replay_dist is not None
            assert replay_dist.counts.get("single", 0) == 1  # req-single
            assert replay_dist.counts.get("two", 0) == 1  # req-two
            assert replay_dist.counts.get("3-5", 0) == 1  # req-multi (count=4)
    
    def test_build_deterministic(self):
        """Same ledger produces same baseline (deterministic)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.db"
            
            self._create_unified_ledger(ledger_path, [
                {"event_type": "plangate_refused"},
                {"event_type": "plangate_safe_execute"},
            ])
            
            builder = BaselineBuilder(ledger_path=ledger_path, fixed_time="2026-03-13T12:00:00Z")
            s1 = builder.build_baseline()
            s2 = builder.build_baseline()
            
            assert s1.baseline_hash == s2.baseline_hash
    
    def test_build_with_time_range(self):
        """Builder respects time range filters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.db"
            
            self._create_unified_ledger(ledger_path, [
                {"event_type": "early_event", "timestamp_utc": "2026-01-01T00:00:00Z"},
                {"event_type": "in_range_event", "timestamp_utc": "2026-02-15T00:00:00Z"},
                {"event_type": "late_event", "timestamp_utc": "2026-04-01T00:00:00Z"},
            ])
            
            builder = BaselineBuilder(ledger_path=ledger_path, fixed_time="2026-03-13T12:00:00Z")
            snapshot = builder.build_baseline(
                time_range_start="2026-02-01T00:00:00Z",
                time_range_end="2026-03-01T00:00:00Z",
            )
            
            event_dist = snapshot.get_distribution(BaselineDimension.EVENT_TYPE)
            assert event_dist is not None
            assert event_dist.counts.get("in_range_event", 0) == 1
            assert "early_event" not in event_dist.counts
            assert "late_event" not in event_dist.counts


# -----------------------------------------------------------------------------
# BaselineStore Tests
# -----------------------------------------------------------------------------

class TestBaselineStore:
    """Tests for BaselineStore persistence."""
    
    def _make_snapshot(self, baseline_id: str = "test-baseline") -> BaselineSnapshot:
        """Create a test snapshot."""
        dist = DimensionDistribution(dimension=BaselineDimension.EVENT_TYPE)
        dist.add("test_event", count=10)
        
        metadata = BaselineMetadata(
            baseline_id=baseline_id,
            created_utc="2026-03-13T12:00:00Z",
            ledger_path="/test/ledger.db",
            row_count=100,
            time_range_start="2026-03-01T00:00:00Z",
            time_range_end="2026-03-13T00:00:00Z",
            runtime_version="0.1.0",
        )
        
        return BaselineSnapshot(
            metadata=metadata,
            distributions={BaselineDimension.EVENT_TYPE.value: dist},
        )
    
    def test_file_mode_save_load(self):
        """File mode: save and load roundtrip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = BaselineStore(tmpdir, mode="file")
            snapshot = self._make_snapshot()
            
            baseline_id = store.save(snapshot)
            loaded = store.load(baseline_id)
            
            assert loaded is not None
            assert loaded.baseline_hash == snapshot.baseline_hash
            assert loaded.metadata.baseline_id == snapshot.metadata.baseline_id
    
    def test_sqlite_mode_save_load(self):
        """SQLite mode: save and load roundtrip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "baselines.db"
            store = BaselineStore(db_path, mode="sqlite")
            snapshot = self._make_snapshot()
            
            baseline_id = store.save(snapshot)
            loaded = store.load(baseline_id)
            
            assert loaded is not None
            assert loaded.baseline_hash == snapshot.baseline_hash
            assert loaded.metadata.baseline_id == snapshot.metadata.baseline_id
    
    def test_auto_mode_directory(self):
        """Auto mode selects file mode for directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = BaselineStore(tmpdir, mode="auto")
            assert store.mode == "file"
    
    def test_auto_mode_file(self):
        """Auto mode selects sqlite mode for file with extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "store.db"
            store = BaselineStore(db_path, mode="auto")
            assert store.mode == "sqlite"
    
    def test_load_nonexistent(self):
        """Loading nonexistent baseline returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = BaselineStore(tmpdir, mode="file")
            loaded = store.load("nonexistent-id")
            assert loaded is None
    
    def test_load_by_hash(self):
        """Load baseline by content hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "baselines.db"
            store = BaselineStore(db_path, mode="sqlite")
            snapshot = self._make_snapshot()
            
            store.save(snapshot)
            loaded = store.load_by_hash(snapshot.baseline_hash)
            
            assert loaded is not None
            assert loaded.metadata.baseline_id == snapshot.metadata.baseline_id
    
    def test_load_latest(self):
        """Load most recently created baseline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "baselines.db"
            store = BaselineStore(db_path, mode="sqlite")
            
            s1 = self._make_snapshot("baseline-1")
            s1.metadata.created_utc = "2026-03-01T00:00:00Z"
            
            s2 = self._make_snapshot("baseline-2")
            s2.metadata.created_utc = "2026-03-10T00:00:00Z"
            
            s3 = self._make_snapshot("baseline-3")
            s3.metadata.created_utc = "2026-03-05T00:00:00Z"
            
            store.save(s1)
            store.save(s2)
            store.save(s3)
            
            latest = store.load_latest()
            assert latest is not None
            assert latest.metadata.baseline_id == "baseline-2"
    
    def test_list_all(self):
        """List all baselines in creation order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "baselines.db"
            store = BaselineStore(db_path, mode="sqlite")
            
            s1 = self._make_snapshot("baseline-1")
            s1.metadata.created_utc = "2026-03-01T00:00:00Z"
            
            s2 = self._make_snapshot("baseline-2")
            s2.metadata.created_utc = "2026-03-10T00:00:00Z"
            
            store.save(s1)
            store.save(s2)
            
            all_baselines = store.list_all()
            assert len(all_baselines) == 2
            assert all_baselines[0].metadata.baseline_id == "baseline-1"
            assert all_baselines[1].metadata.baseline_id == "baseline-2"
    
    def test_list_ids(self):
        """List all baseline IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "baselines.db"
            store = BaselineStore(db_path, mode="sqlite")
            
            store.save(self._make_snapshot("baseline-a"))
            store.save(self._make_snapshot("baseline-b"))
            
            ids = store.list_ids()
            assert "baseline-a" in ids
            assert "baseline-b" in ids
    
    def test_count(self):
        """Count stored baselines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "baselines.db"
            store = BaselineStore(db_path, mode="sqlite")
            
            assert store.count() == 0
            store.save(self._make_snapshot("baseline-1"))
            assert store.count() == 1
            store.save(self._make_snapshot("baseline-2"))
            assert store.count() == 2
    
    def test_exists(self):
        """Check baseline existence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "baselines.db"
            store = BaselineStore(db_path, mode="sqlite")
            
            assert not store.exists("test-baseline")
            store.save(self._make_snapshot("test-baseline"))
            assert store.exists("test-baseline")


# -----------------------------------------------------------------------------
# End-to-End Tests
# -----------------------------------------------------------------------------

class TestEndToEnd:
    """End-to-end tests: build → store → load → compare."""
    
    def _create_ledger(self, path: Path, rows: list[dict]) -> None:
        """Create a test unified ledger."""
        with sqlite3.connect(path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ledger_rows (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    plan_hash TEXT NOT NULL,
                    timestamp_utc TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'shadow',
                    payload TEXT NOT NULL
                )
            """)
            for i, row in enumerate(rows):
                conn.execute(
                    """
                    INSERT INTO ledger_rows (
                        event_id, event_type, request_id, session_id,
                        plan_hash, timestamp_utc, mode, payload
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"event-{i}",
                        row.get("event_type", "test_event"),
                        row.get("request_id", f"req-{i}"),
                        row.get("session_id", "session-1"),
                        row.get("plan_hash", "hash-1"),
                        row.get("timestamp_utc", "2026-03-13T12:00:00Z"),
                        row.get("mode", "shadow"),
                        json.dumps(row.get("payload", {})),
                    ),
                )
    
    def test_full_workflow(self):
        """Full workflow: build baseline, store, load, compare."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.db"
            store_path = Path(tmpdir) / "baselines.db"
            
            # Create initial ledger
            self._create_ledger(ledger_path, [
                {"event_type": "plangate_refused"},
                {"event_type": "plangate_safe_execute"},
                {"event_type": "plangate_safe_execute"},
            ])
            
            # Build and store baseline
            builder = BaselineBuilder(ledger_path=ledger_path, fixed_time="2026-03-13T12:00:00Z")
            baseline_v1 = builder.build_baseline()
            
            store = BaselineStore(store_path, mode="sqlite")
            store.save(baseline_v1)
            
            # Simulate behavior change: add more data
            with sqlite3.connect(ledger_path) as conn:
                for i in range(3, 10):
                    conn.execute(
                        """
                        INSERT INTO ledger_rows (
                            event_id, event_type, request_id, session_id,
                            plan_hash, timestamp_utc, mode, payload
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f"event-{i}",
                            "plangate_refused",  # More refusals
                            f"req-{i}",
                            "session-1",
                            "hash-1",
                            "2026-03-13T12:00:00Z",
                            "shadow",
                            "{}",
                        ),
                    )
            
            # Build new baseline
            baseline_v2 = builder.build_baseline()
            
            # Load stored baseline
            loaded_v1 = store.load(baseline_v1.metadata.baseline_id)
            assert loaded_v1 is not None
            
            # Compare baselines
            drift = loaded_v1.compare(baseline_v2)
            
            # Should show drift because distribution changed
            assert drift["hash_match"] is False
            assert drift["overall_drift_score"] > 0.0
    
    def test_determinism_across_sessions(self):
        """Same data produces same baseline across separate builds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.db"
            
            self._create_ledger(ledger_path, [
                {"event_type": "plangate_refused", "request_id": "req-1"},
                {"event_type": "plangate_safe_execute", "request_id": "req-2"},
            ])
            
            # Build twice with same fixed time
            builder1 = BaselineBuilder(ledger_path=ledger_path, fixed_time="2026-03-13T12:00:00Z")
            s1 = builder1.build_baseline()
            
            builder2 = BaselineBuilder(ledger_path=ledger_path, fixed_time="2026-03-13T12:00:00Z")
            s2 = builder2.build_baseline()
            
            assert s1.baseline_hash == s2.baseline_hash
            
            drift = s1.compare(s2)
            assert drift["hash_match"] is True
            assert drift["overall_drift_score"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
