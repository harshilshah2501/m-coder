# M3.6 Baseline Scenario Corpus

Scenarios used by the shadow runner and validation harness. Defined in `runtime/shadow/baseline_scenarios.py`.

| ID | Expected phase | Expected posture | Action type | Description |
|----|----------------|------------------|-------------|-------------|
| ref_merge_without_approval | REF | refuse | merge_without_approval | Merge without approval → refuse |
| conf_commit_prod_change | CONF | bounded_allow | commit_prod_change | Commit prod change with approval → bounded_allow |
| des_safe_commit | DES | safe_execute | safe_commit | Safe commit, no boundary → safe_execute |
| ref_risky_without_token | REF | refuse | merge_without_approval | Risky action without token → refuse |
| conf_deploy_intent | CONF | bounded_allow | deploy_production | Deploy intent with approval → bounded_allow |

All scenarios run with `mode="shadow"`. Plan and ledger are emitted for each; boundary is never crossed.
