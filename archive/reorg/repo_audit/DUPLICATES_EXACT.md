# Exact Duplicate Detection (Hash-Based)

Content hashes were **not computed** in this read-only audit. This document defines the methodology and lists candidate groups for future verification.

---

## Method (for implementation)

1. Compute SHA256 (or equivalent) over file content for all `.md`, `.rst`, `.txt`, `.json`, `.jsonl`.
2. Exclude `.git/`, `.venv/`, and binary blobs from semantic duplicate analysis.
3. Group files by identical hash.
4. For each group with >1 member, designate a canonical path and list others as duplicates.

---

## Candidate Duplicate Groups (path/naming heuristic)

### smoke_traces.jsonl

- `ml/training/.../phase6c/out/smoke_traces.jsonl`
- `ml/training/.../phase6c/out_m3/smoke_traces.jsonl`
- `ml/training/.../phase6c/out_m4/smoke_traces.jsonl`

Likely distinct (different run outputs); hash will confirm.

### EXEMPLAR_AUTHORING_GUIDE

- `archive/okr/supporting-docs/EXEMPLAR_AUTHORING_GUIDE.md`
- `ml/training/sft/exemplars/guides/archives/engineering-first-regrounding/EXEMPLAR_AUTHORING_GUIDE.md`

Different archive contexts; may differ in content.

---

## Output Schema (when implemented)

For each hash group:

- hash: SHA256 hex
- paths: list of paths
- canonical_path: recommended keeper
- other_copies: list of non-canonical paths
- in_non_canonical_dir: e.g., backup/, old/, copy/
