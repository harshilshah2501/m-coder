# Stage-08D Audit Readiness Report v1

## 1. Governance Snapshot

- Doctrine SHA256: d1fa78dcc955839c5a403da87adeee7e5bb4916dc936dbced72114165bd11da1
- Compiler Version: stage7-compiler-v1.0
- Invariant Normalization: Complete
- Parsing Contract Version: v1.0

## 2. Dataset Provenance

- Frozen Dataset Path: ml/training/datasets/sft/golden_exemplars_v1_frozen.jsonl
- Dataset SHA256: 193d111bb8b08217de26a4ce81a4dee9dadb3d7e37c4bdb8463195f4386b48ce
- Total Rows: 100
- Total Bases: 25
- Phase Distribution:
  - CONF: 40
  - DES: 16
  - MIX: 16
  - CODE: 16
  - REF: 12

## 3. Split Enforcement

- Deterministic Base-Level Split
- Validation Minimums Satisfied:
  - ≥1 REF
  - ≥2 CONF
  - ≥1 DES
  - ≥1 MIX
  - ≥1 CODE
- Base-Level Isolation Confirmed
- Split Manifest Path:
  training/logs/stage08D_split_manifest.json

## 4. Training Loader Hardening

- Strict Schema Detection (STAGE7 / LEGACY)
- Mixed-Schema Abort
- Invalid Phase Abort
- No Silent Row Dropping
- Deterministic Response Rendering
- Audit File:
  training/logs/stage08D_training_input_audit.json

## 5. Configuration Verification

- LoRA Config: Verified
- Base Model Path: Verified
- Logging Paths: Verified
- Random Seed: Confirmed
- No Legacy Dataset References

## 6. GPU-Dependent Tasks Pending

- GPU Smoke Test
- Full Stage-08D Training Run
- Post-Training Structural Invariance Validation

---

Audit Status: READY FOR GPU EXECUTION  
Date: 2026-02-27T00:00:00Z
