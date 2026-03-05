from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict

import sys

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from store import resolve_artifact_root, sha256_file


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _manifest_dir() -> Path:
    return _repo_root() / "ml" / "training" / "freeze_manifests" / "stage6c"


def cmd_init(_args: argparse.Namespace) -> int:
    root = resolve_artifact_root()
    (root / "stage6c" / "suites").mkdir(parents=True, exist_ok=True)
    (root / "stage7" / "freeze").mkdir(parents=True, exist_ok=True)
    (root / "datasets").mkdir(parents=True, exist_ok=True)
    (root / "models" / "checkpoints").mkdir(parents=True, exist_ok=True)
    print(f"artifact_root={root}")
    return 0


def cmd_import_stage6c_run(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.exists() or not run_dir.is_dir():
        raise SystemExit(f"run dir not found: {run_dir}")

    # Full implementation is added in later phase steps; keep command contract stable now.
    print(f"import-stage6c-run accepted run_dir={run_dir}")
    print("status=TODO_IMPLEMENTATION_PENDING")
    return 0


def cmd_verify_manifest(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest).expanduser().resolve()
    if not manifest_path.exists():
        raise SystemExit(f"manifest not found: {manifest_path}")

    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    backend = (doc.get("artifact_backend") or {}).get("kind", "local")
    if backend != "local":
        raise SystemExit("verify-manifest currently supports local backend only")

    root_uri = (doc.get("artifact_backend") or {}).get("root_uri", "")
    if not root_uri.startswith("file://"):
        raise SystemExit("local backend requires artifact_backend.root_uri starting with file://")
    root = Path(root_uri[len("file://"):])

    failures = []
    for item in doc.get("files", []):
        rel = item.get("artifact_relpath")
        expected_sha = item.get("sha256")
        expected_size = item.get("size_bytes")
        if not rel:
            failures.append("missing artifact_relpath in manifest entry")
            continue
        p = root / rel
        if not p.exists():
            failures.append(f"missing file: {p}")
            continue
        size = p.stat().st_size
        sha = sha256_file(p)
        if expected_size is not None and int(expected_size) != size:
            failures.append(f"size mismatch for {p}: expected={expected_size} got={size}")
        if expected_sha and expected_sha != sha:
            failures.append(f"sha mismatch for {p}: expected={expected_sha} got={sha}")

    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        return 2

    print(f"OK: manifest verified {manifest_path}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="artifacts")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize artifact store directories")
    p_init.set_defaults(func=cmd_init)

    p_import = sub.add_parser("import-stage6c-run", help="Import a Stage-6C suite/run directory")
    p_import.add_argument("--run-dir", required=True, help="Path to Stage-6C output directory")
    p_import.set_defaults(func=cmd_import_stage6c_run)

    p_verify = sub.add_parser("verify-manifest", help="Verify manifest file checksums and sizes")
    p_verify.add_argument("--manifest", required=True, help="Path to manifest json")
    p_verify.set_defaults(func=cmd_verify_manifest)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
