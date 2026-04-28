#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from runtime.layer5.authority.code_index_builder import build_index
from runtime.layer5.authority.registry_loader import load_registry
from runtime.layer5.graph import (
    GraphBuilder,
    validate_graph_integrity,
    write_graph_artifacts,
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_output_dir(value: str) -> Path:
    out = Path(value).expanduser()
    if out.is_absolute():
        return out.resolve()
    return (_project_root() / out).resolve()


def _resolve_registry_path(value: str, workspace_root: Path) -> Path:
    raw = Path(value).expanduser()
    if raw.is_absolute():
        return raw.resolve()
    under_workspace = (workspace_root / raw).resolve()
    if under_workspace.exists():
        return under_workspace
    return (_project_root() / raw).resolve()


def _git_commit_sha(workspace_root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(workspace_root),
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except Exception:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Build deterministic Code Intelligence Graph v1")
    ap.add_argument("--workspace-root", required=True, help="Workspace root path")
    ap.add_argument(
        "--registry-path",
        default="runtime/layer5/authority/product_authority_registry.yaml",
        help="Authority registry YAML path",
    )
    ap.add_argument(
        "--out-dir",
        default="runtime/.cache/code_intelligence_graph",
        help="Directory for CIG artifacts",
    )
    ap.add_argument("--include-tests", action="store_true")
    args = ap.parse_args()

    workspace_root = Path(args.workspace_root).expanduser().resolve()
    out_dir = _resolve_output_dir(args.out_dir)
    registry_path = _resolve_registry_path(args.registry_path, workspace_root)

    index = build_index(workspace_root, include_tests=bool(args.include_tests))
    registry = load_registry(registry_path)
    builder = GraphBuilder(workspace_root)
    graph = builder.build(
        index,
        registry=registry,
        repo_identity={"commit_sha": _git_commit_sha(workspace_root)},
        extractor_version="cig_builder.v1",
    )
    result = validate_graph_integrity(graph)
    if not result.passed:
        for e in result.errors:
            print(f"validation_error: {e}")
        return 2
    paths = write_graph_artifacts(graph, out_dir)
    print(f"graph_jsonl: {paths['jsonl']}")
    print(f"graph_manifest: {paths['manifest']}")
    print(f"graph_adjacency: {paths['adjacency']}")
    print(f"graph_stats: {graph.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

