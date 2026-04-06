# AIOps MVP Final Report — filled snapshot (2026-04-06)

> Template reuse: For a new batch, copy this file, replace header + sections 2–6 with the new run_summary.json and artifacts. Canonical queries: docs/validation/aiops_mvp_scenarios.v1.json (top_k_default: 12).

Closure baseline for comparison: 1 PASS / 7 PARTIAL — see docs/validation/MVP_PRODUCTION_CLOSURE_NOTE.md and LOW_CORE_RATIO_DECISION.md section B.

---

## 1) Header

| Field | Value |
|-------|--------|
| Date | 2026-04-06 |
| Batch generated_utc | 2026-04-06T16:02:43Z |
| Repo path | /home/harshil/Harshil-PoCs/m-coder |
| Branch | chore/aiops-mvp-validation-and-pack-reliability (report file update branch) |
| Commit | f2dd73a (docs commit in this repo; batch commit not captured in summary payload) |
| Motadata root (locked) | /home/harshil/Projects/Motadata |
| Context Layer | http://127.0.0.1:8091 |
| Plan-Gate | http://127.0.0.1:8089 |
| Export timeout (batch) | 1200 s |
| Ask timeout (batch) | 7200 s |
| Ask connection retries | 3 |
| Ask retry delay | 10 s |

---

## 2) Execution Summary

| Metric | Value |
|--------|--------|
| Total scenarios planned | 8 |
| Total scenarios run | 8 |
| PASS | 8 |
| PARTIAL | 0 |
| FAIL | 0 |
| ERROR | 0 |
| Artifact pack complete | Yes |
| Machine summary | /home/harshil/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp/summary/run_summary.json |
| Human-readable summary | /home/harshil/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp/summary/run_summary.md |

Delta vs closure baseline:
- Previous baseline: 1 PASS / 7 PARTIAL.
- Current batch: 8 PASS / 0 PARTIAL.

---

## 3) Per-Scenario Results

Queries are from docs/validation/aiops_mvp_scenarios.v1.json. Verdicts below are the automated signal from run_summary.json and scenario ask_response metadata.

### A1 (ASK)

- Result: PASS
- Evidence quality: STRONG
- quality_reasons: []
- Artifacts: /home/harshil/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp/scenario_A1/

### A2 (ASK)

- Result: PASS
- Evidence quality: STRONG
- quality_reasons: ["QUERY_TOO_GENERIC"]
- Artifacts: /home/harshil/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp/scenario_A2/

### D1 (DEBUG)

- Result: PASS
- Evidence quality: STRONG
- quality_reasons: []
- Artifacts: /home/harshil/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp/scenario_D1/

### D2 (DEBUG)

- Result: PASS
- Evidence quality: STRONG
- quality_reasons: []
- Artifacts: /home/harshil/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp/scenario_D2/

### P1 (PLAN)

- Result: PASS
- Evidence quality: STRONG
- quality_reasons: []
- Artifacts: /home/harshil/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp/scenario_P1/

### P2 (PLAN)

- Result: PASS
- Evidence quality: STRONG
- quality_reasons: []
- Artifacts: /home/harshil/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp/scenario_P2/

### C1 (CODE)

- Result: PASS
- Evidence quality: STRONG
- quality_reasons: []
- Artifacts: /home/harshil/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp/scenario_C1/

### C2 (CODE)

- Result: PASS
- Evidence quality: STRONG
- quality_reasons: []
- Artifacts: /home/harshil/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp/scenario_C2/

---

## 4) Cross-Scenario Findings

### Strongest scenarios

- All eight scenarios are automated PASS with STRONG evidence_quality.
- A2 includes QUERY_TOO_GENERIC while still yielding PASS and STRONG.

### Weakest scenarios

- None by automated verdict in this batch (no PARTIAL/FAIL/ERROR).

### Common patterns in this run

- No LOW_CORE_RATIO surfaced in scenario metadata.
- End-to-end export + ask pipeline remained stable across all categories (ASK/DEBUG/PLAN/CODE).

### Failure classification

| Class | Notes |
|-------|--------|
| Retrieval-related | No automated retrieval weakness signal in this run. |
| Grounding-related | All scenarios reached STRONG evidence quality metadata. |
| Deployment / parity | No runtime error class observed (ERROR = 0). |

---

## 5) MVP Verdict

Selected: MVP demo ready (A)

Rationale:

- End-to-end chain completed with scenario status ok for all 8 scenarios in the machine summary.
- Automated usefulness signal is 8/8 PASS with STRONG evidence quality in every scenario.
- This batch exceeds the earlier closure baseline and does not show the prior LOW_CORE_RATIO-dominated pattern.

---

## 6) Artifact Index

| Path | Role |
|------|------|
| /home/harshil/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp/summary/run_summary.json | Machine counts + per-scenario metadata |
| /home/harshil/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp/summary/run_summary.md | Human-readable batch summary |
| docs/validation/artifacts/aiops_mvp/scenario_*/ | Per-scenario export_request/export_response and ask_request/ask_response |
| docs/validation/MVP_PRODUCTION_CLOSURE_NOTE.md | Prior closure baseline for comparison |
| docs/validation/LOW_CORE_RATIO_DECISION.md | Prior LOW_CORE_RATIO decision context |
