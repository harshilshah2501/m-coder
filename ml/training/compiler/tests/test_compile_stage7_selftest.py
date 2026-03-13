"""Selftest for Stage-7 compiler."""
import json
import sys
import unittest
from pathlib import Path

COMPILER_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(COMPILER_DIR))

from compile_stage7 import run_selftest

SCHEMA_PATH = COMPILER_DIR / "dataset_schema.json"
MANIFEST_SCHEMA_PATH = COMPILER_DIR / "manifest_schema.json"


def test_selftest_passes() -> None:
    """Selftest runs in-process and succeeds."""
    schema = json.loads(SCHEMA_PATH.read_text())
    manifest_schema = json.loads(MANIFEST_SCHEMA_PATH.read_text())
    result = run_selftest("stage7-compiler-v1.0", schema, manifest_schema)
    assert result is True


class TestSelftest(unittest.TestCase):
    def test_selftest_passes(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text())
        manifest_schema = json.loads(MANIFEST_SCHEMA_PATH.read_text())
        result = run_selftest("stage7-compiler-v1.0", schema, manifest_schema)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
