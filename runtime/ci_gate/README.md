# CI Backstop Gate v0.1

CLI client that calls the local Plan-Gate Service and fails the build on REFUSAL or CONDITIONAL_BLOCK.

## Usage

```bash
python3 -m runtime.ci_gate.cli \
  --input <ci_input.json> \
  --endpoint http://127.0.0.1:8089/v0/plan \
  --mode shadow \
  --fail-on REFUSAL,CONDITIONAL_BLOCK \
  [--fixed-time "2026-03-01T00:00:00Z"] \
  [--no-strict]
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Decision not in fail-on set (e.g. BOUNDING, APPROVE) |
| 1 | Decision in fail-on set (REFUSAL, CONDITIONAL_BLOCK) |
| 2 | Request invalid or service unreachable (strict mode) |

## CI Input Format (ci_input.json)

- `repo` — repository name
- `branch` — branch name
- `action_type` — PR_MERGE, CONFIG_CHANGE, DEPLOY_INTENT, etc.
- `target` — target (e.g. main, config/prod.yaml)
- `evidence_refs` — optional list of evidence
- `diff_refs` — optional (not yet used in mapping)

Maps deterministically to PlanRequest v0.1.
