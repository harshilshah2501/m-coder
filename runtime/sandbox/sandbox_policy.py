"""
Sandbox Policy — M3.2 execution constraints.

Defines what commands are allowed, time limits, and other guardrails.
Policy is enforced before execution (fail-closed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SandboxPolicy:
    """
    Execution constraints for the sandbox.
    
    The sandbox runner validates all commands against policy before execution.
    Violations raise SandboxPolicyViolation (fail-closed).
    
    Attributes:
        allowed_commands: Set of allowed executable names (basename only).
        max_execution_time: Maximum execution time in seconds.
        max_output_bytes: Maximum combined stdout/stderr size in bytes.
        allowed_working_dirs: If non-empty, restricts working directories.
        env_allowlist: Environment variables allowed to pass through.
        env_blocklist: Environment variables that must be stripped.
    """

    allowed_commands: set[str] = field(default_factory=lambda: {
        "pytest",
        "python",
        "python3",
        "ruff",
        "black",
        "mypy",
        "pylint",
        "flake8",
        "isort",
        "pip",
        "pip3",
        "poetry",
        "npm",
        "node",
        "npx",
        "yarn",
        "pnpm",
        "tsc",
        "eslint",
        "prettier",
        "go",
        "gofmt",
        "cargo",
        "rustfmt",
        "clippy",
        "make",
        "cmake",
        "cat",
        "echo",
        "ls",
        "head",
        "tail",
        "wc",
        "grep",
        "find",
        "diff",
        "touch",
        "mkdir",
        "rm",
        "cp",
        "mv",
    })
    
    max_execution_time: int = 30
    max_output_bytes: int = 1_000_000  # 1MB
    
    allowed_working_dirs: set[str] = field(default_factory=set)
    env_allowlist: set[str] = field(default_factory=lambda: {
        "PATH",
        "HOME",
        "USER",
        "LANG",
        "LC_ALL",
        "TERM",
        "PYTHONPATH",
        "VIRTUAL_ENV",
        "NODE_PATH",
        "GOPATH",
        "CARGO_HOME",
        "RUSTUP_HOME",
    })
    env_blocklist: set[str] = field(default_factory=lambda: {
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "GITLAB_TOKEN",
        "NPM_TOKEN",
        "PYPI_TOKEN",
        "DATABASE_URL",
        "DB_PASSWORD",
        "SECRET_KEY",
        "API_KEY",
        "PRIVATE_KEY",
    })

    def validate_command(self, command: list[str]) -> tuple[bool, str]:
        """
        Validate a command against policy.
        
        Args:
            command: Command as list of arguments (first element is executable).
            
        Returns:
            Tuple of (is_valid, reason). If is_valid is False, reason explains why.
        """
        if not command:
            return False, "Empty command"
        
        executable = command[0]
        
        # Extract basename for validation (handles /usr/bin/python etc.)
        basename = Path(executable).name
        
        if basename not in self.allowed_commands:
            return False, f"Command '{basename}' not in allowed list"
        
        return True, ""

    def validate_working_dir(self, working_dir: Path) -> tuple[bool, str]:
        """
        Validate working directory against policy.
        
        Args:
            working_dir: The working directory to validate.
            
        Returns:
            Tuple of (is_valid, reason). If is_valid is False, reason explains why.
        """
        if not self.allowed_working_dirs:
            # No restriction if allowlist is empty
            return True, ""
        
        working_dir_str = str(working_dir.resolve())
        
        for allowed in self.allowed_working_dirs:
            allowed_path = str(Path(allowed).resolve())
            if working_dir_str == allowed_path or working_dir_str.startswith(allowed_path + "/"):
                return True, ""
        
        return False, f"Working directory '{working_dir}' not in allowed list"

    def filter_environment(self, env: dict[str, str] | None) -> dict[str, str]:
        """
        Filter environment variables according to policy.
        
        Removes blocklisted variables and keeps only allowlisted ones.
        
        Args:
            env: Environment dict to filter. If None, returns empty dict.
            
        Returns:
            Filtered environment dict.
        """
        if env is None:
            return {}
        
        filtered = {}
        for key, value in env.items():
            if key in self.env_blocklist:
                continue
            if key in self.env_allowlist or key.startswith("SANDBOX_"):
                filtered[key] = value
        
        return filtered

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation for audit."""
        return {
            "allowed_commands": sorted(self.allowed_commands),
            "max_execution_time": self.max_execution_time,
            "max_output_bytes": self.max_output_bytes,
            "allowed_working_dirs": sorted(self.allowed_working_dirs),
            "env_allowlist": sorted(self.env_allowlist),
            "env_blocklist": sorted(self.env_blocklist),
        }

    @classmethod
    def strict(cls) -> SandboxPolicy:
        """
        Create a strict policy with minimal allowed commands.
        
        Use for high-risk contexts where only essential commands should run.
        """
        return cls(
            allowed_commands={
                "python",
                "python3",
                "pytest",
                "ruff",
                "mypy",
            },
            max_execution_time=15,
            max_output_bytes=500_000,
        )

    @classmethod
    def permissive(cls) -> SandboxPolicy:
        """
        Create a permissive policy with extended allowed commands.
        
        Use for development/testing contexts with lower risk tolerance.
        """
        policy = cls()
        policy.max_execution_time = 120
        policy.max_output_bytes = 5_000_000
        return policy
