# Axis Separation Lock

**Purpose:** Formally encode and lock the two-axis architecture of the Golden Exemplars Program. The constitution is normative law only; training and evaluation operate exclusively on the pipeline corpus.

**Status:** LOCKED  
**Scope:** Governance vs Compilation; no corpus modification.

---

## 1. Two-Axis Architecture

| Axis | Role | SFT Input? |
|------|------|------------|
| **Constitutional Phase Axis** | Governance doctrine: REF, CONF, DES, MIX, CODE, REACH. Defines law, dominance rules, freeze gates, collapse detection. | **No.** |
| **Pipeline Phase Axis** | Compilation corpus: base exemplars → variants → mutation harness → freeze → SFT. | **Yes (pipeline corpus only).** |

The constitution is **NOT** part of the SFT dataset. Training and evaluation operate **ONLY** on the pipeline corpus.

---

## 2. Layer Diagram

```
Layer 0 — Constitutional Doctrine (Governance; not SFT input)
         │
         │  Defines: phase semantics, dominance hierarchy, boundary invariance,
         │           freeze gates, collapse detection. NEVER fed to model.
         ▼
Layer 1 — Product Base Exemplars (17)
         │  Motadata BASE-001 … BASE-017. Phase-3 locked.
         ▼
Layer 2 — Variants (68)
         │  4 variants per base. Phase-4 locked.
         ▼
Layer 3 — Mutation Harness (Phase-6)
         │  Pre-SFT stress; tests preservation of constitutional behavior.
         ▼
Layer 4 — Dataset Freeze
         │  Checklist pass → frozen dataset; no further corpus change.
         ▼
Layer 5 — SFT (14B QLoRA)
         │  Training on pipeline corpus only. No governance exemplars.
         ▼
Layer 6 — Post-SFT Drift Evaluation
           Mutation re-run; ledger diff; rollback if inversion detected.
```

---

## 3. Explicit Lock Statements

1. **Constitution is normative law only.** It defines what judgment must do. It is not a training input.

2. **Pipeline corpus is SFT-only.** Only Layer 1 (bases) and Layer 2 (variants) — after freeze — may be compiled into the training dataset. Governance exemplars (e.g. GREG corpus) are excluded.

3. **Governance exemplars MUST NOT enter the training dataset.** No constitutional/GREG exemplars in the SFT build. Training consumes only the product compilation corpus (Motadata 17 bases, 68 variants).

4. **Post-SFT results MUST NOT redefine constitutional doctrine.** If evaluation shows drift or collapse, the response is rollback or harness fix — not changing REF/CONF/MIX semantics or dominance rules.

---

## 4. Failure Condition: Constitutional Inversion Event

**Definition:** A **Constitutional Inversion Event** occurs when training or post-SFT behavior causes, or is used to justify, redefinition of REF/CONF/MIX (or other phase) semantics, dominance rules, or boundary doctrine.

**Response:**

- **Freeze** further SFT runs and dataset changes.
- **Rollback** to last approved freeze and/or model checkpoint.
- **Root-cause** via ledger diff and evaluation protocol; fix harness or data pipeline — **not** the constitution.

Constitutional doctrine is updated only through governance versioning (e.g. Manifest v1.1), never as a result of training metrics or model behavior.

---

## 5. References

- Constitutional phase definitions and dominance: `governance/CONSTITUTIONAL_MANIFEST_v1.0.md`
- Pipeline phases and freeze: `phase6/PHASE6_DATASET_FREEZE_CHECKLIST.md`
- Post-SFT evaluation and rollback: `phase6/POST_SFT_EVALUATION_PROTOCOL.md`
