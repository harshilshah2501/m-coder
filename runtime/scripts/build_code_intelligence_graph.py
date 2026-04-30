#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

from runtime.layer5.authority.registry_loader import load_registry
from runtime.layer5.graph.eventbus_topology_map import build_eventbus_topology_map
from runtime.layer5.graph import (
    GraphBuilder,
    validate_graph_integrity,
    write_graph_artifacts,
)
from runtime.scripts.build_authority_code_index import build_index_with_progress
from runtime.scripts.build_authority_code_index import _discover_java_files
from runtime.scripts.build_authority_code_index import _meta_path_for_index
from runtime.scripts.build_authority_code_index import _write_meta
from runtime.scripts.build_authority_code_index import refresh_index_incremental


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


def _default_index_cache_path(workspace_root: Path) -> Path:
    key = hashlib.sha256(str(workspace_root).lower().encode("utf-8")).hexdigest()[:12]
    return (_project_root() / "runtime/.cache" / f"authority_code_index.{key}.json").resolve()


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
    ap.add_argument(
        "--refresh-mode",
        choices=("auto", "full", "incremental"),
        default="auto",
        help="Index refresh mode: auto (default), full, incremental",
    )
    ap.add_argument(
        "--index-cache-out",
        default="",
        help="Optional authority index cache JSON path (default runtime/.cache/authority_code_index.<workspace-hash>.json)",
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
    index_cache_path = (
        Path(args.index_cache_out).expanduser().resolve()
        if str(args.index_cache_out or "").strip()
        else _default_index_cache_path(workspace_root)
    )
    index_cache_path.parent.mkdir(parents=True, exist_ok=True)
    mode = str(args.refresh_mode or "auto")
    if mode == "auto":
        mode = "incremental" if index_cache_path.exists() else "full"
        print(f"[cig] refresh_mode auto -> {mode}")
    if mode == "incremental":
        index = refresh_index_incremental(
            workspace_root=workspace_root,
            source_dirs=source_dirs,
            include_tests=bool(args.include_tests),
            max_files=max(1, int(args.max_files)),
            progress_every=max(0, int(args.progress_every)),
            out_path=index_cache_path,
        )
    else:
        index = build_index_with_progress(
            workspace_root=workspace_root,
            source_dirs=source_dirs,
            include_tests=bool(args.include_tests),
            max_files=max(1, int(args.max_files)),
            progress_every=max(0, int(args.progress_every)),
        )
        _, _, sigs = _discover_java_files(
            workspace_root=workspace_root,
            source_dirs=source_dirs,
            include_tests=bool(args.include_tests),
            max_files=max(1, int(args.max_files)),
        )
        _write_meta(
            _meta_path_for_index(index_cache_path),
            workspace_root=workspace_root,
            source_dirs=source_dirs,
            include_tests=bool(args.include_tests),
            max_files=max(1, int(args.max_files)),
            signatures=sigs,
        )
    # Persist refreshed index so subsequent runs can be incremental.
    index.save(index_cache_path)
    print(f"[cig] index_cache={index_cache_path}")
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
    eventbus_map = build_eventbus_topology_map(
        workspace_root=workspace_root,
        relative_files=index.files.keys(),
        repo_identity={"commit_sha": _git_commit_sha(workspace_root)},
    )
    eventbus_path = out_dir / "eventbus_topology_mapping.v1.json"
    eventbus_path.write_text(
        json.dumps(eventbus_map, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"graph_jsonl: {paths['jsonl']}")
    print(f"graph_manifest: {paths['manifest']}")
    print(f"graph_adjacency: {paths['adjacency']}")
    print(f"eventbus_topology_map: {eventbus_path}")
    print(f"graph_stats: {graph.stats}")
    print(f"[cig] total_elapsed_s={time.perf_counter() - t0:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

