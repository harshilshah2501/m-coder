"""
Path normalization for Windows <-> WSL scenarios.

Provides deterministic path conversion between:
- Windows paths: C:\\Users\\user\\project
- WSL paths: /mnt/c/Users/user/project
- POSIX paths: /home/user/project

Normalization rules (in precedence order):
1. Detect input path type (Windows, WSL, POSIX)
2. Convert to canonical POSIX form with forward slashes
3. For Windows paths, convert drive letter to /mnt/{drive}/...
4. Resolve symlinks and normalize case (for Windows compatibility)
5. Remove trailing slashes
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Tuple, Optional


@dataclass
class PathNormalizationResult:
    """
    Result of path normalization.

    Attributes:
        canonical_path: Normalized POSIX-style path.
        original_path: Original input path.
        detected_type: Detected input type ('windows', 'wsl', 'posix', 'unknown').
        was_normalized: True if any transformation was applied.
        warnings: List of warnings during normalization.
    """

    canonical_path: str
    original_path: str
    detected_type: str
    was_normalized: bool
    warnings: list


class PathNormalizer:
    """
    Deterministic path normalizer for Windows <-> WSL scenarios.

    Conversion rules:
    - Windows drive letter C: -> /mnt/c/
    - Windows backslashes -> forward slashes
    - UNC paths \\\\server\\share -> /mnt/server/share (best effort)
    - Symlinks resolved on current platform
    - Trailing slashes removed
    - Relative paths resolved to absolute from current directory
    """

    # Windows drive letter pattern: C:\ or C:/
    WINDOWS_DRIVE_PATTERN = re.compile(r"^([A-Za-z]):[/\\]")

    # UNC path pattern: \\server\share or //server/share
    UNC_PATTERN = re.compile(r"^(?:\\\\|//)([^/\\]+)[/\\](.*)$")

    # WSL /mnt/{drive}/ pattern
    WSL_MNT_PATTERN = re.compile(r"^/mnt/([a-z])/(.*)$", re.IGNORECASE)

    @classmethod
    def detect_path_type(cls, path: str) -> str:
        """
        Detect the type of input path.

        Returns:
            'windows': Windows-style path (C:\\... or C:/...)
            'wsl': WSL /mnt/ path
            'posix': Standard POSIX path (/home/..., /usr/...)
            'unc': UNC network path (\\\\server\\share)
            'unknown': Could not determine
        """
        if not path:
            return "unknown"

        # Check Windows drive letter first
        if cls.WINDOWS_DRIVE_PATTERN.match(path):
            return "windows"

        # Check UNC path
        if cls.UNC_PATTERN.match(path):
            return "unc"

        # Check WSL /mnt/{drive}/ pattern
        if cls.WSL_MNT_PATTERN.match(path):
            return "wsl"

        # Standard POSIX path
        if path.startswith("/"):
            return "posix"

        # Relative path - classify based on separator
        if "\\" in path:
            return "windows"

        return "posix"

    @classmethod
    def normalize(cls, path: str, resolve_symlinks: bool = True) -> PathNormalizationResult:
        """
        Normalize a path to canonical POSIX form.

        Args:
            path: Input path in any format (Windows, WSL, POSIX).
            resolve_symlinks: Whether to resolve symlinks (requires filesystem access).

        Returns:
            PathNormalizationResult with canonical path and metadata.

        Examples:
            >>> PathNormalizer.normalize("C:\\Users\\dev\\project")
            PathNormalizationResult(canonical_path="/mnt/c/Users/dev/project", ...)

            >>> PathNormalizer.normalize("/mnt/c/Users/dev/project")
            PathNormalizationResult(canonical_path="/mnt/c/Users/dev/project", ...)
        """
        if not path:
            return PathNormalizationResult(
                canonical_path="",
                original_path="",
                detected_type="unknown",
                was_normalized=False,
                warnings=["Empty path provided"],
            )

        original = path
        warnings = []
        detected_type = cls.detect_path_type(path)

        # Convert based on detected type
        if detected_type == "windows":
            canonical = cls._normalize_windows_path(path)
        elif detected_type == "unc":
            canonical, unc_warnings = cls._normalize_unc_path(path)
            warnings.extend(unc_warnings)
        elif detected_type == "wsl":
            canonical = cls._normalize_wsl_path(path)
        else:
            canonical = cls._normalize_posix_path(path)

        # Resolve symlinks if requested and on compatible platform
        if resolve_symlinks:
            try:
                resolved = cls._try_resolve_path(canonical)
                if resolved != canonical:
                    canonical = resolved
            except (OSError, RuntimeError) as e:
                warnings.append(f"Could not resolve symlinks: {e}")

        # Final cleanup
        canonical = canonical.rstrip("/")
        if not canonical:
            canonical = "/"

        was_normalized = canonical != original

        return PathNormalizationResult(
            canonical_path=canonical,
            original_path=original,
            detected_type=detected_type,
            was_normalized=was_normalized,
            warnings=warnings,
        )

    @classmethod
    def _normalize_windows_path(cls, path: str) -> str:
        """Convert Windows path to WSL /mnt/ format."""
        match = cls.WINDOWS_DRIVE_PATTERN.match(path)
        if match:
            drive_letter = match.group(1).lower()
            remainder = path[3:]  # Skip "C:\" or "C:/"
            remainder = remainder.replace("\\", "/")
            return f"/mnt/{drive_letter}/{remainder}"

        # No drive letter, just convert slashes
        return path.replace("\\", "/")

    @classmethod
    def _normalize_unc_path(cls, path: str) -> Tuple[str, list]:
        """
        Convert UNC path to best-effort POSIX equivalent.

        Note: UNC paths don't have a perfect POSIX mapping.
        We use /mnt/{server}/{share}/... as convention.
        """
        warnings = ["UNC paths converted to /mnt/{server}/{share}/... (best effort)"]
        match = cls.UNC_PATTERN.match(path)
        if match:
            server = match.group(1)
            remainder = match.group(2).replace("\\", "/")
            return f"/mnt/{server}/{remainder}", warnings

        return path.replace("\\", "/"), warnings

    @classmethod
    def _normalize_wsl_path(cls, path: str) -> str:
        """Normalize WSL /mnt/ path (ensure lowercase drive letter, forward slashes)."""
        match = cls.WSL_MNT_PATTERN.match(path)
        if match:
            drive_letter = match.group(1).lower()
            remainder = match.group(2)
            return f"/mnt/{drive_letter}/{remainder}"
        return path

    @classmethod
    def _normalize_posix_path(cls, path: str) -> str:
        """Normalize standard POSIX path."""
        # Collapse multiple slashes
        while "//" in path:
            path = path.replace("//", "/")
        return path

    @classmethod
    def _try_resolve_path(cls, path: str) -> str:
        """
        Attempt to resolve a path using the current filesystem.

        For WSL paths when running on native Linux, only resolves if path exists.
        For Windows paths when running on Windows, uses Windows resolution.
        """
        # Only attempt resolution if path likely exists on this system
        # /mnt/ paths only resolve on actual WSL
        if path.startswith("/mnt/") and os.name != "posix":
            return path

        try:
            p = Path(path)
            if p.exists():
                resolved = str(p.resolve())
                # Convert back to POSIX style if needed
                return resolved.replace("\\", "/")
        except (OSError, RuntimeError):
            pass

        return path

    @classmethod
    def to_windows_path(cls, canonical_path: str) -> Optional[str]:
        """
        Convert canonical POSIX path back to Windows format.

        Only works for /mnt/{drive}/... paths.

        Returns:
            Windows path string, or None if not convertible.
        """
        match = cls.WSL_MNT_PATTERN.match(canonical_path)
        if match:
            drive_letter = match.group(1).upper()
            remainder = match.group(2).replace("/", "\\")
            return f"{drive_letter}:\\{remainder}"
        return None

    @classmethod
    def paths_equivalent(cls, path1: str, path2: str) -> bool:
        """
        Check if two paths refer to the same location (case-insensitive for Windows).

        Both paths are normalized before comparison.
        """
        result1 = cls.normalize(path1, resolve_symlinks=False)
        result2 = cls.normalize(path2, resolve_symlinks=False)

        # Case-insensitive comparison for Windows/WSL paths
        canonical1 = result1.canonical_path.lower()
        canonical2 = result2.canonical_path.lower()

        return canonical1.rstrip("/") == canonical2.rstrip("/")
