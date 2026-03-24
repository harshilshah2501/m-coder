"""
Command Normalizer — M4.1 single entrypoint from request to CanonicalExecutionIntent.

Parse command once only. Normalize executable, argv, working_dir, env_delta.
Compute canonical_hash. Reject malformed or ambiguous execution requests.
No downstream layer may re-parse the same raw command.
"""

from __future__ import annotations

import shlex
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

from runtime.integrity.canonical_intent import (
    CanonicalExecutionIntent,
    compute_canonical_hash,
)


class NormalizationError(Exception):
    """Raised when request cannot be normalized to a valid CanonicalExecutionIntent."""

    pass


def _parse_command(command: str | list[str]) -> list[str]:
    """
    Parse command into argv. Single place for parsing; deterministic.
    - If str: shlex.split (strip, handle quotes).
    - If list: normalize (strip each element, drop empty).
    Raises NormalizationError on invalid/empty result.
    """
    if isinstance(command, str):
        s = (command or "").strip()
        if not s:
            raise NormalizationError("Empty or missing command")
        try:
            argv = shlex.split(s)
        except ValueError as e:
            raise NormalizationError(f"Invalid command string: {e}") from e
    elif isinstance(command, (list, tuple)):
        argv = [str(x).strip() for x in command if str(x).strip()]
        if not argv:
            raise NormalizationError("Empty or invalid command list")
    else:
        raise NormalizationError("command must be string or list of strings")
    return argv


def _normalize_working_dir(repo_root: str | None, default_cwd: str = "") -> str:
    """Return absolute path for working directory. Resolve . and ..; no symlink resolution."""
    base = (repo_root or default_cwd or ".").strip()
    if not base:
        base = "."
    try:
        path = Path(base).resolve()
    except (OSError, PermissionError) as e:
        raise NormalizationError(f"Working directory is not accessible: {base} ({e})") from e
    return str(path)


def _normalize_env_delta(env: dict[str, Any] | None) -> tuple[tuple[str, str], ...]:
    """Return (key, value) pairs sorted by key; keys and values as strings."""
    if not env:
        return ()
    out: list[tuple[str, str]] = []
    for k, v in sorted(env.items(), key=lambda x: x[0]):
        out.append((str(k).strip(), str(v) if v is not None else ""))
    return tuple(out)


class CommandNormalizer:
    """
    Builds CanonicalExecutionIntent from execute request.
    Single entrypoint; parse command once; reject malformed.
    """

    def __init__(self, default_working_dir: str = ""):
        """
        Args:
            default_working_dir: Used when repo_root is missing or empty (e.g. Path.cwd()).
        """
        self.default_working_dir = default_working_dir or str(Path.cwd())

    def normalize(self, request: dict[str, Any]) -> CanonicalExecutionIntent:
        """
        Build CanonicalExecutionIntent from request.

        Expects request keys: request_id, repo_root, command (str or list),
        plan_hash (optional), revision, branch, task_id (optional), env (optional),
        timeout_seconds (optional). working_dir is derived from repo_root.

        Raises:
            NormalizationError: Missing required fields or invalid command.
        """
        request_id = request.get("request_id") or f"req-{uuid.uuid4()}"
        plan_hash = request.get("plan_hash") or ""
        repo_root = request.get("repo_root")
        command = request.get("command")
        if command is None:
            raise NormalizationError("Missing required field: command")
        if not request.get("repo_root") and repo_root is None:
            repo_root = self.default_working_dir

        argv = _parse_command(command)
        executable = argv[0] if argv else ""
        # repo_root: request repo_root or working_dir or default (normalized)
        repo_root_raw = request.get("repo_root") or request.get("working_dir") or repo_root or self.default_working_dir or ""
        repo_root_normalized = _normalize_working_dir(repo_root_raw, self.default_working_dir)
        # working_dir: explicit > repo_root > default
        wd_raw = request.get("working_dir") or request.get("repo_root") or repo_root or ""
        working_dir = _normalize_working_dir(wd_raw, self.default_working_dir)
        env_delta = _normalize_env_delta(request.get("env"))
        timeout_seconds = request.get("timeout_seconds")
        if timeout_seconds is not None:
            try:
                timeout_seconds = int(timeout_seconds)
            except (TypeError, ValueError):
                timeout_seconds = None
        capture_artifacts = tuple(
            str(x).strip() for x in (request.get("capture_artifacts") or []) if str(x).strip()
        )
        intent_id = request.get("intent_id") or f"{request_id}-{uuid.uuid4().hex[:12]}"
        execution_surface = request.get("execution_surface") or ""
        branch = request.get("branch") or ""

        # Build intent with placeholder hash; then set real hash (intent_id excluded from hash)
        intent = CanonicalExecutionIntent(
            request_id=request_id,
            plan_hash=plan_hash,
            intent_id=intent_id,
            canonical_hash="",
            executable=executable,
            argv=tuple(argv),
            working_dir=working_dir,
            env_delta=env_delta,
            timeout_seconds=timeout_seconds,
            capture_artifacts=capture_artifacts,
            repo_root=repo_root_normalized,
            execution_surface=execution_surface,
            branch=branch,
        )
        return replace(intent, canonical_hash=compute_canonical_hash(intent))
