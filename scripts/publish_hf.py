#!/usr/bin/env python3
"""
Publish a model export (adapter-only or merged) to a private Hugging Face repo.

Uses HF_TOKEN env var; does not hardcode tokens.
Writes/updates a metadata JSON in the repo with run_id, freeze_id, git_commit, sha256.

Usage:
  export HF_TOKEN=hf_...
  python scripts/publish_hf.py \\
    --local-dir ml/artifacts/exports/adapter_phase08D \\
    --repo-id org/m-coder-adapter \\
    --private \\
    --run-id phase08D --freeze-id golden_v1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _repo_root() -> Path:
    root = Path(__file__).resolve().parents[1]
    return root


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_repo_root(),
            capture_output=True,
            text=True,
            check=False,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def _sha256_dir(dir_path: Path) -> str:
    """Simple aggregate digest over sorted file paths and their sizes (not full content)."""
    h = hashlib.sha256()
    for p in sorted(dir_path.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(dir_path)).encode())
            h.update(str(p.stat().st_size).encode())
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Upload model export to Hugging Face (adapter or merged); optional metadata."
    )
    parser.add_argument(
        "--local-dir",
        type=Path,
        required=True,
        help="Local directory to upload (e.g. ml/artifacts/exports/<model_id>)",
    )
    parser.add_argument(
        "--repo-id",
        required=True,
        help="HF repo id, e.g. org/m-coder-adapter",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Create/use repo as private",
    )
    parser.add_argument("--run-id", default="", help="Training run_id for metadata")
    parser.add_argument("--freeze-id", default="", help="Dataset freeze_id for metadata")
    parser.add_argument("--model-id", default="", help="Model id for metadata (default: dir name)")
    parser.add_argument(
        "--sha256",
        default="",
        help="Override sha256 in metadata (default: derived from dir)",
    )
    args = parser.parse_args()

    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        print("HF_TOKEN is not set. Set it to a Hugging Face write token.", file=sys.stderr)
        return 1

    local_dir = args.local_dir if args.local_dir.is_absolute() else _repo_root() / args.local_dir
    if not local_dir.is_dir():
        print(f"Not a directory: {local_dir}", file=sys.stderr)
        return 1

    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("Install huggingface_hub: pip install huggingface_hub", file=sys.stderr)
        return 1

    api = HfApi(token=token)

    # Ensure repo exists (create if needed, private if requested)
    try:
        api.create_repo(repo_id=args.repo_id, private=args.private, exist_ok=True, repo_type="model")
    except Exception as e:
        print(f"Create/repo check failed: {e}", file=sys.stderr)
        return 1

    # Upload folder
    print(f"Uploading {local_dir} -> {args.repo_id} ...")
    api.upload_folder(
        folder_path=str(local_dir),
        repo_id=args.repo_id,
        repo_type="model",
        token=token,
    )

    # Metadata to write into the repo
    model_id = args.model_id or local_dir.name
    sha = args.sha256 or _sha256_dir(local_dir)
    meta = {
        "model_id": model_id,
        "run_id": args.run_id,
        "freeze_id": args.freeze_id,
        "git_commit": _git_commit(),
        "sha256": sha,
    }

    # Upload metadata JSON (path_in_repo)
    meta_json = json.dumps(meta, indent=2)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        tf.write(meta_json)
        tf.flush()
    try:
        api.upload_file(
            path_or_fileobj=tf.name,
            path_in_repo="model_release_metadata.json",
            repo_id=args.repo_id,
            repo_type="model",
            token=token,
        )
    finally:
        os.unlink(tf.name)

    print("Done. Metadata written to model_release_metadata.json in repo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
