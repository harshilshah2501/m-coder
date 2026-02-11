## Archive Namespace

The `archive/` directory is the **single canonical root** for historical material in this repository.

### Purpose

- Preserve past states, experiments, and reports **without** affecting current behavior.
- Provide traceability for decisions and experiments over time.

### Structure

Recommended subdirectories:

- `archive/docs/` – archived documentation and prior iterations.
- `archive/evaluation/` – archived evaluation results and reports.
- `archive/training/` – archived training artifacts, logs, and reports.
- `archive/okr/` – OKR and progress tracking material.
- `archive/sessions/` – session summaries, progress logs, and one-off notes.

### Invariants

- Archive content is **inert**:
  - Production/runtime code **must not** read from `archive/**`.
  - Training and evaluation pipelines **must not** read from `archive/**`.
- CI:
  - May perform **structure/integrity** checks (e.g., no nested `archive/` under `archive/`).  
  - Should not use `archive/**` as input for tests or linters that reflect current behavior.
- No nested archive directories:
  - Avoid structures like `archive/archive_*/` inside `archive/`.

Archive is **append-only**. Edits and deletions are rare and should be intentional and documented.

