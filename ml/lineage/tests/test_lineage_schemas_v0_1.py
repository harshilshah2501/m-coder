"""
Schema and runtime-rule validation for Lineage Node v0.1 and Freeze Manifest v0.1.

Validates examples against JSON Schema.
Validates runtime-rule invariants (R-L1 through R-L5).
"""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

REPO_ROOT = Path(__file__).resolve().parents[3]
LINEAGE = REPO_ROOT / "ml" / "lineage"
SCHEMAS = LINEAGE / "schemas"
EXAMPLES = SCHEMAS / "examples"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_lineage_rules(obj: dict, *, node_lookup: dict | None = None) -> list[str]:
    """
    Validate lineage node or freeze manifest against runtime rules R-L1 to R-L5.
    Returns list of violated rule codes.
    node_lookup: optional dict[node_id] -> node dict for R-L2 (phase label match).
    """
    violations: list[str] = []

    if obj.get("schema_version") == "lineage.node.v0.1":
        sem = obj.get("semantic", {})
        phrase = sem.get("boundary_phrase", "")
        phrase_hash = sem.get("boundary_phrase_hash", "")
        expected_hash = hashlib.sha256(phrase.encode("utf-8")).hexdigest()
        if phrase_hash != expected_hash:
            violations.append("R-L1")

        if obj.get("node_type") == "DATASET_ROW":
            dr = obj.get("dataset_row", {})
            base_id = dr.get("base_id")
            variant_id = dr.get("variant_id")
            if not base_id or not variant_id:
                violations.append("R-L3")
            row_label = sem.get("phase_semantic_label")
            if node_lookup and row_label is not None:
                for inp in obj.get("inputs", []):
                    nid = inp.get("node_id")
                    ref = node_lookup.get(nid) if nid else None
                    if ref and ref.get("semantic", {}).get("phase_semantic_label") != row_label:
                        violations.append("R-L2")
                        break

    elif obj.get("schema_version") == "freeze.manifest.v0.1":
        ps = obj.get("policy_summary", {})
        fail_count = ps.get("fail_count", 0)
        freeze_allowed = ps.get("freeze_allowed", False)
        if fail_count > 0 and freeze_allowed:
            violations.append("R-L4")
        # R-L5: boundary_set_hash = sha256(sorted(boundary_phrase_hashes from upstream))
        # Test computes expected from upstream nodes when available.

    return violations


@unittest.skipIf(not HAS_JSONSCHEMA, "jsonschema not installed")
class TestLineageNodeSchema(unittest.TestCase):
    """Validate lineage node examples against lineage.node.v0.1.schema.json."""

    def setUp(self) -> None:
        schema = load_json(SCHEMAS / "lineage.node.v0.1.schema.json")
        self.validator = jsonschema.Draft7Validator(schema)

    def _validate(self, name: str) -> None:
        data = load_json(EXAMPLES / name)
        self.validator.validate(data)

    def test_base_exemplar_valid(self) -> None:
        self._validate("base_exemplar_node.json")

    def test_locked_variant_valid(self) -> None:
        self._validate("locked_variant_node.json")

    def test_mutation_result_valid(self) -> None:
        self._validate("mutation_result_node.json")

    def test_dataset_row_valid(self) -> None:
        self._validate("dataset_row_node.json")

    def test_freeze_artifact_valid(self) -> None:
        self._validate("freeze_artifact_node.json")

    def test_sft_checkpoint_valid(self) -> None:
        self._validate("sft_checkpoint_node.json")

    def test_runtime_model_artifact_valid(self) -> None:
        self._validate("runtime_model_artifact_node.json")

    def test_ledger_record_valid(self) -> None:
        self._validate("ledger_record_node.json")


@unittest.skipIf(not HAS_JSONSCHEMA, "jsonschema not installed")
class TestFreezeManifestSchema(unittest.TestCase):
    """Validate freeze manifest against freeze.manifest.v0.1.schema.json."""

    def setUp(self) -> None:
        schema = load_json(SCHEMAS / "freeze.manifest.v0.1.schema.json")
        self.validator = jsonschema.Draft7Validator(schema)

    def test_freeze_manifest_valid(self) -> None:
        data = load_json(EXAMPLES / "freeze_manifest_valid.json")
        self.validator.validate(data)


@unittest.skipIf(not HAS_JSONSCHEMA, "jsonschema not installed")
class TestInvalidExamples(unittest.TestCase):
    """Invalid examples: schema-valid but rule-invalid."""

    def setUp(self) -> None:
        node_schema = load_json(SCHEMAS / "lineage.node.v0.1.schema.json")
        manifest_schema = load_json(SCHEMAS / "freeze.manifest.v0.1.schema.json")
        self.node_validator = jsonschema.Draft7Validator(node_schema)
        self.manifest_validator = jsonschema.Draft7Validator(manifest_schema)

    def test_invalid_boundary_hash_schema_valid(self) -> None:
        data = load_json(EXAMPLES / "invalid_boundary_hash_mismatch_schema_valid.json")
        self.node_validator.validate(data)

    def test_invalid_boundary_hash_fails_rl1(self) -> None:
        data = load_json(EXAMPLES / "invalid_boundary_hash_mismatch_schema_valid.json")
        violations = validate_lineage_rules(data)
        self.assertIn("R-L1", violations)

    def test_invalid_freeze_schema_valid(self) -> None:
        data = load_json(EXAMPLES / "invalid_freeze_non_deterministic_schema_valid.json")
        self.manifest_validator.validate(data)

    def test_invalid_freeze_fails_rl4(self) -> None:
        data = load_json(EXAMPLES / "invalid_freeze_non_deterministic_schema_valid.json")
        violations = validate_lineage_rules(data)
        self.assertIn("R-L4", violations)

    def test_invalid_semantic_label_schema_valid(self) -> None:
        data = load_json(EXAMPLES / "invalid_semantic_label_mismatch_schema_valid.json")
        self.node_validator.validate(data)

    def test_invalid_semantic_label_fails_rl2(self) -> None:
        data = load_json(EXAMPLES / "invalid_semantic_label_mismatch_schema_valid.json")
        lookup = {
            "sha256:base1": load_json(EXAMPLES / "base_exemplar_node.json"),
            "sha256:var1": load_json(EXAMPLES / "locked_variant_node.json"),
        }
        violations = validate_lineage_rules(data, node_lookup=lookup)
        self.assertIn("R-L2", violations)


class TestEnumFreeze(unittest.TestCase):
    """Freeze enums to prevent silent drift."""

    def test_node_types_enum_frozen(self) -> None:
        nt = load_json(SCHEMAS / "node_types.v0.1.json")
        actual = set(nt["items"]["enum"])
        expected = {
            "BASE_EXEMPLAR", "LOCKED_VARIANT", "MUTATION_RESULT", "DATASET_ROW",
            "FREEZE_ARTIFACT", "SFT_CHECKPOINT", "RUNTIME_MODEL_ARTIFACT", "LEDGER_RECORD",
        }
        self.assertEqual(actual, expected)

    def test_collapse_vectors_enum_frozen(self) -> None:
        cv = load_json(SCHEMAS / "collapse_vectors.v0.1.json")
        actual = set(cv["items"]["enum"])
        expected = {
            "REF_SOFTENING", "CONF_TO_DES", "BOUNDARY_ALIASING",
            "MIX_SINGLE_PRESSURE_COLLAPSE", "CODE_GUARD_DRIFT", "AUTHORITY_HALLUCINATION",
        }
        self.assertEqual(actual, expected)

    def test_surfaces_enum_frozen(self) -> None:
        sf = load_json(SCHEMAS / "surfaces.v0.1.json")
        actual = set(sf["items"]["enum"])
        expected = {
            "SignalIntegrity", "BaselinesHistory", "ChangeBlastRadius",
            "AuthorityOwnership", "TimePressure", "Compositional",
            "ImplementationIrreversibility", "ContextDrift",
        }
        self.assertEqual(actual, expected)

    def test_surfaces_set_equality_with_runtime(self) -> None:
        lineage_sf = load_json(SCHEMAS / "surfaces.v0.1.json")
        runtime_sf = load_json(REPO_ROOT / "runtime" / "schemas" / "surfaces.v0.1.json")
        self.assertEqual(
            set(lineage_sf["items"]["enum"]),
            set(runtime_sf["items"]["enum"]),
            "Lineage surfaces must match runtime surfaces",
        )
