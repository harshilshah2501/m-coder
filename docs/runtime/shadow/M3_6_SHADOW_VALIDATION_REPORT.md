# M3.6 Shadow Mode Validation Report

## Run summary

- **Branch:** feature/m3.6-shadow  
- **Baseline tag:** layer3-runtime-baseline  
- **Date:** 2026-03-13  

## Commands executed

```bash
python3 -m pytest runtime/tests/shadow_runner_test.py runtime/tests/shadow_harness_test.py runtime/shadow/tests/test_shadow_protocol_v0_1.py -v
python3 -m pytest runtime/tests/test_emulator_invariants.py -v
python3 -m runtime.shadow_runner.run_demo
```

## Results

| Suite | Result | Count |
|-------|--------|-------|
| shadow_runner_test | PASS | 11 tests |
| shadow_harness_test | PASS | 11 tests |
| test_shadow_protocol_v0_1 | PASS | 11 tests |
| test_emulator_invariants | PASS | 28 tests |
| shadow_runner run_demo | PASS | 3 scenarios, invariants held |

## Invariant checks

- **S-1:** No scenario emitted `boundary_verdict=crossed` or `boundary_crossed=true`.  
- **S-2:** Plan and ledger emitted for every scenario.  
- **S-3:** `plan_hash` consistent between decision, ledger, and run record.  
- **S-6:** Ingestion batch items contain `request_id`, `plan`, `ledger_row`.  

## Representative cases

- **REF:** merge_without_approval (no approval) → REFUSAL, refuse.  
- **CONF:** commit_prod_change (with approval) → BOUNDED_ALLOW, bounded_allow.  
- **DES:** safe_commit (no boundary) → SAFE_EXECUTE, safe_execute.  

## Conclusion

Shadow mode validation (M3.6) meets the success criteria: full governed path, plan + ledger emission, no boundary crossed, and ingestion batch structure validated.
