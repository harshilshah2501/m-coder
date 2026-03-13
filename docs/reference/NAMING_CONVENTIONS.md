# Repository Naming Conventions

Canonical reference for naming in the m-coder repository. **Historical files may retain legacy names; all new files and directories must follow these conventions.**

---

## 1. Top-level directory naming

- **Lowercase with hyphen allowed only where established:** `governance`, `ml`, `runtime`, `observation`, `docs`, `scripts`, `tests`, `archive`, `jetbrains-plugin`.
- **Layer directories:** Use lowercase, single word or hyphenated where already canonical: `governance` (L1), `ml` (L2), `runtime` (L3), `observation` (L4).
- **No uppercase** in new top-level directory names. Existing mixed-case under `docs/` (e.g. `COMPILATION`, `CONTRACTS`, `OBSERVATION`) are legacy; do not add new uppercase top-level or docs subdirs.

---

## 2. Python package / module naming

- **Snake_case** for package and module names: `plan_gate_service`, `sandbox_executor`, `context_engine`, `shadow_runner`.
- **Directory name = import name:** e.g. `runtime/plan_gate_service/` → `runtime.plan_gate_service`.
- **File names:** `snake_case.py` for modules; preserve existing names (e.g. `plangate_service.py` under package `plangate`) when adding to existing packages.

---

## 3. Docs directory naming

- **Prefer lowercase** for new subdirectories under `docs/`: e.g. `docs/runtime`, `docs/governance`, `docs/reference`.
- **Legacy:** Some docs subdirs use UPPERCASE (`docs/COMPILATION`, `docs/CONTRACTS`, `docs/OBSERVATION`). Do not rename them for convention alone; add no new UPPERCASE docs subdirs.

---

## 4. Milestone doc naming pattern

- **Pattern:** `M<m>.<n>_<SHORT_NAME>.md` under `docs/runtime/milestones/`.
- **Examples:** `M3.1_AGENT_LOOP_ORCHESTRATOR.md`, `M3.10_SANDBOX_DRIVER_ABSTRACTION.md`, `M3.11_CONTAINER_SANDBOX_RUNTIME.md`.
- Use canonical milestone ID (e.g. M3.0–M3.18); no alternate naming (M3.E0, M3X.*) in new doc filenames.

---

## 5. Branch execution note naming pattern

- **Pattern:** `<branch_slug>.md` under `docs/runtime/branch_execution_notes/`, with hyphens: `feature-m3.1-orchestrator.md`, `feature-m3.5-ledger.md`, `m3.10-sandbox-driver.md`.
- Branch slug typically mirrors the branch name with slashes replaced by hyphens; lowercase acceptable for minor variants.

---

## 6. Terminology conventions

- **Prose and docs:** Use **Plan-Gate** (with hyphen) when referring to the governance gate in narrative, specs, and comments.
- **Package and directory names** (existing; do not rename for convention):
  - **`plangate`** — Core Plan-Gate package under `runtime/plangate/` (e.g. `plangate_service`, `plangate_decision`, authority_validator, judge_gate).
  - **`plan_gate_service`** — Service/HTTP layer under `runtime/plan_gate_service/`.
  - **`plan_gate_stub`** — Stub/emulator under `runtime/plan_gate_stub/`.
- New code or docs: use **Plan-Gate** in prose; use existing package/dir names when importing or referencing paths. Do not introduce new spelling variants.

---

## 7. Legacy and new-file rule

- **Historical files and directories** may keep existing names. Renaming for consistency alone is out of scope for this document; see AGENT_EXECUTION_RULES and governance for change rules.
- **All new files, directories, and doc titles** must follow the conventions above. When in doubt, match the pattern of the most recent similar artifact (e.g. latest milestone doc, latest branch note).
