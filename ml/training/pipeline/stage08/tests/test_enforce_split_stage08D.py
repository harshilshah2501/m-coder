"""Unit tests for Stage-08D split enforcement."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TRAINING_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(TRAINING_DIR))

from enforce_split_stage08D import (
    BALANCED_VAL_SPEC,
    _base_id_and_phase,
    balanced_base_split_phase08D,
    load_jsonl_records,
)


class TestEnforceSplitStage08D(unittest.TestCase):
    def test_invalid_phase_fails(self):
        """Invalid phase should cause load_jsonl_records to exit with code 1."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"input": "x", "output": "y", "phase": "INVALID", "base_id": "B1"}) + "\n")
            bad_path = Path(f.name)
        try:
            with self.assertRaises(SystemExit) as ctx:
                load_jsonl_records(bad_path.parent, dataset_file=bad_path.name)
            self.assertEqual(ctx.exception.code, 1)
        finally:
            bad_path.unlink(missing_ok=True)

    def test_missing_base_id_fails(self):
        """Missing base_id/sample_id should cause load_jsonl_records to exit with code 1."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"input": "x", "output": "y", "phase": "REF"}) + "\n")
            bad_path = Path(f.name)
        try:
            with self.assertRaises(SystemExit) as ctx:
                load_jsonl_records(bad_path.parent, dataset_file=bad_path.name)
            self.assertEqual(ctx.exception.code, 1)
        finally:
            bad_path.unlink(missing_ok=True)

    def test_val_base_minimums_enforce_2_conf_bases(self):
        """Validation must have at least 2 CONF bases (per BALANCED_VAL_SPEC)."""
        synth = []
        for bid, phase in [
            ("B1", "REF"), ("B7", "REF"),
            ("B2", "CONF"), ("B3", "CONF"), ("B8", "CONF"),
            ("B4", "DES"), ("B9", "DES"),
            ("B5", "MIX"), ("B10", "MIX"),
            ("B6", "CODE"), ("B11", "CODE"),
        ]:
            synth.append({"input": "x", "output": "y", "phase": phase, "base_id": bid})
        train_r, val_r, _, _, _ = balanced_base_split_phase08D(synth)
        val_conf_bases = {
            r.get("base_id") or r.get("sample_id")
            for r in val_r
            if str(r.get("phase", "")).strip().upper() == "CONF"
        }
        self.assertGreaterEqual(
            len(val_conf_bases), BALANCED_VAL_SPEC["CONF"],
            f"Expected >= 2 CONF bases in val, got {len(val_conf_bases)}"
        )

    def test_base_id_and_phase_raises_on_empty_base_id(self):
        """_base_id_and_phase must raise if base_id is empty."""
        with self.assertRaises(ValueError) as ctx:
            _base_id_and_phase({"input": "x", "output": "y", "phase": "REF"})
        self.assertIn("missing base_id", str(ctx.exception))

    def test_base_id_and_phase_raises_on_invalid_phase(self):
        """_base_id_and_phase must raise if phase is invalid (no coercion to MIX)."""
        with self.assertRaises(ValueError) as ctx:
            _base_id_and_phase({"input": "x", "output": "y", "phase": "INVALID", "base_id": "B1"})
        self.assertIn("Invalid phase", str(ctx.exception))

    def test_selftest_mode_exits_zero(self):
        """--selftest should exit 0 when all checks pass."""
        result = subprocess.run(
            [sys.executable, str(TRAINING_DIR / "enforce_split_stage08D.py"), "--selftest"],
            cwd=TRAINING_DIR,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, f"selftest failed: {result.stderr}")


if __name__ == "__main__":
    unittest.main()
