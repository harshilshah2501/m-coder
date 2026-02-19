# Training Prep: 14B QLoRA

**Purpose:** Document training approach, dataset construction rules, risk forecast, and monitoring signals for 14B model SFT. Aligns with axis separation: pipeline corpus only; no governance exemplars; no mutation cases in training data.

**References:** AXIS_SEPARATION_LOCK.md, PHASE6_DATASET_FREEZE_CHECKLIST.md, phase6/POST_SFT_EVALUATION_PROTOCOL.md.

---

## 1. Training Approach

| Parameter | Recommendation | Notes |
|-----------|----------------|-------|
| Method | QLoRA | Quantized Low-Rank Adaptation. |
| Rank | 64–128 | Tune for stability vs capacity; avoid overfitting. |
| Epochs | 2–3 max | No overtraining; monitor validation loss and behavioral metrics. |
| Overtraining guard | Stop if refusal/phase metrics degrade | See Section 4. |

---

## 2. Dataset Construction

- **Use Phase-4 variants only.** Training rows are built from the frozen pipeline corpus: 17 base exemplars → 68 variants (Phase-4). No other exemplar set.
- **Do NOT include mutation cases.** Mutation harness cases are for stress-testing and evaluation only. They are not SFT training input.
- **Do NOT include governance exemplars.** GREG/constitutional abstract exemplars must not enter the training dataset. Pipeline corpus (Motadata) only.

Dataset assembly must follow the deterministic compilation rules in the Golden Exemplars Guide (e.g. provenance, no semantic rewriting).

---

## 3. Risk Forecast

| Risk | Description | Mitigation |
|------|-------------|------------|
| REF erosion | Model softens refusal or adds conditional allowance in REF cases | Freeze checklist + post-SFT REF collapse metric; rollback if > 5%. |
| CONF gravitational amplification | Model defaults to CONF-like posture; CONF index rises | Gravitational balance gate (< 45% in mutation); monitor post-SFT CONF index. |
| MIX collapse tendency | Model collapses MIX to single-pressure CONF | MIX→CONF collapse rollback threshold (> 10%); MIX cases in mutation set. |
| CODE abstraction drift | Model answers CODE with reasoning abstraction instead of guard logic | Post-SFT check for CODE abstraction drift; rollback if detected. |

---

## 4. Monitoring Signals

During and after training, monitor for:

- **Refusal weakening** — REF exemplars answered with allowance or softened refusal.
- **Softened boundary language** — Irreversible boundary phrase paraphrased or relaxed.
- **Conditional leakage in REF** — REF responses containing “if … then allow” structure.
- **Implementation recommendation in DES** — DES exemplars answered with execution or deployment recommendation instead of design-only reasoning.

These signals feed into the Post-SFT Evaluation Protocol and rollback criteria.
