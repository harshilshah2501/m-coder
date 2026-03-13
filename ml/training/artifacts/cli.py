from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import sys

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from store import resolve_artifact_root, sha256_file


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _manifest_dir() -> Path:
    return _repo_root() / "ml" / "training" / "freeze_manifests" / "stage6c"


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for _ in handle:
            count += 1
    return count


def _load_ledger_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _git_commit() -> str:
    head = (_repo_root() / ".git" / "HEAD")
    if not head.exists():
        return "unknown"
    try:
        import subprocess

        out = subprocess.check_output(
            ["git", "-C", str(_repo_root()), "rev-parse", "--short", "HEAD"],
            text=True,
        )
        return out.strip()
    except Exception:
        return "unknown"


def _build_manifest(
    suite_id: str,
    rows: List[Dict[str, Any]],
    files: List[Dict[str, Any]],
    artifact_root: Path,
    notes: str,
) -> Dict[str, Any]:
    first = rows[0] if rows else {}
    run_count = len(rows)
    return {
        "schema_version": "stage6c-artifact-manifest/v1",
        "suite_id": suite_id,
        "run_count": run_count,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "suite": first.get("suite", "canonical"),
        "config_path": "ml/training/pipeline/stage6/stage6c/config/gating_config.yaml",
        "config_digest": first.get("config_digest"),
        "seeds_digest": first.get("seeds_digest"),
        "model_id": first.get("model_id"),
        "expected_counts": {
            "planned_runs": run_count,
            "executed_runs": run_count,
            "trace_rows": run_count,
            "ledger_rows": run_count,
        },
        "artifact_backend": {
            "kind": "local",
            "root_uri": f"file://{artifact_root}",
            "bucket": None,
            "prefix": None,
        },
        "files": files,
        "freeze_certificate_ref": "ml/training/pipeline/FREEZE_CERTIFICATE_v1.json",
        "notes": notes,
    }


def _write_control_plane_outputs(
    suite_id: str,
    manifest_obj: Dict[str, Any],
) -> tuple[Path, Path, Path]:
    out_dir = _manifest_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / f"{suite_id}.manifest.json"
    pointer_path = out_dir / f"{suite_id}.pointer.json"
    summary_path = out_dir / f"{suite_id}.summary.md"

    manifest_path.write_text(
        json.dumps(manifest_obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    pointer = {
        "suite_id": suite_id,
        "manifest": str(manifest_path.relative_to(_repo_root())),
        "artifact_backend": manifest_obj.get("artifact_backend"),
        "files": [
            {
                "logical_name": item.get("logical_name"),
                "artifact_relpath": item.get("artifact_relpath"),
            }
            for item in manifest_obj.get("files", [])
        ],
    }
    pointer_path.write_text(
        json.dumps(pointer, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    summary = [
        f"# Stage6C Artifact Summary: {suite_id}",
        "",
        f"- run_count: {manifest_obj.get('run_count', 0)}",
        f"- git_commit: {manifest_obj.get('git_commit', 'unknown')}",
        f"- model_id: {manifest_obj.get('model_id', 'unknown')}",
        f"- manifest: {manifest_path.relative_to(_repo_root())}",
        f"- pointer: {pointer_path.relative_to(_repo_root())}",
    ]
    summary_path.write_text("\n".join(summary) + "\n", encoding="utf-8")
    return manifest_path, pointer_path, summary_path


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

    suite_id = run_dir.name
    artifact_root = resolve_artifact_root()
    suite_dest = artifact_root / "stage6c" / "suites" / suite_id
    suite_dest.mkdir(parents=True, exist_ok=True)

    def move_file(src: Path, dst: Path) -> None:
        if not src.exists():
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            dst.unlink()
        shutil.move(str(src), str(dst))

    def move_dir(src: Path, dst: Path) -> None:
        if not src.exists() or not src.is_dir():
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.move(str(src), str(dst))

    ledger_src = run_dir / "stage6c_ledger.jsonl"
    traces_src = run_dir / "suite_traces.jsonl"
    plots_src = run_dir / "plots"
    ledger_dst = suite_dest / "stage6c_ledger.jsonl"
    traces_dst = suite_dest / "suite_traces.jsonl"
    plots_dst = suite_dest / "plots"

    move_file(ledger_src, ledger_dst)
    move_file(traces_src, traces_dst)
    move_dir(plots_src, plots_dst)

    final_dir = run_dir / "final"
    freeze_manifest_src = final_dir / "freeze_manifest.json"
    if not freeze_manifest_src.exists():
        alt = final_dir / "stage7_freeze_manifest.json"
        if alt.exists():
            freeze_manifest_src = alt
    golden_src = final_dir / "golden_exemplars_v1.jsonl"
    freeze_id = f"{suite_id}_freeze"
    freeze_dest = artifact_root / "stage7" / "freeze" / freeze_id
    freeze_dest.mkdir(parents=True, exist_ok=True)
    freeze_manifest_dst = freeze_dest / "freeze_manifest.json"
    golden_dst = freeze_dest / "golden_exemplars_v1.jsonl"

    move_file(freeze_manifest_src, freeze_manifest_dst)
    move_file(golden_src, golden_dst)

    rows = _load_ledger_rows(ledger_dst)
    files: List[Dict[str, Any]] = []
    if ledger_dst.exists():
        files.append(
            {
                "logical_name": "stage6c_ledger",
                "artifact_relpath": f"stage6c/suites/{suite_id}/stage6c_ledger.jsonl",
                "repo_pointer": f"ml/training/freeze_manifests/stage6c/{suite_id}.pointer.json",
                "size_bytes": ledger_dst.stat().st_size,
                "sha256": sha256_file(ledger_dst),
                "media_type": "application/x-ndjson",
            }
        )
    if traces_dst.exists():
        files.append(
            {
                "logical_name": "suite_traces",
                "artifact_relpath": f"stage6c/suites/{suite_id}/suite_traces.jsonl",
                "repo_pointer": f"ml/training/freeze_manifests/stage6c/{suite_id}.pointer.json",
                "size_bytes": traces_dst.stat().st_size,
                "sha256": sha256_file(traces_dst),
                "media_type": "application/x-ndjson",
            }
        )
    if plots_dst.exists():
        files.append(
            {
                "logical_name": "plots_dir",
                "artifact_relpath": f"stage6c/suites/{suite_id}/plots",
                "repo_pointer": f"ml/training/freeze_manifests/stage6c/{suite_id}.pointer.json",
                "size_bytes": sum(p.stat().st_size for p in plots_dst.rglob("*") if p.is_file()),
                "sha256": None,
                "media_type": "inode/directory",
            }
        )
    if golden_dst.exists():
        files.append(
            {
                "logical_name": "stage7_golden_exemplars",
                "artifact_relpath": f"stage7/freeze/{freeze_id}/golden_exemplars_v1.jsonl",
                "repo_pointer": f"ml/training/freeze_manifests/stage6c/{suite_id}.pointer.json",
                "size_bytes": golden_dst.stat().st_size,
                "sha256": sha256_file(golden_dst),
                "media_type": "application/x-ndjson",
            }
        )
    if freeze_manifest_dst.exists():
        files.append(
            {
                "logical_name": "stage7_freeze_manifest",
                "artifact_relpath": f"stage7/freeze/{freeze_id}/freeze_manifest.json",
                "repo_pointer": f"ml/training/freeze_manifests/stage6c/{suite_id}.pointer.json",
                "size_bytes": freeze_manifest_dst.stat().st_size,
                "sha256": sha256_file(freeze_manifest_dst),
                "media_type": "application/json",
            }
        )

    manifest = _build_manifest(
        suite_id=suite_id,
        rows=rows,
        files=files,
        artifact_root=artifact_root,
        notes="Artifacts relocated to store; repo retains manifest, summary, and pointer only.",
    )
    if manifest["expected_counts"]["trace_rows"] == 0 and traces_dst.exists():
        manifest["expected_counts"]["trace_rows"] = _line_count(traces_dst)
    manifest_path, pointer_path, summary_path = _write_control_plane_outputs(suite_id, manifest)

    print(f"suite_id={suite_id}")
    print(f"artifact_suite_dir={suite_dest}")
    print(f"artifact_freeze_dir={freeze_dest}")
    print(f"manifest={manifest_path}")
    print(f"pointer={pointer_path}")
    print(f"summary={summary_path}")
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
        if p.is_dir():
            size = sum(fp.stat().st_size for fp in p.rglob("*") if fp.is_file())
            sha = None
        else:
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
    if argv is None:
        argv = sys.argv[1:]
    if argv and len(argv) > 0 and argv[0] == "artifacts":
        argv = argv[1:]
    parser = _build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
