"""
M4.2 Baseline Models — Data structures for drift baseline artifacts.

Defines baseline dimensions and snapshot structure for deterministic
behavioral baselining over ledger evidence.

Dimensions tracked:
- event_type: Distribution of ledger event types
- outcome_type: Distribution of sandbox outcomes (refused/blocked/executed)
- decision_posture: Distribution of Plan-Gate postures
- refusal_reason: Distribution of refusal reason codes
- backend: Distribution of execution backends
- execution_surface: Distribution of execution surfaces
- replay_frequency: Distribution of request replays (same request_id count)
- canonical_hash_reuse: Distribution of canonical_hash reuse patterns
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class BaselineDimension(str, Enum):
    """Baseline dimension identifiers for behavioral tracking."""
    
    EVENT_TYPE = "event_type"
    OUTCOME_TYPE = "outcome_type"
    DECISION_POSTURE = "decision_posture"
    REFUSAL_REASON = "refusal_reason"
    BACKEND = "backend"
    EXECUTION_SURFACE = "execution_surface"
    REPLAY_FREQUENCY = "replay_frequency"
    CANONICAL_HASH_REUSE = "canonical_hash_reuse"


@dataclass
class DimensionDistribution:
    """
    Distribution of values for a single baseline dimension.
    
    Stores counts for each observed value and computes normalized frequencies.
    Deterministic: same input data → same distribution.
    """
    
    dimension: BaselineDimension
    counts: dict[str, int] = field(default_factory=dict)
    total: int = 0
    
    def add(self, value: str, count: int = 1) -> None:
        """Add count(s) for a value."""
        if value not in self.counts:
            self.counts[value] = 0
        self.counts[value] += count
        self.total += count
    
    def get_frequency(self, value: str) -> float:
        """Get normalized frequency for a value (0.0 to 1.0)."""
        if self.total == 0 or value not in self.counts:
            return 0.0
        return self.counts[value] / self.total
    
    def get_all_frequencies(self) -> dict[str, float]:
        """Get all normalized frequencies."""
        if self.total == 0:
            return {}
        return {k: v / self.total for k, v in sorted(self.counts.items())}
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to deterministic dictionary."""
        return {
            "dimension": self.dimension.value,
            "counts": dict(sorted(self.counts.items())),
            "total": self.total,
            "frequencies": self.get_all_frequencies(),
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DimensionDistribution:
        """Deserialize from dictionary."""
        dist = cls(
            dimension=BaselineDimension(d["dimension"]),
            counts=dict(d.get("counts", {})),
            total=d.get("total", 0),
        )
        return dist


@dataclass
class BaselineMetadata:
    """
    Metadata for a baseline snapshot.
    
    Captures provenance information for audit and replay.
    """
    
    baseline_id: str
    created_utc: str
    ledger_path: str
    row_count: int
    time_range_start: str
    time_range_end: str
    runtime_version: str
    schema_version: str = "baseline.v0.1"
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "baseline_id": self.baseline_id,
            "schema_version": self.schema_version,
            "created_utc": self.created_utc,
            "ledger_path": self.ledger_path,
            "row_count": self.row_count,
            "time_range_start": self.time_range_start,
            "time_range_end": self.time_range_end,
            "runtime_version": self.runtime_version,
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> BaselineMetadata:
        """Deserialize from dictionary."""
        return cls(
            baseline_id=d["baseline_id"],
            created_utc=d["created_utc"],
            ledger_path=d["ledger_path"],
            row_count=d["row_count"],
            time_range_start=d["time_range_start"],
            time_range_end=d["time_range_end"],
            runtime_version=d["runtime_version"],
            schema_version=d.get("schema_version", "baseline.v0.1"),
        )


def _canonical_json(obj: Any) -> bytes:
    """Stable JSON serialization: sorted keys, UTF-8."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _compute_baseline_hash(distributions: dict[str, DimensionDistribution]) -> str:
    """
    Compute deterministic hash of baseline distributions.
    
    Same distributions → same hash. Used for baseline identity.
    """
    content = {
        dim: dist.to_dict() 
        for dim, dist in sorted(distributions.items())
    }
    return hashlib.sha256(_canonical_json(content)).hexdigest()


@dataclass
class BaselineSnapshot:
    """
    Complete baseline snapshot capturing behavioral distributions.
    
    Immutable after creation. Deterministic: same ledger evidence → same snapshot.
    
    Contains:
    - metadata: Provenance information
    - distributions: Per-dimension behavioral distributions
    - baseline_hash: Deterministic hash of distributions for identity
    """
    
    metadata: BaselineMetadata
    distributions: dict[str, DimensionDistribution] = field(default_factory=dict)
    baseline_hash: str = ""
    
    def __post_init__(self) -> None:
        """Compute baseline_hash if not set."""
        if not self.baseline_hash and self.distributions:
            self.baseline_hash = _compute_baseline_hash(self.distributions)
    
    def get_distribution(self, dimension: BaselineDimension) -> DimensionDistribution | None:
        """Get distribution for a specific dimension."""
        return self.distributions.get(dimension.value)
    
    def compare(self, other: BaselineSnapshot) -> dict[str, Any]:
        """
        Compare this baseline to another, returning drift metrics.
        
        Returns per-dimension drift scores and an overall drift indicator.
        Deterministic comparison using normalized frequencies.
        """
        drift_report: dict[str, Any] = {
            "baseline_hash_self": self.baseline_hash,
            "baseline_hash_other": other.baseline_hash,
            "hash_match": self.baseline_hash == other.baseline_hash,
            "dimension_drifts": {},
            "new_values": {},
            "missing_values": {},
        }
        
        all_dims = set(self.distributions.keys()) | set(other.distributions.keys())
        
        for dim in sorted(all_dims):
            self_dist = self.distributions.get(dim)
            other_dist = other.distributions.get(dim)
            
            if self_dist is None:
                drift_report["dimension_drifts"][dim] = {
                    "status": "new_dimension",
                    "drift_score": 1.0,
                }
                continue
            
            if other_dist is None:
                drift_report["dimension_drifts"][dim] = {
                    "status": "missing_dimension",
                    "drift_score": 1.0,
                }
                continue
            
            self_freqs = self_dist.get_all_frequencies()
            other_freqs = other_dist.get_all_frequencies()
            
            all_values = set(self_freqs.keys()) | set(other_freqs.keys())
            new_vals = set(other_freqs.keys()) - set(self_freqs.keys())
            missing_vals = set(self_freqs.keys()) - set(other_freqs.keys())
            
            if new_vals:
                drift_report["new_values"][dim] = sorted(new_vals)
            if missing_vals:
                drift_report["missing_values"][dim] = sorted(missing_vals)
            
            total_drift = 0.0
            for val in all_values:
                self_freq = self_freqs.get(val, 0.0)
                other_freq = other_freqs.get(val, 0.0)
                total_drift += abs(self_freq - other_freq)
            
            drift_report["dimension_drifts"][dim] = {
                "status": "compared",
                "drift_score": total_drift / 2,
                "value_count_self": len(self_freqs),
                "value_count_other": len(other_freqs),
            }
        
        drift_scores = [
            d["drift_score"] 
            for d in drift_report["dimension_drifts"].values()
        ]
        drift_report["overall_drift_score"] = (
            sum(drift_scores) / len(drift_scores) if drift_scores else 0.0
        )
        
        return drift_report
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to deterministic dictionary."""
        return {
            "schema_version": "baseline.v0.1",
            "metadata": self.metadata.to_dict(),
            "distributions": {
                dim: dist.to_dict() 
                for dim, dist in sorted(self.distributions.items())
            },
            "baseline_hash": self.baseline_hash,
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> BaselineSnapshot:
        """Deserialize from dictionary."""
        metadata = BaselineMetadata.from_dict(d["metadata"])
        distributions = {
            dim: DimensionDistribution.from_dict(dist_data)
            for dim, dist_data in d.get("distributions", {}).items()
        }
        return cls(
            metadata=metadata,
            distributions=distributions,
            baseline_hash=d.get("baseline_hash", ""),
        )
