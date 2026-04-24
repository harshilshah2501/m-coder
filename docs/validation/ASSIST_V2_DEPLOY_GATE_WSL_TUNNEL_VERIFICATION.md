# Assist v2 — Objective, tests, WSL tunnel run, results, and conclusion

Date: 2026-04-24  
Status: verification record (artifact-driven)  
Related: `ASSIST_V2_API_CONTRACT_FREEZE_V1.md`, `ASSIST_V2_API_FREEZE_DEPLOY_GATE_REPORT.md`, `docs/guides/ASSIST_V2_BACKEND_DEPLOY_HARDENING_RUNBOOK.md`

## 1) Objective

**Primary goal:** Prove that a **remote** Plan-Gate stack (the same HTTP surfaces used in deployment) satisfies the **frozen Assist v2 contract** and the **strict HTTP deploy gate**, without changing architecture, retrieval, governance, or execution semantics.

**This verification is intentionally narrow:**

- Confirm Ask structured shape, weak-Ask investigate omission, Debug shape and fail-closed behavior, and **graph preflight `COMPLETE`** under the gate script’s deterministic checks.
- Record how verification is run from **WSL** when Plan-Gate is reached via **SSH local port forwarding** (so `http://127.0.0.1:8089` on WSL is the tunnel endpoint, not a separate “fake” Plan-Gate process on the laptop).

**Explicitly out of scope for this objective:** plugin work, model upgrades (for example Qwen3), UI changes, new routing surfaces, and **Plan/Code productization** (that is the **next** phase after this record).

## 2) References (what was frozen and how it is tested)

| Artifact | Role |
|----------|------|
| `docs/validation/ASSIST_V2_API_CONTRACT_FREEZE_V1.md` | Canonical Ask / Debug / Investigate contract and invariants |
| `runtime/scripts/assist_v2_http_deploy_gate.py` | Strict HTTP regression gate (default: graph preflight **required**) |
| `runtime/tests/test_assist_v2_http_deploy_gate.py` | Unit-level gate behavior against a local stub server |
| `docs/guides/ASSIST_V2_BACKEND_DEPLOY_HARDENING_RUNBOOK.md` | Pre-deploy checklist, startup, strict vs local-smoke commands, rollback |
| `scripts/wsl_plugin_mvp_stack.sh` | WSL stack helper; documents **optional SSH tunnel** so `PLAN_GATE_URL` may be `http://127.0.0.1:8089` while traffic is forwarded to the remote host’s Plan-Gate port |

Merge and release pointer on `main`:

- Tag: `assist-v2-api-freeze-deploy-gate-complete` (merge that introduced freeze + gate + runbook + tracker closure for this pack).

## 3) Why `127.0.0.1` does not mean “local-only Plan-Gate”

When `ENABLE_SSH_TUNNEL=1`, `wsl_plugin_mvp_stack.sh` starts an SSH tunnel with local forwards, for example Plan-Gate `LOCAL_PLAN_GATE_PORT` → `REMOTE_PLAN_GATE_HOST:REMOTE_PLAN_GATE_PORT` on the SSH target (see script header and `start_tunnel_if_enabled`).

Therefore:

- **`--plan-gate-url http://127.0.0.1:8089`** on WSL means: **send HTTP to the tunnel’s local listener**, which forwards to **the remote Plan-Gate** bound on the tunnel target host.
- The deploy gate still exercises **real** `/v1/ask` (and related) behavior on that remote service, subject to tunnel latency and SSH availability.

Health/latency probes against `127.0.0.1:8089` measure **loopback + tunnel + remote** combined, which is appropriate for this verification pattern.

## 4) What the strict gate tests (summary)

The script aggregates four checks; strict mode keeps **`require_graph_preflight=true`** (omit `--skip-graph-preflight`).

| Check | Meaning (short) |
|-------|------------------|
| `grounded_ask_shape` | Grounded Ask responses match expected Assist v2 Ask shaping and invariants (`v1_evidence`, `PLAN_ONLY`, `execution=false`, etc.). |
| `weak_ask_investigate_omission` | Weak / ungrounded Ask path does **not** expose an inappropriate Investigate bridge. |
| `debug_shape_and_fail_closed` | Debug responses preserve required structure and fail-closed behavior for the missing-file insufficiency scenario. |
| `graph_preflight_healthy` | Graph ingest / anchor counters meet configured thresholds; state must be **`COMPLETE`** when preflight is required. |

Pass criteria for a run:

- Process exit code **`0`**
- Top-level **`"all_pass": true`**
- **`errors`** is an empty array

## 5) Preconditions

1. **Repo** at a revision that includes `runtime/scripts/assist_v2_http_deploy_gate.py` (for example `main` at or after merge `851abff`, or tag `assist-v2-api-freeze-deploy-gate-complete`).
2. **Python environment** on WSL with dependencies required by Plan-Gate client code paths used inside the gate (same as normal stack usage).
3. **SSH tunnel** to the host where Plan-Gate listens, per `scripts/wsl_plugin_mvp_stack.sh` (or equivalent `ssh -L` forwards), so Plan-Gate is reachable at the local URL you export.
4. **Remote Plan-Gate and dependencies** (Context Layer, graph endpoint reachable from Plan-Gate for preflight, etc.) consistent with your stack; the gate does not substitute for full infra runbooks.

## 6) Exact commands (WSL, tunnel, strict gate)

From repository root:

```bash
cd ~/Harshil-PoCs/m-coder   # or your clone path

# After tunnel is up: local URL points at forwarded remote Plan-Gate
export STAGING_PLAN_GATE_URL='http://127.0.0.1:8089'

python3 runtime/scripts/assist_v2_http_deploy_gate.py \
  --plan-gate-url "$STAGING_PLAN_GATE_URL" \
  --timeout-s 20 \
  --out runtime/.run/assist_v2_http_deploy_gate.staging.json

echo $?
```

Sanity probe (optional):

```bash
curl -sS -o /dev/null -w 'http_code=%{http_code} time_total=%{time_total}\n' \
  "${STAGING_PLAN_GATE_URL%/}/healthz"
```

Inspect artifact:

```bash
jq '.all_pass, .errors,
    .checks.grounded_ask_shape,
    .checks.weak_ask_investigate_omission,
    .checks.debug_shape_and_fail_closed,
    .checks.graph_preflight_healthy' \
  runtime/.run/assist_v2_http_deploy_gate.staging.json
```

Note: `runtime/.run/` is typically gitignored. The strict gate’s `--out` path above is the canonical **working** artifact location (you can also copy the same JSON into `runtime/.run/` if it was produced elsewhere). For a **durable, repo-stored** evidence file, duplicate into `TestRunEvals/` (or attach to CI).

## 7) Observed results (verification run)

The following was observed on a **strict** run from WSL against Plan-Gate reached through the SSH tunnel (`STAGING_PLAN_GATE_URL` → `http://127.0.0.1:8089`).

| Field | Value |
|-------|--------|
| Exit code | `0` |
| `all_pass` | `true` |
| `errors` | `[]` |
| `grounded_ask_shape.pass` | `true` |
| `weak_ask_investigate_omission.pass` | `true` |
| `debug_shape_and_fail_closed.pass` | `true` |
| `graph_preflight_healthy.pass` | `true` |
| `graph_preflight_healthy.required` | `true` |
| Graph `state` | `COMPLETE` |
| Graph `reason` (example) | `graph ingest counters satisfy required thresholds` |
| Example `anchor_counts` | `VERTICLE_REGISTRATION`: 8; `EVENTBUS_CONSUMER_REGISTRATION`: 22; `API_ROUTE_REGISTRATION`: 222 |
| Matching `thresholds` (example) | 5 / 10 / 1 respectively |
| `/healthz` (example) | HTTP 200, `time_total` on the order of **~0.14s** (includes tunnel path) |

Re-running the same command without `--timeout-s` used the script default (`20`); outcome remained **`all_pass: true`**.

## 8) Conclusion

**Conclusion:** For the remote Plan-Gate instance reached from WSL via the documented SSH tunnel pattern, the **strict Assist v2 HTTP deploy gate passed** with **graph preflight required and healthy**. Ask shaping, weak-Ask investigate omission, and Debug fail-closed checks are green under the frozen gate, matching the intent of the API freeze and deploy-hardening phase.

This closes the verification story for **“freeze contract + ship deterministic gate + prove remote stack through WSL tunnel”** before expanding product behavior.

## 9) Next engineering phase (explicit handoff)

**Next focus:** **Plan + multi-step Code reasoning solidification** on top of the **frozen** Assist v2 HTTP contract and passing deploy gate, without reopening plugin surfaces, model swaps, or UI-heavy work unless separately staffed.

Use existing Plan/Code validation and behavior guides as the starting rails; treat Assist v2 as **stable substrate** for that work.
