# Target Canonical Layout

Proposed top-level structure aligned with the four-layer architecture and existing repo contents.

## Baseline Structure

- governance/
- ml/
- runtime/
- observation/
- docs/
- scripts/
- repo_audit/
- archive/by_topic/ (governance_history, old_variants, deprecated_mutation, legacy_training, draft_docs, experiments, misc_orphans)
- artifacts/
- datasets/

## governance/

Purpose: Layer-1 constitutional doctrine and locked governance corpus.

Belongs: GREG manifest, ratified kernels, golden exemplar governance (Phases 01-05, Phase-06 hardening), governance READMEs.

Does NOT belong: Raw training artifacts, logs, speculative drafts not locked.

## ml/

Purpose: Layer-2 ML Compilation — exemplars, variants, mutation harnesses, dataset freeze.

Belongs: Exemplar/variant mapping, Stage-6 (6A/6B/6C) specs and code, dataset freeze checklists, SFT configs.

Does NOT belong: Governance-locked doctrine; runtime enforcement code.

## runtime/

Purpose: Layer-3 runtime enforcement and integration.

Belongs: Plan/Judge/Authority/Irreversibility gate designs, runtime adapters, RAG and policy specs.

Does NOT belong: Training pipelines, dataset compilation.

## observation/

Purpose: Layer-4 drift, probes, and audit.

Belongs: Post-SFT mutation harness, drift probes, GREG audit evidence.

Does NOT belong: Pre-freeze mutation harness (that lives in ml/).

## docs/

Purpose: Cross-cutting human documentation.

Belongs: READMEs, how-tos, architecture maps, reference guides not canonical doctrine.

Does NOT belong: LOCKED governance docs.

## scripts/

Purpose: Utilities and automation.

Belongs: Shell scripts, CI scripts, data prep, monitoring.

Does NOT belong: Application source code.

## repo_audit/

Purpose: Structural audit outputs.

Belongs: INDEX_TREE, DOC_INDEX, ASSET_INDEX, DUPLICATES_*, ORPHANS, TARGET_LAYOUT, ARCHIVE_TAXONOMY, MOVE_PLAN, RISK_MAP.

## archive/by_topic/

Purpose: Structured parking for historical/deprecated material. See ARCHIVE_TAXONOMY.md.

## artifacts/

Purpose: Non-source data and model artifacts.

Belongs: Checkpoints, frozen outputs, packaged tarballs.

Does NOT belong: Source code, governance docs.

## datasets/

Purpose: Training/eval datasets and splits.

Belongs: Input datasets, derived datasets, manifests.
