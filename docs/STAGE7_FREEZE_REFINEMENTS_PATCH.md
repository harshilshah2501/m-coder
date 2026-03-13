# PATCH: Stage-7 Freeze Refinements

This document specifies refinements to the Stage-7 deterministic freeze design (plan `stage-7_deterministic_freeze_design_b4e65d3a`). Apply these changes before implementation.

---

## 1. Plan Patch (Diff-Style)

```diff
--- a/plan
+++ b/plan

 ## 1. Architectural Placement

 ### Exact Module Location

  m-coder/ml/training/
  ├── compiler/
  │   ├── compile_stage7.py          # Existing: doctrine → JSONL
  │   ├── manifest_schema.json       # Extend for freeze manifest
  │   └── freeze_manifest_schema.json # Stage-7 freeze manifest schema
  ├── pipeline/
  │   └── stage6/                    # Stage-6 root (stage6a, stage6b, stage6c, mutation)
  │       ├── pyproject.toml         # Entry points for stage6c-* CLIs
  │       ├── stage6a/               # Schemas, docs, PHASE6_DATASET_FREEZE_CHECKLIST
  │       ├── stage6b/               # Spec placeholders
  │       ├── stage6c/               # Canonical implementation
  │       │   ├── orchestrator/cli.py
  │       │   ├── reporting/cli.py   # stage6c-report
  │       │   ├── reporting/gates.py # evaluate_gates() — consumed by freeze
  │       │   └── freeze/            # stage6c-freeze entrypoint
  └── lineage/schemas/
      └── freeze.manifest.v0.1.schema.json

 ### Canonical Root Unification

-- Stage-6 content consolidated under pipeline/stage6/. No forwarding package.
+- Stage-7 user-facing entrypoint lives under stage6.stage6c.freeze.
+- freeze.py imports compiler.compile_stage7 (compile_doctrine) and stage6.stage6c.reporting.gates.
+- No parallel truth root under compiler; compiler provides primitives only.

 ## 4. Failure Conditions (Fail-Closed Rules)
@@ Stage-6C PASS absent          | stage6c_pass_reference.pass != true

+| Freeze gate: full PASS         | tier2.pass AND tier3.pass AND tier2_non_dummy.pass AND tier3_non_dummy.pass | Exit 1; freeze_block_reason
+| Freeze gate: non-dummy runs    | non_dummy_canonical_runs_count == 0                                      | Exit 1; "non-dummy gates not evaluable"
+| Freeze gate: S3 / critical     | S3_count > 0 in non-dummy canonical evaluation                            | Exit 1; freeze_block_reason
+| Freeze gate: critical collapses| T-BYPASS or T-ALIAS or T-DOMINANCE-FLIP present in canonical non-dummy    | Exit 1; freeze_block_reason

 ## 3. Freeze Manifest Schema
@@ "stage6c_pass_reference": {
@@   }
   }
 }
+
+    "stage6c_suite_configuration_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
+    "freeze_block_reason": { "type": "array", "items": { "type": "string" } },  // empty if freeze allowed
+    "split_hashes": {
+      "type": "object",
+      "required": ["train_hash", "val_hash"],
+      "properties": {
+        "train_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
+        "val_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
+        "test_hash": { "type": ["string","null"] }
+      }
+    },
@@ "collapse_rate_snapshot": {
@@       "tmcr_ge_s2": { "type": "number" },
+      // All floats serialized with 6 decimal places (e.g. round(v, 6))
@@     }
   }
 }
```

---

## 2. File Layout Changes

### Create

| Path | Purpose |
|------|---------|
| `ml/training/pipeline/stage6/stage6c/freeze/__init__.py` | Package init; exports `run_freeze`, `evaluate_freeze_gates` |
| `ml/training/pipeline/stage6/stage6c/freeze/freeze.py` | Freeze orchestration; calls `compiler.compile_stage7.compile_doctrine`, `reporting.gates.evaluate_gates`, `stage08.enforce_split_stage08D.balanced_base_split_phase08D` |
| `ml/training/pipeline/stage6/stage6c/freeze/cli.py` | `stage6c-freeze` CLI; imports from `freeze.freeze` |
| `ml/training/compiler/freeze_manifest_schema.json` | Stage-7 freeze manifest JSON schema (with refinements) |

### Modify

| Path | Change |
|------|--------|
| `ml/training/pipeline/stage6/pyproject.toml` | Entry point `stage6c-freeze = "stage6.stage6c.freeze.cli:main"` |
| `ml/training/pipeline/stage08/enforce_split_stage08D.py` | Sort `base_ids` before split iteration; add assertion that train/val lists are in canonical sorted order; return split_hashes (train_hash, val_hash) |
| `ml/training/pipeline/stage6/stage6c/reporting/load.py` | (Optional) Expose helper for ledger SHA256 if needed |

### Do NOT create

- `ml/training/compiler/freeze_stage7.py` — freeze orchestration lives under stage6.stage6c.freeze, not compiler

---

## 3. APIs & Manifest Schema

### freeze entrypoint function signature

```python
def run_freeze(
    doctrine_path: Path,
    out_dir: Path,
    ledger_path: Path,
    config_path: Path | None = None,
    *,
    split_seed: int = 42,
    force: bool = False,
    dry_run: bool = False,
) -> RunFreezeResult:
    """
    Orchestrate Stage-7 freeze. Fails closed on any invariant violation.
    Returns RunFreezeResult with success, manifest, freeze_block_reasons.
    """
```

```python
@dataclass
class RunFreezeResult:
    success: bool
    manifest: dict | None
    freeze_block_reasons: list[str]
    corpus_hash: str | None
    jsonl_path: Path | None
    manifest_path: Path | None
```

### Gate evaluation function calls

```python
from ..reporting.gates import evaluate_gates

gate_results = evaluate_gates(ledger_rows)
tier2 = gate_results["tier2"]
tier3 = gate_results["tier3"]
tier2_nd = gate_results.get("tier2_non_dummy")
tier3_nd = gate_results.get("tier3_non_dummy")
meta = gate_results["meta"]
```

Freeze passes only if:
- `meta["has_model_labels"]` is True
- `meta["non_dummy_canonical_runs_count"] > 0`
- `tier2_nd is not None` and `tier3_nd is not None`
- `tier2_nd["pass"]` and `tier3_nd["pass"]` are True
- `tier2["pass"]` and `tier3["pass"]` are True
- `tier2_nd["metrics"]["S3_count"] == 0`
- No canonical non-dummy row has `collapse_class` in `{"T-BYPASS","T-ALIAS","T-DOMINANCE-FLIP"}`

### Manifest schema (fields + types)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| schema_version | string (const) | Yes | "stage7-freeze-manifest.v1" |
| source_git_sha | string | Yes | minLength 7 |
| corpus_hash | string | Yes | ^[a-f0-9]{64}$ |
| bases_count | integer | Yes | ≥ 1 |
| variants_count | integer | Yes | ≥ 1 |
| total_rows | integer | Yes | ≥ 1 |
| phase_distribution | object | Yes | REF,CONF,DES,MIX,CODE counts |
| stage6c_suite_configuration_hash | string | Yes | SHA256 of harness config (sorted keys JSON) |
| collapse_rate_snapshot | object | Yes | tier2_pass, tier3_pass, tmcr_ge_s2, s3_count, bda_norm_p95 (6-decimal floats) |
| mutation_taxonomy_version | string | Yes | e.g. "STAGE6C_MUTATION_TAXONOMY_v1" |
| adapter_param_signature_snapshot | string \| null | No | SHA of adapter params from ledger |
| generated_at_utc | string | Yes | ISO8601 ending Z |
| stage6c_pass_reference | object | Yes | pass, ledger_path, ledger_sha256 |
| freeze_block_reason | array of string | Yes | Empty if freeze allowed |
| split_hashes | object | Yes | train_hash, val_hash (test_hash optional) |

### Float stability

All floats in `collapse_rate_snapshot` and BDA summaries: `round(v, 6)` before JSON serialization.

---

## 4. Test Additions

| Test | Description | Pass criteria |
|------|-------------|---------------|
| test_freeze_blocks_without_non_dummy | Ledger with only dummy model_id or no model_id | Freeze aborts; freeze_block_reason includes "non_dummy_canonical_runs_count==0" or "non-dummy gates not evaluable" |
| test_freeze_requires_tier2_and_tier3 | Ledger with tier2 pass but tier3 fail | Freeze aborts; freeze_block_reason includes tier3 failed gate(s) |
| test_freeze_requires_non_dummy_tier2_tier3 | Ledger with tier2/tier3 pass on all, but tier2_nd/tier3_nd fail | Freeze aborts; freeze_block_reason includes non-dummy gate failures |
| test_manifest_hash_stability | Two freeze runs with same inputs | stage6c_suite_configuration_hash identical; corpus_hash identical |
| test_split_determinism | Two runs, same seed | split_hashes.train_hash and split_hashes.val_hash identical |
| test_split_canonical_order | Inspect train_records, val_records | Both sorted by (phase, base_id, variant_id) or equivalent canonical order |
| test_float_serialization | collapse_rate_snapshot with 0.123456789 | JSON shows 0.123457 (6 decimals) |

---

## 5. CLI Output Contract

### stage6c-freeze arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| --doctrine | No | STAGE4 path | Path to STAGE4_VARIANT_GENERATION.md |
| --out-dir | Yes | — | Output directory for JSONL + manifest |
| --ledger | Yes | — | Path to stage6c_ledger.jsonl |
| --config | No | None | Path to harness config (for stage6c_suite_configuration_hash) |
| --split-seed | No | 42 | Seed for deterministic split |
| --force | No | false | Overwrite existing outputs |
| --dry-run | No | false | Validate only, no write |

### Success output (stdout, deterministic order)

```
Compiling doctrine from <path>
Stage-6C full PASS verified (tier2, tier3, non-dummy)
Corpus: <N> rows, <M> bases, corpus_hash=<hash>
Split: train=<train_count>, val=<val_count>, train_hash=<hash>, val_hash=<hash>
Wrote <jsonl_path>
Wrote <manifest_path>
FREEZE COMPLETE
```

### Failure output (stderr, deterministic order)

```
FATAL: Freeze blocked. Reasons:
  1. <reason1>
  2. <reason2>
  ...
```

`freeze_block_reason` list is sorted before printing. Each reason is a short, machine-parseable string (e.g. "tier3.fail_rate_ge_S2<=0.02", "non_dummy_canonical_runs_count==0", "S3_count>0", "collapse_class:T-BYPASS present").

### Exit codes

- 0: Freeze complete
- 1: Freeze blocked or invariant violation
