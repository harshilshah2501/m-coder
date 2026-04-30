# Documentation Navigation Hub

This is the click-navigation entrypoint for docs. Use this page to move by intent (operate, validate, extend, troubleshoot) without guessing which file is current.

## Fast Start Routes

- **Simple path (pick automated vs manual API vs setup — read this first if docs feel fragmented):** [`../MOTADATA_SIMPLE_PATH.md`](../MOTADATA_SIMPLE_PATH.md)
- **API-only developer setup (current onboarding path):** [`guides/MCODER_API_ONLY_DEVELOPER_SETUP.md`](guides/MCODER_API_ONLY_DEVELOPER_SETUP.md)
- **`mcoder` CLI UX contract:** [`guides/MCODER_CLI_UX_CONTRACT_V1.md`](guides/MCODER_CLI_UX_CONTRACT_V1.md)
- **All user scenarios (Ask / Debug / Plan / Code / Agent) — root guide:** [`../MCODER_USER_SCENARIOS_GUIDE.md`](../MCODER_USER_SCENARIOS_GUIDE.md)
- **Current system truth:** [`LIVE_ROADMAP_TRACKER.md`](LIVE_ROADMAP_TRACKER.md)
- **Canonical doctrine/spec spine:** [`MASTER_SYSTEM_SPEC.md`](MASTER_SYSTEM_SPEC.md)
- **Program snapshot:** [`PROGRAM_STATE_SNAPSHOT.md`](PROGRAM_STATE_SNAPSHOT.md)
- **4-layer + product-slice map:** [`PRODUCT_SLICE.md`](PRODUCT_SLICE.md), [`ARCHITECTURE_4_LAYER.md`](ARCHITECTURE_4_LAYER.md)
- **Definitive demo + capability testbook:** [`MOTADATA_DEMOBOOK.md`](MOTADATA_DEMOBOOK.md)
- **Verifier output walkthrough (stdout + `motadata_behavior_validation.json`):** [`demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md`](demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md)

## Operator Navigation

- **Developer API-only onboarding:** [`guides/MCODER_API_ONLY_DEVELOPER_SETUP.md`](guides/MCODER_API_ONLY_DEVELOPER_SETUP.md)
- **CLI command/output/error contract:** [`guides/MCODER_CLI_UX_CONTRACT_V1.md`](guides/MCODER_CLI_UX_CONTRACT_V1.md)
- **Bring services up/down (governed path):** [`guides/ORCHESTRATOR_GUIDE.md`](guides/ORCHESTRATOR_GUIDE.md)
- **Optional local systemd wrapper:** [`guides/ORCHESTRATOR_SERVICE_GUIDE.md`](guides/ORCHESTRATOR_SERVICE_GUIDE.md)
- **Production verification flow (Motadata workspace):** [`guides/MOTADATA_VERIFICATION_GUIDE.md`](guides/MOTADATA_VERIFICATION_GUIDE.md)
- **Demo machine setup (GPU -> WSL -> Windows):** [`MOTADATA_DEMO_SETUP_RUNBOOK.md`](MOTADATA_DEMO_SETUP_RUNBOOK.md)
- **Demo narrative/success criteria:** [`MOTADATA_DEMO_SCENARIOS.md`](MOTADATA_DEMO_SCENARIOS.md)

## Capability Validation Navigation

- **Scenario definitions:** [`validation/motadata_aiops_behavior_scenarios.v1.json`](validation/motadata_aiops_behavior_scenarios.v1.json)
- **Quality policy:** [`validation/motadata_evidence_quality_policy.v1.json`](validation/motadata_evidence_quality_policy.v1.json)
- **Baseline artifact policy:** [`validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md`](validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md)
- **Post-closure maintenance rules:** [`validation/POST_CLOSURE_MAINTENANCE.md`](validation/POST_CLOSURE_MAINTENANCE.md)
- **Debug-depth charter/evidence:** [`DEBUG_DEPTH_CHARTER.md`](DEBUG_DEPTH_CHARTER.md), [`validation/DEBUG_DEPTH_CHARTER_CLOSURE_REPORT.md`](validation/DEBUG_DEPTH_CHARTER_CLOSURE_REPORT.md)
- **Dirty-buffer charter/evidence:** [`L5_7_DIRTY_BUFFER_CHARTER.md`](L5_7_DIRTY_BUFFER_CHARTER.md), [`validation/L57_DIRTY_BUFFER_CHARTER_CLOSURE_REPORT.md`](validation/L57_DIRTY_BUFFER_CHARTER_CLOSURE_REPORT.md)

## Engineering Navigation (Code Contracts)

- **Plan-Gate API surface:** [`runtime/README.md`](runtime/README.md), [`api/README.md`](api/README.md)
- **Runtime state transitions:** [`runtime/RUNTIME_STATE_TRANSITIONS.md`](runtime/RUNTIME_STATE_TRANSITIONS.md)
- **Developer CLI/API setup contract:** [`guides/MCODER_API_ONLY_DEVELOPER_SETUP.md`](guides/MCODER_API_ONLY_DEVELOPER_SETUP.md), [`guides/MCODER_CLI_UX_CONTRACT_V1.md`](guides/MCODER_CLI_UX_CONTRACT_V1.md)
- **Context Layer package/runtime contract:** [`packaging/motadata-context-layer/README.md`](../packaging/motadata-context-layer/README.md)
- **Observability references:** [`OBSERVATION/README.md`](OBSERVATION/README.md), [`../observation/README.md`](../observation/README.md)

## Troubleshooting Navigation

- **General troubleshooting:** [`troubleshooting/DEBUGGING_GUIDE.md`](troubleshooting/DEBUGGING_GUIDE.md)
- **Integration setup and checks:** [`guides/INTEGRATION_GUIDE.md`](guides/INTEGRATION_GUIDE.md)
- **Verification command failure triage:** [`guides/MOTADATA_VERIFICATION_GUIDE.md#9-troubleshooting`](guides/MOTADATA_VERIFICATION_GUIDE.md#9-troubleshooting)

## Indexed Catalog (Machine-Readable)

- **Catalog JSON:** [`index/doc_catalog.json`](index/doc_catalog.json)

The JSON catalog is intentionally compact so tooling can use it for route suggestions, docs search surfaces, and deterministic "start from here" jumps.
