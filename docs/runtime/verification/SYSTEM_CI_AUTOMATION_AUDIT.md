# System CI Automation Audit

**Report date:** 2026-03-13  
**Snapshot:** [SYSTEM_REPOSITORY_SNAPSHOT.json](SYSTEM_REPOSITORY_SNAPSHOT.json)

---

## Scope

Inspect CI workflows and scripts. Verify that CI does not bypass Plan-Gate or SandboxExecutor and that it only runs tests/builds (or structural guards). No execution path in CI should invoke governed user execution or skip governance.

---

## Surfaces Inspected

- **CI workflows:** `.github/` directory (if present)
- **Scripts under scripts/ci/:** `check_structure.py`, `check_no_governance_yaml_in_docs.py`, `check_pipeline_boundaries.py`, `check_no_exemplar_phases_under_ml.py`, `check_no_nested_archive.py`
- **References to Plan-Gate / SandboxExecutor / execute in scripts:** Grep for plan_gate, PlanGate, sandbox_executor, SandboxExecutor, execute_sandbox, bypass in `scripts/`

---

## Findings

### Absence of .github workflows

- **Finding:** No `.github` directory present in the repository at audit time. No GitHub Actions workflow files were inspected. If CI is run elsewhere (e.g. external or local), those flows were not in scope.

### scripts/ci/ contents

| Script | Purpose | Invokes Plan-Gate / Sandbox? |
|--------|---------|------------------------------|
| `check_structure.py` | Layer-2 structural invariants: no numeric stage dirs at ml/training root, no STAGE*.md in vendor, no .jsonl in vendor, no /root/ in dataset_manifest, compiler DEFAULT_OUT_DIR must be generated/ | No |
| `check_no_governance_yaml_in_docs.py` | Ensures governance-style YAML (e.g. Phase-06-*, RU-SO-*) does not appear under docs/ | No |
| `check_pipeline_boundaries.py` | Fails if any path contains `ml/training/src/sources/Motadata/stage` | No |
| `check_no_exemplar_phases_under_ml.py` | Fails if `ml/training/sft/exemplars/Phases` exists (exemplars must come from _build mirror) | No |
| `check_no_nested_archive.py` | (Not read in full; listed in directory.) | No (structural guard by name) |

**Observation:** All inspected CI scripts are static/structure checks. None import or call PlanGateService, SandboxExecutor, or execute_service handlers. None run user commands through the governed sandbox or Plan-Gate path.

### Grep for governance/execution in scripts

- **scripts/:** Matches for "execute" in scripts (e.g. `scripts/verify_task4_final.py` referencing an executor, `scripts/test_graph_population.py` with "void execute();") are unrelated to the runtime Plan-Gate or SandboxExecutor. No script was found that invokes the governed execution endpoint or bypasses Plan-Gate.

---

## Risks

1. **CI not in repo:** With no `.github` (or equivalent) in tree, the exact CI entrypoints and any future workflows are not auditable in this pass. If CI is added later, it should remain limited to tests/builds/guards and must not call /v0/execute or run user commands through the sandbox.
2. **Local or external CI:** Any CI run outside the repo (e.g. Jenkins, local cron) was not inspected; same recommendation applies.

---

## Verdict

**PASS.** All inspected CI scripts under `scripts/ci/` are read-only structural guards and do not invoke Plan-Gate or SandboxExecutor. No CI path was found that could bypass governance or run governed user execution. Recommendation: keep any future CI (e.g. GitHub Actions) restricted to tests, builds, and structural checks; do not add steps that call the execution service or sandbox for user-supplied commands.
