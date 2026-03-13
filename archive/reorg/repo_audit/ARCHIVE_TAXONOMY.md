# Archive by Topic Taxonomy

Each topic defines purpose, criteria, example files, and risk level. No files are moved in this audit.

## governance_history/

Purpose: Preserve historical versions of governance docs and guides.

Criteria: Older versions of canonical docs (e.g., guide v1.5, v1.6 when v1.7 is current); superseded GREG drafts.

Examples: Golden_Exemplars_Guide_v1.5.md, legacy GOLDEN_EXEMPLARS_GUIDE in archives.

Risk level: high — touches doctrine; always needs_decision before archival.

## old_variants/

Purpose: Older exemplar variants no longer in active ML corpus.

Criteria: Variants superseded by newer geometry; kept for history only.

Examples: Old MOTADATA base/variant mappings replaced by later work.

Risk level: medium

## deprecated_mutation/

Purpose: Deprecated mutation harness specs and experiments.

Criteria: Phase-6 / Stage-6 specs with a newer replacement.

Examples: Early PHASE6B mutation reports superseded by PHASE6C or updated specs.

Risk level: medium-high

## legacy_training/

Purpose: Old training configs and experiments.

Criteria: Outdated SFT configs, notebooks, scripts not part of current discipline.

Examples: Old adapter configs, superseded training runs.

Risk level: medium

## draft_docs/

Purpose: Drafts and scratch notes.

Criteria: Names containing draft, notes, tmp, WIP.

Examples: *_draft.md, *_notes.txt.

Risk level: low (unless overlapping doctrine)

## experiments/

Purpose: Exploratory notebooks and one-off investigations.

Criteria: Jupyter notebooks or scripts that are exploratory, not production.

Examples: Local Phase-6C smoke test experiments.

Risk level: low-medium

## misc_orphans/

Purpose: Orphans that do not fit other topics.

Criteria: Unreferenced files not obviously harmful but cluttering structure.

Examples: Old scratch logs, single-use scripts, chat-*.txt session logs.

Risk level: low-medium; needs_decision if touching phase/dataset semantics
