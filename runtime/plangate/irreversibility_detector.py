"""
Plan-Gate IrreversibilityDetector — M3.3B decomposition.

Determines whether the request is reversible, boundary-adjacent, or irreversible.
MVP deterministic rules; not a full production boundary policy engine.

Output is an explicit IrreversibilityResult object, not hidden booleans in PlanGateService.
"""

from __future__ import annotations

from typing import Any

from runtime.plangate.contracts import IrreversibilityResult


class IrreversibilityDetector:
    """
    Detects whether the request involves an irreversible action or boundary crossing.

    MVP implementation supports:
    - Clearly dangerous commands → boundary_detected=True, irreversible=True
    - Explicit request flags (boundary_detected=True, irreversible=True)
    - Safe commands → boundary_detected=False, irreversible=False

    This is a first-class subcomponent with explicit, machine-readable output.
    """

    # Commands that are clearly dangerous and irreversible.
    # Aligned with existing REFUSED_COMMANDS in PlanGateService.
    DANGEROUS_COMMANDS: frozenset[str] = frozenset({"curl", "wget", "rm", "mkfs", "dd"})

    def detect(self, request: dict[str, Any]) -> IrreversibilityResult:
        """
        Detect irreversibility and boundaries for the request.

        Request fields examined:
        - boundary_detected: If True, explicit boundary hint.
        - irreversible: If True, explicit irreversibility hint.
        - plan_gate_refuse: If True, implies boundary crossing.
        - command: If command is in DANGEROUS_COMMANDS, classified as irreversible.

        Returns:
            IrreversibilityResult with boundary_detected, irreversible, boundary_reason, boundary_class.
        """
        # Check for explicit boundary/irreversibility hints
        explicit_boundary = request.get("boundary_detected") is True
        explicit_irreversible = request.get("irreversible") is True

        if explicit_boundary or explicit_irreversible:
            return IrreversibilityResult(
                boundary_detected=explicit_boundary or explicit_irreversible,
                irreversible=explicit_irreversible,
                boundary_reason="Boundary/irreversibility explicitly flagged by request hint",
                boundary_class="request_hint",
            )

        # Check for explicit refuse hint (implies boundary crossing)
        if request.get("plan_gate_refuse") is True:
            return IrreversibilityResult(
                boundary_detected=True,
                irreversible=True,
                boundary_reason="Boundary detected via request hint (plan_gate_refuse=True)",
                boundary_class="request_hint",
            )

        # Check for dangerous command
        command = request.get("command")
        if command and isinstance(command, (list, tuple)):
            cmd_name = self._extract_command_name(command)
            if cmd_name in self.DANGEROUS_COMMANDS:
                return IrreversibilityResult(
                    boundary_detected=True,
                    irreversible=True,
                    boundary_reason=f"Command '{cmd_name}' classified as dangerous/irreversible",
                    boundary_class="dangerous_command",
                )

        # Default: no boundary, reversible
        return IrreversibilityResult(
            boundary_detected=False,
            irreversible=False,
            boundary_reason="No boundary or irreversibility detected",
            boundary_class=None,
        )

    def _extract_command_name(self, command: list | tuple) -> str:
        """Extract the base command name from a command list/tuple."""
        if not command:
            return ""
        cmd_name = str(command[0] or "").strip()
        # Handle paths like /usr/bin/curl → curl
        if "/" in cmd_name:
            cmd_name = cmd_name.split("/")[-1]
        return cmd_name
