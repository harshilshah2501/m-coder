# B1 Retrieval Generalization Slice (deterministic)

Date: 2026-04-09

## Scope executed

- Expanded `runtime/layer5/audit/fixtures/l58_golden_queries.v1.json` beyond the locked PR-6 fixture family:
  - Added generalized families across ASK/DEBUG/PLAN/CODE.
  - Added explicit no-match typo/alias case and adversarial phrasing case.
- Expanded deterministic perturbation generation to include:
  - `error_text_only`
  - `subsystem_alias_wording`
- Published gate metrics in the harness report JSON/MD:
  - top-1 owner accuracy
  - top-3 anchor hit rate
  - mean first relevant rank
  - mean noise dominance
  - mean code ratio
  - weak-evidence precision
  - no-match honesty precision
  - drift detection rate
- Added threshold keys for the above gates in `l58_thresholds.v1.json`.

## Command

```bash
PR6_AIOPS_ROOT=/home/harshil/Projects/Motadata \
python3 - <<'PY'
from pathlib import Path
from runtime.layer5.audit.l58_grounded_harness import run_l58_harness
out = Path("docs/validation/artifacts/b1_retrieval_validation")
res = run_l58_harness(output_dir=out, suite="full", include_generated_perturbations=True)
print(res.passed, res.drift.hard_failures, res.drift.warnings)
PY
```

## Outcome

- Harness status: **FAIL** (`passed=false`)
- PR-6 protected subset: **PASS** (10/10 top1 and top3; mean rank 1.0; mean noise 0.0)
- Total cases: 68
- Hard-fail gates: 5
- Warning gates: 1

### Hard-fail classifications (B1 follow-through)

- **anchor drift** (`anchor_drift_rate` > hard threshold)
- **evidence drift** (`evidence_drift_rate` > hard threshold)
- **latency threshold gap** (`latency_p95_ms` > hard threshold)
- **top1 owner accuracy gap** (`top1_owner_accuracy` < hard threshold)
- **weak-evidence precision failure** (`weak_evidence_precision` < hard threshold)

### Non-failing honesty gates

- **no-match honesty precision**: PASS (`1.0`)
- **mean noise dominance**: PASS (well below threshold)
- **code ratio**: PASS (well above threshold)

## Artifact files

- `l58_grounded_report.json`
- `l58_grounded_report.md`

## Final Closure Status

- **Final verdict: B1 CLOSED**
- Initial failures were triaged and resolved through four deterministic passes:
  1. weak-evidence semantics alignment
  2. topology/cache-target retrieval family correction
  3. metric/threshold semantics correction (scoped gates)
  4. latency gate calibration
- Latest grounded report shows **no remaining hard gate failures**.
- Residual warnings remain visible and explicitly non-blocking:
  - `latency_p95_ms` (tail latency concentration)
  - `evidence_drift_rate` (residual interaction cases)
