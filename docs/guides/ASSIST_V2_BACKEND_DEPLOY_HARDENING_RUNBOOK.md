# Assist v2 Backend Deploy Hardening Runbook

Date: 2026-04-23  
Phase: API freeze + deploy gate  
Scope: backend only (plugin/UI out of scope)

## 1) Purpose

Provide deterministic pre-deploy, startup, verification, and rollback procedures for frozen Assist v2 backend surfaces:

- Ask structured shaping
- Debug structured shaping
- Ask-to-Debug Investigate bridge

## 2) Pre-deploy checklist

- [ ] Branch/commit is on `main` and includes Assist v2 freeze docs.
- [ ] `runtime.plan_gate_service` starts cleanly.
- [ ] `runtime.context_layer_service` reachable on expected host/port.
- [ ] `runtime/scripts/assist_v2_http_deploy_gate.py` is present.
- [ ] Graph preflight dependencies are installed in deploy environment (neo4j driver + graph endpoint reachability).
- [ ] No unresolved schema validation errors for `/v1/ask`.

## 3) Startup procedure

From repo root:

```bash
# Terminal 1: Context Layer
python3 -m runtime.context_layer_service
```

```bash
# Terminal 2: Plan-Gate
export PLAN_GATE_PORT=8089
python3 -m runtime.plan_gate_service.app
```

Health checks:

```bash
curl -sS http://127.0.0.1:8091/healthz | jq .
curl -sS http://127.0.0.1:8089/healthz | jq .
```

## 4) Post-deploy verification commands

### 4.1 Strict deploy gate (includes graph preflight requirement)

```bash
python3 runtime/scripts/assist_v2_http_deploy_gate.py \
  --plan-gate-url http://127.0.0.1:8089 \
  --out runtime/.run/assist_v2_http_deploy_gate.deploy.json
```

Pass criteria:

- process exits with code `0`
- `all_pass=true`
- `checks.graph_preflight_healthy.pass=true`
- `checks.grounded_ask_shape.pass=true`
- `checks.weak_ask_investigate_omission.pass=true`
- `checks.debug_shape_and_fail_closed.pass=true`

### 4.2 Local non-graph smoke (developer machine only)

```bash
python3 runtime/scripts/assist_v2_http_deploy_gate.py \
  --plan-gate-url http://127.0.0.1:8089 \
  --skip-graph-preflight \
  --out runtime/.run/assist_v2_http_deploy_gate.local.json
```

Use only for local smoke where graph stack is intentionally unavailable.

### 4.3 WSL + SSH tunnel: strict gate against remote Plan-Gate

If Plan-Gate is on a **remote** host, start the tunnel per `scripts/wsl_plugin_mvp_stack.sh` (`ENABLE_SSH_TUNNEL=1`, `PLAN_GATE_URL=http://127.0.0.1:8089`, etc.). Then run the **same strict gate** as §4.1; the local URL is the tunnel endpoint.

Full objective, commands, observed results, and conclusion:

- `docs/validation/ASSIST_V2_DEPLOY_GATE_WSL_TUNNEL_VERIFICATION.md`

### 4.4 Deep slice behavior verification (WSL/staging)

Use canonical commands from:

- `docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md`

Minimum acceptance:

- Ask deep slice pass
- Debug deep slice pass
- graph preflight `COMPLETE`

## 5) Healthy-state definition

Deployment is healthy only when all are true:

- Ask remains `v1_evidence`, `PLAN_ONLY`, and `execution=false`
- Debug responses keep top-level `explain_debug` and include `assist_v2.debug_v2` in debug mode
- Investigate bridge appears for grounded Ask and is omitted for weak Ask
- Missing-file Debug remains fail-closed (`grounding_tier=none`, explicit insufficiency)
- Graph preflight state is `COMPLETE` in deploy/staging gate runs

## 6) Rollback notes

If deploy gate fails:

1. Stop services and restore prior known-good tag/commit.
2. Restart Context Layer and Plan-Gate.
3. Re-run strict deploy gate script to confirm restoration.
4. Preserve failed gate artifact JSON for root-cause review.

Rollback command pattern:

```bash
git checkout <known_good_tag_or_commit>
```

## 7) Artifact and log locations

- Deploy gate outputs:
  - `runtime/.run/assist_v2_http_deploy_gate.deploy.json`
  - `runtime/.run/assist_v2_http_deploy_gate.local.json`
  - `runtime/.run/assist_v2_http_deploy_gate.staging.json` (example name for tunnel/remote strict runs; often gitignored — copy to `TestRunEvals/` to retain)
- Behavior verification outputs:
  - `runtime/.run/motadata_behavior_validation.ask.deep.json`
  - `runtime/.run/motadata_behavior_validation.debug.deep.json`
  - `runtime/.run/motadata_behavior_validation.20slice.json`
- Service logs (depending on operator launch mode):
  - `runtime/.run/*.log`

## 8) Explicit out-of-scope for this phase

- Plugin work
- Model upgrades
- Retrieval redesign
- New reasoning modes
- Multi-hop tracing
- Auto-debug/auto-fix
