"""
Observation Layer — M4.x drift detection and governance escalation.

This package provides runtime observation, drift detection, collapse tracking,
and GREG (Governance Review and Escalation Group) escalation capabilities.

M4.5 GREG Escalation:
- EscalationPolicy: threshold-based escalation decision logic
- GREGBundle: evidence bundle for governance escalation
- BundleBuilder: constructs bundles from ledger/observation data
"""

from runtime.observation.greg_escalation import (
    EscalationPolicy,
    EscalationThresholds,
    EscalationDecision,
    EscalationType,
    EscalationSeverity,
)
from runtime.observation.greg_bundle import (
    GREGBundle,
    EscalationEvidence,
    MismatchClassification,
    CollapseClassification,
)
from runtime.observation.bundle_builder import BundleBuilder

__all__ = [
    "EscalationPolicy",
    "EscalationThresholds",
    "EscalationDecision",
    "EscalationType",
    "EscalationSeverity",
    "GREGBundle",
    "EscalationEvidence",
    "MismatchClassification",
    "CollapseClassification",
    "BundleBuilder",
]
