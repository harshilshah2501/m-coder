# System Governance Audit

**Report date:** 2026-03-13  
**Canonical state reference:** [SYSTEM_CANONICAL_STATE_AUDIT.md](SYSTEM_CANONICAL_STATE_AUDIT.md)  
**Snapshot:** [SYSTEM_REPOSITORY_SNAPSHOT.json](SYSTEM_REPOSITORY_SNAPSHOT.json)

---

## 1. Scope

Audit governance directories, constitutional documents, AGENT_EXECUTION_RULES.md, phase doctrine references, and protected surfaces per AGENT_EXECUTION_RULES §3.

---

## 2. Governance Surfaces Inspected

- Root: `AGENT_EXECUTION_RULES.md`
- Governance dirs: `governance/`, `docs/governance/`
- Protected paths from rules: `governance/**`, `ml/**`, `docs/CONSTITUTION*`, `docs/governance/**`, `runtime/schemas/**`, `runtime/ide/schemas/**`
- Constitutional manifest and phase doctrine refs: `docs/LAYER1_GOVERNANCE_SPEC.md`, `docs/NON_NEGOTIABLE_INVARIANTS.md`

---

## 3. Files and Directories Found

| Path | Present | Notes |
|------|---------|------|
| `AGENT_EXECUTION_RULES.md` | Yes | Root copy |
| `docs/governance/AGENT_EXECUTION_RULES.md` | Yes | Docs copy |
| `docs/governance/README.md` | Yes | |
| `governance/` | Yes | Top-level Layer-1 dir |
| `governance/README.md` | Yes | |
| `governance/CONSTITUTIONAL_MANIFEST_v1.0.md` | Yes | |
| `governance/REPOSITORY_CONSTITUTION.md` | Yes | |
| `governance/golden-exemplars/` | Yes | |
| `governance/review-packages/` | Yes | |
| `docs/LAYER1_GOVERNANCE_SPEC.md` | Yes | |
| `docs/NON_NEGOTIABLE_INVARIANTS.md` | Yes | |
| `runtime/schemas/` | Yes | Contains ledger_row, plan, reason_codes, surfaces (v0.1) |
| `runtime/ide/schemas/` | Yes | Contains action_types, ask_request, authority_verdicts, boundary_hashing, decision_*, execute_*, ide_event, plan_*, examples |

No `docs/GOVERNANCE` (uppercase) — only `docs/governance` (lowercase). No `docs/CONSTITUTION*` files; constitutional content lives under `governance/` and docs reference it.

---

## 4. Consistency Findings

- Protected surfaces listed in AGENT_EXECUTION_RULES §3 all exist: governance/**, docs/governance/**, runtime/schemas/**, runtime/ide/schemas/**. (ml/** not enumerated in this audit; covered in repository structure and ML pipeline audits.)
- Phase doctrine (REF, CONF, dominance, fail-closed) is referenced in docs/governance and in docs/LAYER1_GOVERNANCE_SPEC.md.
- Root and docs/governance copies of AGENT_EXECUTION_RULES.md both present; content alignment not diffed (audit is structural).

---

## 5. Risks

- **Dual copy of AGENT_EXECUTION_RULES:** Root and `docs/governance/` both hold a copy; drift between them would be a consistency risk. Not verified in this run.
- **docs/CONSTITUTION*:** Rules protect this pattern; no files match under docs. Constitutional content is in `governance/`; no finding.

---

## 6. Pass/Fail Verdict

**PASS.** Governance directories exist, AGENT_EXECUTION_RULES is present at root and under docs/governance, constitutional and phase-doctrine references exist (LAYER1_GOVERNANCE_SPEC, NON_NEGOTIABLE_INVARIANTS), and protected schema directories (runtime/schemas, runtime/ide/schemas) are present and non-empty.
