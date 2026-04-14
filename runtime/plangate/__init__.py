"""
Plan-Gate — M3.3 mandatory pre-sandbox decision gate.

All execution paths must flow through Plan-Gate before sandbox.
Postures: refuse, defer, bounded_allow, safe_execute.
Only safe_execute may reach sandbox.

M3.3B Internal Decomposition:
Plan-Gate is now internally decomposed into explicit first-class subcomponents:
- AuthorityValidator → AuthorityResult
- IrreversibilityDetector → IrreversibilityResult
- JudgeGate → PlanGateDecision

External PlanGateService contract is unchanged.

Naming (do not confuse with HTTP / CLI):
- **This package** is the M3.3 **pre-sandbox** gate (`PlanGateService`).
- **`runtime/plan_gate_service/`** — HTTP PlanRequest v0.1 surface; **`runtime/plan_gate_stub/`** — protocol/CLI stub.
- Canonical map: `runtime/README.md` (section *Execution gate*).
"""

from runtime.plangate.authority_validator import AuthorityValidator
from runtime.plangate.command_utils import extract_command_name
from runtime.plangate.contracts import AuthorityResult, IrreversibilityResult, JudgeInput
from runtime.plangate.irreversibility_detector import IrreversibilityDetector
from runtime.plangate.judge_gate import JudgeGate
from runtime.plangate.plangate_decision import PlanGateDecision, Posture
from runtime.plangate.plangate_service import PlanGateService

__all__ = [
    # External contract (unchanged)
    "PlanGateDecision",
    "PlanGateService",
    "Posture",
    # Internal subcomponents (M3.3B)
    "AuthorityValidator",
    "AuthorityResult",
    "IrreversibilityDetector",
    "IrreversibilityResult",
    "JudgeGate",
    "JudgeInput",
    # Shared utilities
    "extract_command_name",
]
