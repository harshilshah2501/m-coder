# System Naming Convention Audit

**Report date:** 2026-03-13  
**Snapshot:** [SYSTEM_REPOSITORY_SNAPSHOT.json](SYSTEM_REPOSITORY_SNAPSHOT.json)

---

## Scope

Audit repository naming discipline across directories, Python modules, milestone documents, and terminology. Record mixed casing, inconsistent module/component names, and terminology drift. Read-only documentation of findings; no fixes.

---

## Surfaces Inspected

- Top-level and docs directories (casing)
- Runtime directory and module names (plan_gate vs plangate)
- Milestone and branch-execution doc names
- Stage/Phase terminology in docs and paths
- Python package and import names under `runtime/` and `ml/`

---

## Findings

### Directory casing

| Location | Pattern | Examples |
|----------|---------|----------|
| **Top-level** | Lowercase | `governance`, `ml`, `runtime`, `observation`, `docs`, `scripts`, `tests`, `archive`, `jetbrains-plugin` |
| **docs/** | Mixed | Lowercase: `docs/governance`, `docs/runtime`, `docs/demo`, `docs/guides`. Uppercase: `docs/COMPILATION`, `docs/CONTRACTS`, `docs/OBSERVATION`. |
| **runtime/** | Lowercase with underscore | `plan_gate_service`, `plan_gate_stub`, `shadow_runner`, `execute_service`, `ask_service`, `ci_gate` |
| **runtime/plangate** | No underscore | Single word `plangate` (vs `plan_gate_service`, `plan_gate_stub`) |

**Finding:** Inconsistent naming between `plan_gate_*` (underscore) and `plangate` (no underscore) for related Plan-Gate components. Docs mix lowercase subdirs (governance, runtime) with uppercase (COMPILATION, CONTRACTS, OBSERVATION).

### Python module and package names

- **Directories as packages:** `runtime/plan_gate_service`, `runtime/plan_gate_stub` → imports as `runtime.plan_gate_service`, `runtime.plan_gate_stub`. `runtime/plangate` → `runtime.plangate`. So we have both `plan_gate_*` and `plangate` in the same runtime layer.
- **Files:** `plangate_service.py`, `plangate_decision.py` live under `runtime/plangate/`; `plan_gate.py` under `runtime/plan_gate_stub/`. Naming is consistent within each package but differs across packages (plan_gate vs plangate).

### Milestone and branch-execution documents

| Type | Pattern | Examples |
|------|---------|----------|
| Milestone docs | `M3.<n>_<NAME>.md` | M3.1_AGENT_LOOP_ORCHESTRATOR.md, M3.3_PLAN_GATE_INTEGRATION.md, M3.10_SANDBOX_DRIVER_ABSTRACTION.md |
| Branch notes | Mixed | `feature-m3.1-orchestrator.md`, `feature-m3.5-ledger.md` (hyphen), `m3.10-sandbox-driver.md`, `m3.11-container-runtime.md` (lowercase m3), `PR_M3_6_SHADOW.md` (underscore, M3_6) |
| Shadow docs | M3_6 | M3_6_SHADOW_VALIDATION_REPORT.md, M3_6_BASELINE_SCENARIOS.md (underscore between M3 and 6) |

**Finding:** Milestone IDs in filenames: sometimes `M3.10` (dot), sometimes `M3_6` (underscore). Branch notes use hyphen and sometimes lowercase `m3`.

### Stage vs phase terminology

- **Pipeline stages:** Dir names `stage6`, `stage08`, `stage6c` (no hyphen); docs and specs use “Stage-6”, “Stage-8”, “Stage-6C” (with hyphen and capital S). Canonical layout doc uses both (e.g. stage6/stage6c vs Stage-6C).
- **Constitutional phases:** “Phase-1” through “Phase-6” in governance/docs; directory `governance/golden-exemplars/Phases`. Consistent “Phase” with hyphen and number.
- **Risk:** Stage (pipeline) vs Phase (constitutional) is documented as distinct in ARCHITECTURE_4_LAYER; naming in dirs (stage6 vs Stage-6) is minor inconsistency (directory lowercase no hyphen, prose with hyphen).

### Terminology drift

- **Plan-Gate vs PlanGate vs plangate:** Docs and code use “Plan-Gate” (with hyphen) in prose; package name `plangate`; dirs `plan_gate_service`, `plan_gate_stub`. Acceptable but mixed (hyphen in prose, no hyphen in identifiers, underscore in two dir names).
- **M3.x:** Tracker and milestone docs use M3.0–M3.18; some shadow docs use M3_6. Already covered in NOMENCLATURE_AUDIT as historical/acceptable where documented.

---

## Risks

1. **plan_gate vs plangate:** New contributors might search for “plan_gate” and miss `runtime/plangate` or vice versa. Documentation and onboarding could clarify the two naming styles (service/stub vs core package).
2. **docs casing:** UPPERCASE vs lowercase in docs/ can cause case-sensitive issues on some systems or in links; currently no duplicate (e.g. no both COMPILATION and compilation).
3. **M3.6 vs M3_6:** Filename and doc title inconsistency; low risk if treated as historical and referenced consistently in tracker.

---

## Verdict

**PASS WITH CAVEAT.** Naming is audited and documented. No single naming failure; findings are inconsistencies: (1) `plan_gate_*` vs `plangate` for Plan-Gate-related code, (2) mixed casing under docs (COMPILATION/CONTRACTS/OBSERVATION vs governance/runtime), (3) milestone filename variants (M3.10 vs M3_6), (4) branch note style (feature-m3.1 vs m3.10). Terminology (Stage vs Phase, Plan-Gate in prose vs plangate/plan_gate in paths) is documented and understood. Recommend documenting the plan_gate vs plangate convention in a single reference; no changes made in this audit.
