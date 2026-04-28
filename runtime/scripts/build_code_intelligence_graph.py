#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path

from runtime.layer5.authority.registry_loader import load_registry
from runtime.layer5.graph import (
    GraphBuilder,
    validate_graph_integrity,
    write_graph_artifacts,
)
from runtime.scripts.build_authority_code_index import build_index_with_progress


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
    try:
        if under_workspace.exists():
            return under_workspace
    except PermissionError:
        # Workspace root may be inaccessible on this host/user (for example,
        # probing /root/... from a non-root account). Fall back to project-local
        # registry path instead of crashing.
        pass
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


def _discover_source_dirs(workspace_root: Path) -> list[str]:
    candidates = [
        "src/main/java",
        "src",
        "motadata/src/main/java",
        "app/src/main/java",
        "core/src/main/java",
    ]
    found = [c for c in candidates if (workspace_root / c).exists()]
    return found or ["."]


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
    ap.add_argument(
        "--max-files",
        type=int,
        default=50000,
        help="Hard cap on processed Java files (default 50000)",
    )
    ap.add_argument(
        "--progress-every",
        type=int,
        default=100,
        help="Progress update granularity for index extraction",
    )
    args = ap.parse_args()

    workspace_root = Path(args.workspace_root).expanduser().resolve()
    out_dir = _resolve_output_dir(args.out_dir)
    registry_path = _resolve_registry_path(args.registry_path, workspace_root)

    t0 = time.perf_counter()
    print(f"[cig] workspace_root={workspace_root}")
    print(f"[cig] out_dir={out_dir}")
    print(f"[cig] registry_path={registry_path}")
    source_dirs = _discover_source_dirs(workspace_root)
    print(f"[cig] source_dirs={source_dirs}")
    print("[cig] building code index (live progress below)")
    index = build_index_with_progress(
        workspace_root=workspace_root,
        source_dirs=source_dirs,
        include_tests=bool(args.include_tests),
        max_files=max(1, int(args.max_files)),
        progress_every=max(0, int(args.progress_every)),
    )
    print(f"[cig] code index built in {(time.perf_counter() - t0):.2f}s; stats={index.stats}")

    print("[cig] loading authority registry")
    registry = load_registry(registry_path)
    builder = GraphBuilder(workspace_root)
    print("[cig] assembling deterministic graph")
    graph = builder.build(
        index,
        registry=registry,
        repo_identity={"commit_sha": _git_commit_sha(workspace_root)},
        extractor_version="cig_builder.v1",
    )
    print("[cig] validating graph integrity")
    result = validate_graph_integrity(graph)
    if not result.passed:
        for e in result.errors:
            print(f"validation_error: {e}")
        return 2
    print("[cig] writing graph artifacts")
    paths = write_graph_artifacts(graph, out_dir)
    print(f"graph_jsonl: {paths['jsonl']}")
    print(f"graph_manifest: {paths['manifest']}")
    print(f"graph_adjacency: {paths['adjacency']}")
    print(f"graph_stats: {graph.stats}")
    print(f"[cig] total_elapsed_s={time.perf_counter() - t0:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

