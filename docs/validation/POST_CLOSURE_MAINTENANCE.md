# Post-closure maintenance & optional charters

**Purpose:** Ongoing **operational discipline** after the Motadata behavior-verification **closure** (see `MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md`). This is **not** an open “MVP closure checklist” — closure items **01–09** are **complete**. Use this file for **maintenance** and **optional** follow-on work only.

---

## 1. Operational lock (every tuning or stack change)

Keep **`motadata_behavior_verify.py`** comparable across runs:

| Invariant | Record in run notes / PR |
|-----------|---------------------------|
| **`--workspace-root`** | Same Motadata tree (or document if intentionally changed) |
| **`--scenarios`** | `docs/validation/motadata_aiops_behavior_scenarios.v1.json` unless charter expands suite |
| **`--quality-policy`** | `docs/validation/motadata_evidence_quality_policy.v1.json` unless policy version changes |
| **Stage A mode** | Same `--export-stage-a` / server env as baseline (`LexicalRetrievalConfig` / `MOTADATA_L5_*`) |

**Artifacts:** On any retrieval or quality change, save a **named** candidate, e.g.  
`runtime/.run/motadata_behavior_validation.CANDIDATE.<label>.motadata.json`, and diff or compare against **`docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5**.

**Regression reports must cite:** m-coder **git SHA** + **`workspace_identity_hash`** from the artifact (see §5) + note Stage A + policy file.

**Canonical command shape:**

```bash
PYTHONPATH=. python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenarios-only \
  --print dev \
  --out "runtime/.run/motadata_behavior_validation.CANDIDATE.<label>.motadata.json"
```

Full stack setup: `docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md`.

---

## 2. Living checklist (this file — not “closure todos”)

- **Closure gate list 01–09:** **DONE** — do not treat as blocking.
- **This section:** refresh only when **process** changes (e.g. new policy file version, new scenario pack).

---

## 3. No architecture churn (default)

- Do **not** add parallel retrieval stacks, new authority sources, or ambiguous Ask routes without **explicit charter** + §5 regression proof.
- **Optional** next-phase work is tracked under **`docs/LIVE_ROADMAP_TRACKER.md` §1.4** (e.g. **debug depth / `CHARTER-TBD`**, **§B1 / L5-RET** with §5 guardrails).

---

## 4. Where optional charters live

| Topic | Pointer |
|--------|---------|
| Debug depth / richer **`explain_debug`** / vLLM | Tracker **§1.4** row **CHARTER-TBD** |
| Broader exploratory asks / L5-RET | Tracker **§1.4** — metrics + **§5** guardrails |
| Baseline promotion / artifact naming | `MOTADATA_BASELINE_ARTIFACT_POLICY.md` |

---

## 5. Related docs

- `docs/validation/MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md` — what closed and evidence pointers  
- `docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5 — promoted baseline  
- `docs/PROGRAM_STATE_SNAPSHOT.md` — short program snapshot  
- `docs/SYSTEM_TRUTH.md` — canonical contradictions / invariants  
