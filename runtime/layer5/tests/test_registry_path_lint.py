"""Tests for registry_path_lint."""

from __future__ import annotations

import textwrap
from pathlib import Path

from runtime.layer5.authority.registry_loader import load_registry
from runtime.layer5.authority.registry_path_lint import (
    collect_registry_file_refs,
    lint_registry_against_workspace,
)


def _write_registry(tmp: Path, yaml_body: str) -> Path:
    p = tmp / "reg.yaml"
    p.write_text(yaml_body, encoding="utf-8")
    return p


def test_lint_passes_when_all_paths_exist(tmp_path: Path):
    reg = _write_registry(
        tmp_path,
        textwrap.dedent(
            """
            schema_version: "product_authority_registry.v1.1"
            last_updated: "2026-01-01"
            maintainer: "test"
            concepts:
              demo:
                primary_owner:
                  file: "src/Ok.java"
                  class: "Ok"
                verification:
                  last_verified_at: "2026-01-01T00:00:00Z"
                  verification_source: "human"
                  staleness_threshold_days: 90
                collaborators:
                  - file: "src/Helper.java"
                    role: "x"
                    relationship: "y"
                forbidden_distractors: []
                entry_points:
                  - type: "h"
                    file: "src/Entry.java"
                    method: "m"
            """
        ),
    )
    (tmp_path / "src").mkdir()
    for name in ("Ok.java", "Helper.java", "Entry.java"):
        (tmp_path / "src" / name).write_text("class X {}\n", encoding="utf-8")

    registry = load_registry(reg)
    issues = lint_registry_against_workspace(registry, tmp_path)
    assert issues == []
    refs = collect_registry_file_refs(registry)
    assert len(refs) == 3


def test_lint_fails_when_primary_missing(tmp_path: Path):
    reg = _write_registry(
        tmp_path,
        textwrap.dedent(
            """
            schema_version: "product_authority_registry.v1.1"
            last_updated: "2026-01-01"
            maintainer: "test"
            concepts:
              demo:
                primary_owner:
                  file: "src/Missing.java"
                  class: "Missing"
                verification:
                  last_verified_at: "2026-01-01T00:00:00Z"
                  verification_source: "human"
                  staleness_threshold_days: 90
            """
        ),
    )
    registry = load_registry(reg)
    issues = lint_registry_against_workspace(registry, tmp_path)
    assert len(issues) == 1
    assert issues[0].role == "primary_owner"
    assert issues[0].detail == "missing"
