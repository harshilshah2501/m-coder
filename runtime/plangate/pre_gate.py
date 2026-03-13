"""
Pre-Gate Deterministic Guard — M4.1 hard-fail before Plan-Gate.

Evaluates CanonicalExecutionIntent only. Pass or refuse (with category).
Does not mutate intent. Does not replace Plan-Gate posture logic.
Per PRE_GATE_DESIGN_v1.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from runtime.integrity.canonical_intent import CanonicalExecutionIntent


# Protected branches: no write/execution on these (deterministic list).
PROTECTED_BRANCHES = frozenset({"main", "master"})
PROTECTED_BRANCH_PREFIX = "release/"

# Executables that imply unsupported network execution (hard-fail before Plan-Gate).
UNSUPPORTED_NETWORK_EXECUTABLES = frozenset({"curl", "wget"})

# Executables/patterns that imply destructive filesystem or irreversible system actions.
DESTRUCTIVE_EXECUTABLES = frozenset({"rm", "mkfs", "dd", "format", "shred"})
IRREVERSIBLE_PATTERNS = re.compile(
    r"\b(drop\s+(database|table)|revoke|delete\s+immutable|rm\s+-rf\s+/|format\s+\w+|mkfs)\b",
    re.IGNORECASE,
)
# Dangerous path roots: only refuse when an argv token is exactly one of these (not substring).
DANGEROUS_PATH_ROOTS = frozenset({"/", "/usr", "/etc", "/bin", "/sys", "/boot"})


@dataclass(frozen=True)
class GuardResult:
    """Result of DeterministicGuard.evaluate. Pass or refuse with category."""

    passed: bool
    refused: bool
    category: str  # empty if passed; one of the five categories if refused
    reason: str

    @classmethod
    def pass_result(cls) -> GuardResult:
        return cls(passed=True, refused=False, category="", reason="")

    @classmethod
    def refuse(cls, category: str, reason: str) -> GuardResult:
        return cls(passed=False, refused=True, category=category, reason=reason)


class DeterministicGuard:
    """
    Hard-fail guard before Plan-Gate. Evaluates CanonicalExecutionIntent only.

    Refusal categories (per PRE_GATE_DESIGN_v1.md):
    - protected_branch_mutation
    - destructive_filesystem_commands
    - irreversible_system_actions
    - authority_mismatch
    - unsupported_network_execution
    """

    def __init__(
        self,
        protected_branches: frozenset[str] | None = None,
        protected_prefix: str = PROTECTED_BRANCH_PREFIX,
    ):
        self.protected_branches = protected_branches or PROTECTED_BRANCHES
        self.protected_prefix = protected_prefix

    def evaluate(self, intent: CanonicalExecutionIntent) -> GuardResult:
        """
        Evaluate intent. Returns pass or refuse with category.
        Does not mutate intent.
        """
        # 1. Protected branch mutation
        branch = (getattr(intent, "branch", None) or "").strip()
        if branch:
            if branch in self.protected_branches:
                return GuardResult.refuse(
                    "protected_branch_mutation",
                    f"Protected branch '{branch}' may not be targeted for execution.",
                )
            if self.protected_prefix and branch.startswith(self.protected_prefix):
                return GuardResult.refuse(
                    "protected_branch_mutation",
                    f"Branch '{branch}' matches protected prefix '{self.protected_prefix}'.",
                )

        # 2. Unsupported network execution (curl, wget)
        exe = (intent.executable or "").strip()
        if "/" in exe:
            exe = exe.split("/")[-1]
        if exe.lower() in UNSUPPORTED_NETWORK_EXECUTABLES:
            return GuardResult.refuse(
                "unsupported_network_execution",
                f"Outbound network execution '{intent.executable}' is not allowed.",
            )

        # 3. Destructive filesystem commands
        if exe.lower() in DESTRUCTIVE_EXECUTABLES:
            return GuardResult.refuse(
                "destructive_filesystem_commands",
                f"Destructive filesystem command '{intent.executable}' is not allowed.",
            )
        # 3b. rm/shred with argv token exactly a dangerous root (not substring; avoids "rm -rf /tmp" false positive)
        if exe.lower() in ("rm", "shred"):
            for arg in intent.argv:
                if arg in DANGEROUS_PATH_ROOTS:
                    return GuardResult.refuse(
                        "destructive_filesystem_commands",
                        "Bulk destructive path or system path not allowed.",
                    )

        argv_str = " ".join(intent.argv) if intent.argv else ""
        # 4. Irreversible system actions (pattern in argv)
        if IRREVERSIBLE_PATTERNS.search(argv_str):
            return GuardResult.refuse(
                "irreversible_system_actions",
                "Command matches irreversible system action pattern.",
            )

        # 5. Authority mismatch (explicit hint only in MVP; no role/token parsing)
        auth_ctx = (getattr(intent, "authority_context", None) or "").strip()
        if auth_ctx and auth_ctx.lower() == "mismatch":
            return GuardResult.refuse(
                "authority_mismatch",
                "Authority context indicates mismatch.",
            )

        return GuardResult.pass_result()
