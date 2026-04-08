# Workspace backend on native Linux — governed GPU stack (proof)

**Date:** 2026-04-08  
**Host:** native Linux (Ubuntu; `WSL_DISTRO_NAME` empty) — **not WSL**.

**Topology this run:** services **co-located** on one machine (`127.0.0.1` for Context Layer **8091**, Plan-Gate **8089**, vLLM **8000**). Same contracts apply when Plan-Gate+vLLM run on a **remote GPU** and URLs point via SSH tunnel — connectivity is the only delta.

## PASS criteria met

| Step | Check | Result |
|------|--------|--------|
| 1 | `GET /healthz` Context Layer | HTTP 200, `status: ok` |
| 2 | `GET /healthz` Plan-Gate | HTTP 200 |
| 2 | `GET /v1/models` vLLM | HTTP 200, `motadata-coder` present |
| 3 | `POST /v1/export_evidence` | JSON bundle with `entries` (3) |
| 3 | `POST /v0/ask` | `plan_only_response.v0.1`, `governance_posture: PLAN_ONLY`, `execution: false`, `error: null` |

## Artifacts

| File | Contents |
|------|----------|
| `b5_linux_backend_proof_run.txt` | Health + vLLM models excerpt |
| `b5_export_evidence_summary.txt` | Export bundle key/entry count |
| `b5_v0_ask_summary.txt` | Parsed Ask response fields |
| `b5_v0_ask_response.json` | Full `/v0/ask` response |
| `b5_env_snapshot_sanitized.txt` | Relevant env vars (may be minimal in CI) |

## Interpretation

- **No misleading success:** Ask returned explicit `PLAN_ONLY` and `execution: false` (plan-only path).
- **Backend → Plan-Gate:** `/v0/ask` completed without HTTP error; routing `plan_only` (no Explain path invoked for this query).
