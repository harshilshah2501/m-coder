"""Tests for Stage-08 dataset path discovery."""
import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
TRAINING_ROOT = REPO_ROOT / "ml" / "training"
STAGE08_DIR = TRAINING_ROOT / "pipeline" / "stage08"

# Allow importing stage08 modules
sys.path.insert(0, str(STAGE08_DIR))


def _get_canonical_sft():
    """Use canonical helper; avoid hardcoding datasets/sft in tests."""
    from _path_utils import get_canonical_sft_dataset_dir
    return get_canonical_sft_dataset_dir()


class TestDatasetDiscovery(unittest.TestCase):
    """Assert discover_dataset_dir resolves to canonical ml/training/datasets/sft."""

    def test_get_canonical_sft_dataset_dir_resolves_to_training_datasets_sft(self):
        """get_canonical_sft_dataset_dir() must return ml/training/datasets/sft/."""
        from _path_utils import get_canonical_sft_dataset_dir

        resolved = get_canonical_sft_dataset_dir()
        self.assertTrue(
            resolved.is_dir(),
            f"Expected {resolved} to be a directory",
        )
        self.assertEqual(
            resolved.name, "sft",
            f"Expected leaf 'sft', got {resolved.name}",
        )
        self.assertEqual(
            resolved.parent.name, "datasets",
            f"Expected parent 'datasets', got {resolved.parent.name}",
        )
        # Path should end with .../datasets/sft
        self.assertTrue(
            str(resolved).endswith("datasets" + str(Path("/")) + "sft") or str(resolved).endswith("datasets/sft"),
            f"Expected path ending with datasets/sft, got {resolved}",
        )

    def test_canonical_sft_path_exists_and_has_jsonl(self):
        """Canonical ml/training/datasets/sft/ must exist and contain .jsonl files."""
        resolved = _get_canonical_sft()
        self.assertEqual(resolved.name, "sft", f"Leaf must be sft: {resolved}")
        self.assertEqual(resolved.parent.name, "datasets", f"Parent must be datasets: {resolved}")
        self.assertTrue(resolved.exists(), f"Canonical SFT dir must exist: {resolved}")
        jsonl_files = list(resolved.glob("*.jsonl"))
        self.assertGreater(
            len(jsonl_files), 0,
            f"Canonical SFT dir must contain .jsonl files",
        )

    def test_discover_dataset_dir_cwd_independent(self):
        """Dataset discovery must work regardless of current working directory."""
        from enforce_split_stage08D import discover_dataset_dir

        orig_cwd = os.getcwd()
        try:
            os.chdir("/tmp")
            result = discover_dataset_dir()
            self.assertTrue(
                result.exists(),
                f"discover_dataset_dir must resolve from /tmp cwd; got {result}",
            )
            self.assertIn("sft", str(result), f"Path must contain sft: {result}")
        finally:
            os.chdir(orig_cwd)

    def test_no_hardcoded_datasets_sft_in_entrypoints(self):
        """Regression: entrypoints must not hardcode datasets/sft; use get_canonical_sft_dataset_dir."""
        entrypoints = [
            STAGE08_DIR / "train.py",
            STAGE08_DIR / "train_stage08D.py",
            STAGE08_DIR / "enforce_split_stage08D.py",
        ]
        # Patterns that indicate hardcoded path construction (bug we fixed)
        bad_patterns = [
            'parent / "datasets" / "sft"',
            'parent / "datasets" / \'sft\'',
            'SCRIPT_DIR.parent / "datasets" / "sft"',
            '"/" + "datasets" + "/" + "sft"',
        ]
        for path in entrypoints:
            self.assertTrue(path.exists(), f"Entrypoint not found: {path}")
            text = path.read_text()
            for bad in bad_patterns:
                self.assertNotIn(
                    bad, text,
                    f"Found hardcoded datasets/sft path in {path.name}; use get_canonical_sft_dataset_dir()",
                )


if __name__ == "__main__":
    unittest.main()
