"""
Stage-08 path resolution utilities.

Uses sentinel-based detection to find ml/training root: walk up until we find
a directory containing both 'compiler' and 'datasets' subdirs.
"""
from __future__ import annotations

from pathlib import Path

_STAGE08_DIR = Path(__file__).resolve().parent
_SENTINELS = ("compiler", "datasets", "pipeline")


def get_training_root() -> Path:
    """
    Resolve ml/training root by walking up until sentinels are found.

    Expects a directory with subdirs: compiler, datasets, pipeline.
    """
    current = _STAGE08_DIR
    for _ in range(10):  # guard against infinite loop
        if current is None or not current.exists():
            break
        if all((current / s).is_dir() for s in _SENTINELS):
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    # Fallback: assume stage08 -> pipeline -> training
    return _STAGE08_DIR.parent.parent


def get_canonical_sft_dataset_dir() -> Path:
    """Canonical frozen SFT dataset directory: ml/training/datasets/sft/."""
    return get_training_root() / "datasets" / "sft"
