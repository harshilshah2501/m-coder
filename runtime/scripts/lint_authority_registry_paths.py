#!/usr/bin/env python3
"""
CLI: verify authority registry file paths exist under a Motadata (or any) workspace root.

Usage:
  python3 runtime/scripts/lint_authority_registry_paths.py \\
    --workspace-root /path/to/Motadata

Optional:
  --registry PATH   (default: runtime/layer5/authority/product_authority_registry.yaml)

Exit code: 0 if all paths exist, 1 if any missing or on usage error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _default_registry_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "layer5"
        / "authority"
        / "product_authority_registry.yaml"
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--workspace-root",
        required=True,
        help="Workspace root containing paths as in the registry (e.g. Motadata repo root)",
    )
    p.add_argument(
        "--registry",
        default=str(_default_registry_path()),
        help="Path to product_authority_registry.yaml",
    )
    args = p.parse_args()
    root = Path(args.workspace_root).expanduser()
    reg_path = Path(args.registry).expanduser()
    if not root.is_dir():
        print(f"ERROR: workspace root is not a directory: {root}", file=sys.stderr)
        return 1
    if not reg_path.is_file():
        print(f"ERROR: registry file not found: {reg_path}", file=sys.stderr)
        return 1

    from runtime.layer5.authority.registry_loader import load_registry
    from runtime.layer5.authority.registry_path_lint import (
        format_issues_report,
        lint_registry_against_workspace,
    )

    registry = load_registry(reg_path)
    issues = lint_registry_against_workspace(registry, root)
    if not issues:
        print(f"OK: all registry file paths exist under {root.resolve()}")
        print(f"    registry: {reg_path.resolve()}")
        print(f"    concepts: {len(registry.concepts)}")
        return 0

    print(
        f"FAIL: {len(issues)} registry path(s) missing or invalid under {root.resolve()}",
        file=sys.stderr,
    )
    print(format_issues_report(issues), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
