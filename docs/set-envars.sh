#!/usr/bin/env bash
# Environment defaults for **WSL** (Context Layer) and **Windows/JetBrains** clients calling
# Plan-Gate + vLLM on the **GPU** over SSH tunnels or direct IPs.
#
# This matches the operating profile in docs/MOTADATA_DEMO_SETUP_RUNBOOK.md (Phase 2 WSL,
# Phase 3 Windows). The GPU is a backend; you do **not** need m-coder on WSL to run validation
# scenarios—only HTTP clients (`curl`, plugin).
#
# Usage:  source docs/set-envars.sh
# Optional query:  source docs/set-envars.sh 'your query here'
#
# Paths
# -----
# WORKSPACE_ROOT — Motadata **on WSL** for Context Layer `POST /v1/export_evidence`. Primary path.
#   **You do not need Motadata on the GPU** for that flow (evidence → POST /v1/ask).
# PLAN_GATE_REPO_ROOT — **Optional / v0 only:** `repo_root` in `POST /v0/ask` (Plan-Gate reads repo
#   on GPU). Skip unless you test server-side ContextEngine. See DEBUG_PATH_VALIDATION_RUNBOOK.md.
#   export PLAN_GATE_REPO_ROOT=/ABSOLUTE/PATH/TO/workspace
#
# URLs (WSL → services)
# ---------------------
# CONTEXT_URL — Context Layer in WSL (default 127.0.0.1:8091 per demo runbook).
# PLAN_GATE_URL — Plan-Gate on GPU; from WSL use **127.0.0.1:8089** when using SSH local forward
#   from WSL to GPU, or set to http://<gpu-ip>:8089 if routed.
# VLLM_URL — Usually not called from WSL directly; forwarded 127.0.0.1:8000 or GPU IP. Used if you
#   run local tools that probe vLLM.

export WORKSPACE_ROOT="${WORKSPACE_ROOT:-}"

# Plan-Gate /v0/ask: set explicitly (path on GPU, readable by Plan-Gate user — NOT /root/... unless root).
# export PLAN_GATE_REPO_ROOT=/ABSOLUTE/PATH/TO/workspace

export CONTEXT_URL="${CONTEXT_URL:-http://127.0.0.1:8091}"
export PLAN_GATE_URL="${PLAN_GATE_URL:-http://127.0.0.1:8089}"
export VLLM_URL="${VLLM_URL:-http://127.0.0.1:8000}"

# Only relevant if you start Plan-Gate or Python handlers **on this machine** (unusual on WSL).
export MOTADATA_EXPLAIN_VLLM_URL="${MOTADATA_EXPLAIN_VLLM_URL:-$VLLM_URL}"

export TOP_K="${TOP_K:-8}"

if [ -n "${1:-}" ]; then
  export QUERY="$1"
elif ! [ -n "${QUERY+x}" ]; then
  export QUERY="Which files implement topology anomaly scoring pipeline?"
fi
