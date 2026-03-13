"""
Plan-Gate command utilities — shared helpers for command processing.

Centralizes command extraction logic to prevent semantic drift between
AuthorityValidator and IrreversibilityDetector.
"""

from __future__ import annotations

from typing import Any


def extract_command_name(command: Any) -> str:
    """
    Extract the base command name from a command specification.

    Handles:
    - List/tuple commands: ["curl", "http://x.com"] → "curl"
    - Path commands: ["/usr/bin/curl", "..."] → "curl"
    - Empty/invalid commands: [] or None → ""

    Args:
        command: Command specification (list, tuple, or other).

    Returns:
        Base command name as string, or empty string if invalid.
    """
    if not command or not isinstance(command, (list, tuple)):
        return ""

    if len(command) == 0:
        return ""

    cmd_name = str(command[0] or "").strip()

    # Handle paths like /usr/bin/curl → curl
    if "/" in cmd_name:
        cmd_name = cmd_name.split("/")[-1]

    return cmd_name
