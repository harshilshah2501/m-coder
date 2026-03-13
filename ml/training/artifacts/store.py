from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _config_path() -> Path:
    return _repo_root() / "ml" / "training" / "artifacts" / "artifact_store.yaml"


def _load_config() -> Dict[str, Any]:
    path = _config_path()
    if not path.exists():
        return {
            "backend": "local",
            "local": {"root": "/home/harshil/Harshil-PoCs/m-coder_artifacts"},
            "s3": {
                "enabled": False,
                "bucket": "",
                "prefix": "",
                "endpoint": "",
                "region": "",
                "access_key_env": "ARTIFACTS_S3_ACCESS_KEY_ID",
                "secret_key_env": "ARTIFACTS_S3_SECRET_ACCESS_KEY",
                "session_token_env": "ARTIFACTS_S3_SESSION_TOKEN",
            },
        }

    raw = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            raise ValueError("artifact_store.yaml must parse into a mapping")
        return data
    except Exception:
        # Fallback for environments without PyYAML: accept JSON content.
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("artifact_store config must parse into a mapping")
        return data


def resolve_artifact_root() -> Path:
    override = os.environ.get("M_CODER_ARTIFACT_ROOT", "").strip()
    if override:
        root = Path(override).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        return root

    cfg = _load_config()
    backend = str(cfg.get("backend", "local")).lower()
    if backend != "local":
        raise RuntimeError(
            f"Configured backend '{backend}' is not supported by local resolver. "
            "Use local backend for file operations."
        )

    local = cfg.get("local") or {}
    root_raw = str(local.get("root", "/home/harshil/Harshil-PoCs/m-coder_artifacts"))
    root = Path(root_raw).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def sha256_file(path: str | Path) -> str:
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"Cannot hash missing file: {p}")

    digest = hashlib.sha256()
    with p.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(manifest_path: str | Path, manifest_obj: Dict[str, Any]) -> Path:
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(manifest_obj, indent=2, sort_keys=True, ensure_ascii=False)
    path.write_text(payload + "\n", encoding="utf-8")
    return path


def put_dir(src_dir: str | Path, dest_relpath: str) -> Path:
    src = Path(src_dir).resolve()
    if not src.exists() or not src.is_dir():
        raise FileNotFoundError(f"Source directory does not exist: {src}")

    root = resolve_artifact_root()
    dest = root / dest_relpath
    dest.parent.mkdir(parents=True, exist_ok=True)

    mode = os.environ.get("ARTIFACT_PUT_MODE", "move").strip().lower()
    if dest.exists():
        if dest.is_dir():
            shutil.rmtree(dest)
        else:
            dest.unlink()

    if mode == "copy":
        shutil.copytree(src, dest)
    else:
        shutil.move(str(src), str(dest))
    return dest
