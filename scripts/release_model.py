#!/usr/bin/env python3
"""
Layer-2 release verification script.

Usage (from repo root):
  python3 scripts/release_model.py

This will:
  - Verify the Patch-2 dataset, freeze certificate, checkpoint, and release metadata
  - Write ml/artifacts/LAYER2_RELEASE_VERIFICATION.json
  - Exit 0 on PASS, non-zero on FAIL
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


REPO_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = REPO_ROOT / "ml" / "training" / "pipeline" / "stage08" / "dataset" / "golden_exemplars_v1_conf_patch2.jsonl"
FREEZE_CERT_PATH = REPO_ROOT / "ml" / "training" / "pipeline" / "stage08" / "FREEZE_CERTIFICATE_STAGE8_CONF_PATCH2.json"
CHECKPOINT_DIR = REPO_ROOT / "ml" / "artifacts" / "checkpoints" / "phase08D_conf_patch2" / "checkpoint-58"
RELEASE_META_PATH = REPO_ROOT / "ml" / "artifacts" / "MODEL_RELEASE_PATCH2.json"
REPORT_PATH = REPO_ROOT / "ml" / "artifacts" / "LAYER2_RELEASE_VERIFICATION.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    errors: List[str] = []

    # Base report structure
    report: Dict[str, Any] = {
        "layer": "Layer-2",
        "status": "FAIL",
        "dataset_path": str(DATASET_PATH),
        "dataset_sha256": "",
        "freeze_certificate_valid": False,
        "checkpoint_path": str(CHECKPOINT_DIR),
        "checkpoint_valid": False,
        "release_metadata_valid": False,
        "conf_drift_result": {
            "S0": 80,
            "conf_to_des": 0,
            "s2_s3": 0,
        },
        "errors": errors,
    }

    # 1) Verify dataset file exists
    if not DATASET_PATH.is_file():
        errors.append(f"Dataset file missing: {DATASET_PATH}")
        dataset_sha = ""
    else:
        # 2) Compute SHA256 of dataset file
        dataset_sha = sha256_file(DATASET_PATH)
        report["dataset_sha256"] = dataset_sha

    # 3) Verify freeze certificate matches path + SHA
    if not FREEZE_CERT_PATH.is_file():
        errors.append(f"Freeze certificate missing: {FREEZE_CERT_PATH}")
    else:
        try:
            cert = load_json(FREEZE_CERT_PATH)
            frozen_path = cert.get("frozen_dataset_path")
            frozen_sha = cert.get("dataset_sha256")
            if frozen_path != f"ml/training/pipeline/stage08/dataset/{DATASET_PATH.name}":
                errors.append(
                    f"Freeze certificate dataset path mismatch: "
                    f"expected ml/training/pipeline/stage08/dataset/{DATASET_PATH.name}, got {frozen_path!r}"
                )
            if dataset_sha and frozen_sha != dataset_sha:
                errors.append(
                    f"Freeze certificate dataset_sha256 mismatch: expected {dataset_sha}, got {frozen_sha}"
                )
            if not errors:
                report["freeze_certificate_valid"] = True
        except Exception as e:
            errors.append(f"Failed to load/validate freeze certificate: {e}")

    # 4) Verify checkpoint directory exists
    if not CHECKPOINT_DIR.is_dir():
        errors.append(f"Checkpoint directory missing: {CHECKPOINT_DIR}")
    else:
        # 5) Verify required checkpoint files
        adapter_weights = CHECKPOINT_DIR / "adapter_model.safetensors"
        adapter_config = CHECKPOINT_DIR / "adapter_config.json"
        missing_any = False
        if not adapter_weights.is_file():
            errors.append(f"Checkpoint weights missing: {adapter_weights}")
            missing_any = True
        if not adapter_config.is_file():
            errors.append(f"Checkpoint config missing: {adapter_config}")
            missing_any = True
        if not missing_any:
            report["checkpoint_valid"] = True

    # 6) Verify release metadata matches dataset + checkpoint + conf drift result
    if not RELEASE_META_PATH.is_file():
        errors.append(f"Release metadata missing: {RELEASE_META_PATH}")
    else:
        try:
            meta = load_json(RELEASE_META_PATH)
            expected_dataset_rel = f"ml/training/pipeline/stage08/dataset/{DATASET_PATH.name}"
            if meta.get("training_dataset") != expected_dataset_rel:
                errors.append(
                    f"MODEL_RELEASE_PATCH2.training_dataset mismatch: "
                    f"expected {expected_dataset_rel}, got {meta.get('training_dataset')!r}"
                )
            if dataset_sha and meta.get("dataset_sha256") != dataset_sha:
                errors.append(
                    f"MODEL_RELEASE_PATCH2.dataset_sha256 mismatch: expected {dataset_sha}, "
                    f"got {meta.get('dataset_sha256')}"
                )
            expected_ckpt_rel = f"ml/artifacts/checkpoints/phase08D_conf_patch2/checkpoint-58"
            if meta.get("checkpoint") != expected_ckpt_rel:
                errors.append(
                    f"MODEL_RELEASE_PATCH2.checkpoint mismatch: "
                    f"expected {expected_ckpt_rel}, got {meta.get('checkpoint')!r}"
                )

            drift = meta.get("conf_drift_result") or {}
            severity = drift.get("severity") or {}
            if severity.get("S0") != 80:
                errors.append(
                    f"conf_drift_result.severity.S0 mismatch: expected 80, got {severity.get('S0')}"
                )
            if drift.get("conf_to_des") != 0:
                errors.append(
                    f"conf_drift_result.conf_to_des mismatch: expected 0, got {drift.get('conf_to_des')}"
                )
            if drift.get("s2_s3") != 0:
                errors.append(
                    f"conf_drift_result.s2_s3 mismatch: expected 0, got {drift.get('s2_s3')}"
                )

            if not any(
                msg.startswith("MODEL_RELEASE_PATCH2") or msg.startswith("conf_drift_result")
                for msg in errors
            ):
                report["release_metadata_valid"] = True
        except Exception as e:
            errors.append(f"Failed to load/validate MODEL_RELEASE_PATCH2.json: {e}")

    # 7) Final status and report write
    status = "PASS" if not errors else "FAIL"
    report["status"] = status

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Emit a short console summary for humans
    print(f"[LAYER2_RELEASE] status={status}")
    if errors:
        for msg in errors:
            print(f"[LAYER2_RELEASE][ERROR] {msg}")

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

