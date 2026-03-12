"""
Plan-Gate AuthorityValidator — M3.3B decomposition.

Determines whether authority is sufficient for the requested action.
MVP deterministic rules; not a full enterprise RBAC/approval engine.

Output is an explicit AuthorityResult object, not hidden booleans in PlanGateService.
"""

from __future__ import annotations

from typing import Any

from runtime.plangate.contracts import AuthorityResult


class AuthorityValidator:
    """
    Validates whether the requester has sufficient authority for the action.

    MVP implementation supports:
    - Explicit request hints (authority_denied=True, plan_gate_refuse=True)
    - Refused command classes implying authority failure
    - Default to authority_ok=True for safe MVP behavior

    This is a first-class subcomponent with explicit, machine-readable output.
    """

    # Commands that imply authority failure when detected (dangerous commands).
    # These are aligned with the existing REFUSED_COMMANDS in PlanGateService.
    AUTHORITY_DENYING_COMMANDS: frozenset[str] = frozenset({"curl", "wget", "rm", "mkfs", "dd"})

    def validate(self, request: dict[str, Any]) -> AuthorityResult:
        """
        Validate authority for the request.

        Request fields examined:
        - authority_denied: If True, explicitly denies authority.
        - plan_gate_refuse: If True, implies authority failure via hint.
        - command: If command is in AUTHORITY_DENYING_COMMANDS, authority fails.

        Returns:
            AuthorityResult with authority_ok, authority_reason, authority_source.
        """
        # Check for explicit authority denial hint
        if request.get("authority_denied") is True:
            return AuthorityResult(
                authority_ok=False,
                authority_reason="Authority explicitly denied by request (authority_denied=True)",
                authority_source="request_hint",
            )

        # Check for explicit refuse hint (implies authority failure)
        if request.get("plan_gate_refuse") is True:
            return AuthorityResult(
                authority_ok=False,
                authority_reason="Authority denied by request hint (plan_gate_refuse=True)",
                authority_source="request_hint",
            )

        # Check for dangerous command (authority-denying command class)
        command = request.get("command")
        if command and isinstance(command, (list, tuple)):
            cmd_name = self._extract_command_name(command)
            if cmd_name in self.AUTHORITY_DENYING_COMMANDS:
                return AuthorityResult(
                    authority_ok=False,
                    authority_reason=f"Authority denied: command '{cmd_name}' is not authorized",
                    authority_source="dangerous_command_rule",
                )

        # Default: authority granted
        return AuthorityResult(
            authority_ok=True,
            authority_reason="Authority granted: no denial conditions met",
            authority_source="default",
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
