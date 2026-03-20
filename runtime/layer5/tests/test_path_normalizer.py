"""
Tests for path normalization.

Validates deterministic path conversion between Windows, WSL, and POSIX formats.
These tests run on any platform (not just WSL).
"""

import pytest
from runtime.layer5.workspace.path_normalizer import PathNormalizer, PathNormalizationResult


class TestPathTypeDetection:
    """Test path type detection."""

    def test_windows_drive_path(self):
        assert PathNormalizer.detect_path_type("C:\\Users\\dev\\project") == "windows"
        assert PathNormalizer.detect_path_type("D:/Projects/myapp") == "windows"
        assert PathNormalizer.detect_path_type("c:\\lower\\case") == "windows"

    def test_wsl_mnt_path(self):
        assert PathNormalizer.detect_path_type("/mnt/c/Users/dev/project") == "wsl"
        assert PathNormalizer.detect_path_type("/mnt/d/Projects/myapp") == "wsl"

    def test_posix_path(self):
        assert PathNormalizer.detect_path_type("/home/user/project") == "posix"
        assert PathNormalizer.detect_path_type("/usr/local/bin") == "posix"
        assert PathNormalizer.detect_path_type("/") == "posix"

    def test_unc_path(self):
        assert PathNormalizer.detect_path_type("\\\\server\\share\\path") == "unc"
        assert PathNormalizer.detect_path_type("//server/share/path") == "unc"

    def test_relative_path_with_backslash(self):
        assert PathNormalizer.detect_path_type("src\\main\\java") == "windows"

    def test_relative_posix_path(self):
        assert PathNormalizer.detect_path_type("src/main/java") == "posix"

    def test_empty_path(self):
        assert PathNormalizer.detect_path_type("") == "unknown"


class TestWindowsPathNormalization:
    """Test Windows -> WSL path normalization."""

    def test_basic_windows_path(self):
        result = PathNormalizer.normalize("C:\\Users\\dev\\project", resolve_symlinks=False)
        assert result.canonical_path == "/mnt/c/Users/dev/project"
        assert result.detected_type == "windows"
        assert result.was_normalized

    def test_windows_path_with_forward_slashes(self):
        result = PathNormalizer.normalize("C:/Users/dev/project", resolve_symlinks=False)
        assert result.canonical_path == "/mnt/c/Users/dev/project"
        assert result.detected_type == "windows"

    def test_lowercase_drive_letter(self):
        result = PathNormalizer.normalize("d:\\Projects\\app", resolve_symlinks=False)
        assert result.canonical_path == "/mnt/d/Projects/app"

    def test_uppercase_drive_letter_normalized_to_lowercase(self):
        result = PathNormalizer.normalize("D:\\Projects\\app", resolve_symlinks=False)
        assert result.canonical_path == "/mnt/d/Projects/app"

    def test_mixed_separators(self):
        result = PathNormalizer.normalize("C:\\Users/dev\\project/src", resolve_symlinks=False)
        assert result.canonical_path == "/mnt/c/Users/dev/project/src"

    def test_trailing_slash_removed(self):
        result = PathNormalizer.normalize("C:\\Users\\dev\\project\\", resolve_symlinks=False)
        assert result.canonical_path == "/mnt/c/Users/dev/project"
        assert not result.canonical_path.endswith("/")


class TestWSLPathNormalization:
    """Test WSL path normalization (already canonical, minor cleanup only)."""

    def test_wsl_path_unchanged(self):
        result = PathNormalizer.normalize("/mnt/c/Users/dev/project", resolve_symlinks=False)
        assert result.canonical_path == "/mnt/c/Users/dev/project"
        assert result.detected_type == "wsl"

    def test_wsl_drive_letter_lowercase(self):
        result = PathNormalizer.normalize("/mnt/C/Users/dev/project", resolve_symlinks=False)
        assert result.canonical_path == "/mnt/c/Users/dev/project"

    def test_wsl_trailing_slash_removed(self):
        result = PathNormalizer.normalize("/mnt/c/Users/dev/project/", resolve_symlinks=False)
        assert result.canonical_path == "/mnt/c/Users/dev/project"


class TestPOSIXPathNormalization:
    """Test POSIX path normalization."""

    def test_posix_path_unchanged(self):
        result = PathNormalizer.normalize("/home/user/project", resolve_symlinks=False)
        assert result.canonical_path == "/home/user/project"
        assert result.detected_type == "posix"

    def test_double_slashes_collapsed(self):
        result = PathNormalizer.normalize("/home//user///project", resolve_symlinks=False)
        assert result.canonical_path == "/home/user/project"

    def test_root_path(self):
        result = PathNormalizer.normalize("/", resolve_symlinks=False)
        assert result.canonical_path == "/"


class TestUNCPathNormalization:
    """Test UNC path normalization."""

    def test_unc_backslash(self):
        result = PathNormalizer.normalize("\\\\server\\share\\path\\file", resolve_symlinks=False)
        assert result.canonical_path == "/mnt/server/share/path/file"
        assert result.detected_type == "unc"
        assert len(result.warnings) > 0  # Should warn about best-effort conversion

    def test_unc_forward_slash(self):
        result = PathNormalizer.normalize("//server/share/path", resolve_symlinks=False)
        assert result.canonical_path == "/mnt/server/share/path"


class TestPathEquivalence:
    """Test path equivalence checking."""

    def test_windows_and_wsl_equivalent(self):
        assert PathNormalizer.paths_equivalent(
            "C:\\Users\\dev\\project",
            "/mnt/c/Users/dev/project"
        )

    def test_case_insensitive_equivalence(self):
        assert PathNormalizer.paths_equivalent(
            "C:\\Users\\Dev\\Project",
            "/mnt/c/users/dev/project"
        )

    def test_trailing_slash_equivalence(self):
        assert PathNormalizer.paths_equivalent(
            "/mnt/c/project/",
            "/mnt/c/project"
        )

    def test_different_paths_not_equivalent(self):
        assert not PathNormalizer.paths_equivalent(
            "C:\\Users\\dev\\project1",
            "C:\\Users\\dev\\project2"
        )


class TestToWindowsPath:
    """Test conversion back to Windows format."""

    def test_wsl_to_windows(self):
        result = PathNormalizer.to_windows_path("/mnt/c/Users/dev/project")
        assert result == "C:\\Users\\dev\\project"

    def test_wsl_to_windows_different_drive(self):
        result = PathNormalizer.to_windows_path("/mnt/d/Projects/app")
        assert result == "D:\\Projects\\app"

    def test_non_mnt_path_returns_none(self):
        result = PathNormalizer.to_windows_path("/home/user/project")
        assert result is None


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_path(self):
        result = PathNormalizer.normalize("", resolve_symlinks=False)
        assert result.canonical_path == ""
        assert len(result.warnings) > 0

    def test_whitespace_preserved(self):
        result = PathNormalizer.normalize("C:\\Users\\My Documents\\project", resolve_symlinks=False)
        assert result.canonical_path == "/mnt/c/Users/My Documents/project"

    def test_special_characters(self):
        result = PathNormalizer.normalize("C:\\Users\\dev\\project-v1.0", resolve_symlinks=False)
        assert result.canonical_path == "/mnt/c/Users/dev/project-v1.0"


class TestDeterminism:
    """Test that normalization is deterministic."""

    def test_same_input_same_output(self):
        inputs = [
            "C:\\Users\\dev\\project",
            "/mnt/c/Users/dev/project",
            "C:/Users/dev/project",
            "/home/user/project",
        ]

        for inp in inputs:
            result1 = PathNormalizer.normalize(inp, resolve_symlinks=False)
            result2 = PathNormalizer.normalize(inp, resolve_symlinks=False)
            assert result1.canonical_path == result2.canonical_path
            assert result1.detected_type == result2.detected_type

    def test_windows_variants_converge(self):
        """Different Windows representations of same path converge to same canonical form."""
        variants = [
            "C:\\Users\\dev\\project",
            "C:/Users/dev/project",
            "c:\\Users\\dev\\project",
            "c:/Users/dev/project",
        ]

        canonical_paths = set()
        for v in variants:
            result = PathNormalizer.normalize(v, resolve_symlinks=False)
            canonical_paths.add(result.canonical_path)

        # All variants should produce same canonical path
        assert len(canonical_paths) == 1
        assert canonical_paths.pop() == "/mnt/c/Users/dev/project"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
