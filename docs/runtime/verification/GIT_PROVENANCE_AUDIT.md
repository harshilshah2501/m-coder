# Git Provenance Audit

**Report date:** 2026-03-13  
**Canonical state reference:** [SYSTEM_CANONICAL_STATE_AUDIT.md](SYSTEM_CANONICAL_STATE_AUDIT.md)  
**Snapshot:** [SYSTEM_REPOSITORY_SNAPSHOT.json](SYSTEM_REPOSITORY_SNAPSHOT.json)

---

## 1. Scope

Audit release tags, milestone branches, merge commits, and completion reports vs git truth. Verify tag targets, merge ancestry, roadmap claims vs git history, and actual release chain.

---

## 2. Tags Inspected

| Tag | Resolved commit SHA | Subject (first line) |
|-----|----------------------|----------------------|
| `layer3-runtime-baseline` | `0283a2ed8eb77c21fda07a1c8f696dcc39508db1` | Merge integration/layer3-runtime-stack into main — Layer-3 baseline (M3.2–M3.4) |
| `layer3-runtime-governed-v1` | `23395b60bb72d70d01fbb6750c1ffb70760c3dcd` | Merge integration/layer3-next-verification — Layer-3 governed runtime (M3.1, M3.5, M3.6) |
| `GE_SFT_DATASET_v1_FROZEN` | (not resolved in this run) | Layer-2 dataset freeze |
| `stage6c-checkpoint-2026-03-03` | (not resolved in this run) | Stage-6C checkpoint |

Both release tags required by the plan resolve successfully.

---

## 3. Branches Inspected

- **main:** HEAD at `03acb511cc0ee723a5f6bbbb4b8275ffe069062d`. Branch is ahead of origin/main by 1 commit.
- **Local branches (from snapshot):** main, Layer-2-ML-Compilation-Stage-8-Controlled-SFT, feature/m3.10-m3.11-execution-isolation, feature/m3.6-shadow, integration/layer3-next-verification, integration/layer3-runtime-stack, layer3-plangate-decomposition, layer3-plugin-runtime-bridge, layer3-runtime-docs-emulator.
- **merge-base(main, layer3-runtime-baseline):** `0283a2ed` — equals baseline tag; baseline is ancestor of main.
- **merge-base(main, layer3-runtime-governed-v1):** `23395b60` — equals governed-v1 tag; governed-v1 is ancestor of main.
- **Containment:** main (and feature/m3.10-m3.11-execution-isolation, feature/m3.6-shadow, integration/layer3-next-verification, origin/main) contain commit `0283a2ed` (baseline).

---

## 4. Merge-Chain Findings

- Order: `layer3-runtime-baseline` (0283a2e) → `layer3-runtime-governed-v1` (23395b6) → later merges → main (03acb51). Main contains both tag commits. No rewriting observed; history linear for this chain.

---

## 5. Report-to-Git Consistency Findings

- **LAYER3_PARALLEL_BRANCH_AUDIT_REPORT.md** states: “layer3-runtime-baseline — tag present, points to `999f41c779cca775f631051d13b2fc7c2cfd9eb9`”. **Actual** `git rev-parse layer3-runtime-baseline^{commit}` at audit time: `0283a2ed8eb77c21fda07a1c8f696dcc39508db1`. Discrepancy recorded; possible typo or prior repo state in the earlier report. Do not overwrite that report; this audit records the current tag resolution.
- Roadmap claims “M3.0–M3.11 complete on main” and “Layer-3 baseline / governed-v1” merges; git shows main contains both release tags and the corresponding merge commits. **Consistent.**

---

## 6. Pass/Fail Verdict

**PASS.** Both release tags `layer3-runtime-baseline` and `layer3-runtime-governed-v1` resolve to intended merge commits; main contains both; merge-base and containment checks confirm ancestry. One existing report (LAYER3_PARALLEL_BRANCH_AUDIT_REPORT) cites a different baseline SHA (999f41c); documented as discrepancy; not treated as audit failure.
