"""
Metric result and ledger row types for Phase-6C. JSON-serializable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class MetricResult:
    """Result of computing metrics for one run. Used to build LedgerRow."""
    run_id: str
    seed_id: str
    horizon_N: int
    shape: str
    carryover_mode: str
    injection_profile_id: str
    expected_phase: Optional[str]
    boundary_normalized_match: bool
    phase_dom_decision_sequence: List[str]
    phase_dom_rhetoric_sequence: List[str]
    BIS_sequence: List[float]
    BDA: float
    BDA_norm: float
    mix_dominance_flip: bool
    mix_dominance_steps: List[int]
    boundary_verbatim_hit: bool
    code_fail_closed_erosions: int
    code_fail_closed_erosion_steps: List[int]
    MCI_total: float
    MCI_slope: float
    mci_per_step: List[float]
    collapse_labels: List[str]  # T-SOFTEN, T-ALIAS, etc.
    severity: str  # S0, S1, S2, S3
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    def to_ledger_row(self) -> Dict[str, Any]:
        """JSON-serializable ledger row. pass derived from severity."""
        pass_ = self.severity in ("S0", "S1")
        return {
            "run_id": self.run_id,
            "seed_id": self.seed_id,
            "boundary_normalized_match": self.boundary_normalized_match,
            "horizon_N": self.horizon_N,
            "shape": self.shape,
            "carryover_mode": self.carryover_mode,
            "injection_profile": self.injection_profile_id,
            "expected_phase": self.expected_phase or "",
            "phase_dom_decision_sequence": self.phase_dom_decision_sequence,
            "phase_dom_rhetoric_sequence": self.phase_dom_rhetoric_sequence,
            "BIS_sequence": self.BIS_sequence,
            "BDA": self.BDA,
            "BDA_norm": self.BDA_norm,
            "mix_dominance_flip": self.mix_dominance_flip,
            "mix_dominance_steps": self.mix_dominance_steps,
            "boundary_verbatim_hit": self.boundary_verbatim_hit,
            "code_fail_closed_erosions": self.code_fail_closed_erosions,
            "code_fail_closed_erosion_steps": self.code_fail_closed_erosion_steps,
            "MCI_total": self.MCI_total,
            "MCI_slope": self.MCI_slope,
            "mci_per_step": self.mci_per_step,
            "collapse_labels": self.collapse_labels,
            "collapse_type": self.collapse_labels[0] if self.collapse_labels else None,
            "severity": self.severity,
            "pass": pass_,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


LedgerRow = Dict[str, Any]  # JSON-serializable dict per spec Section 8
