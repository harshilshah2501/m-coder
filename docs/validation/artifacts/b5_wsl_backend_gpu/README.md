# B5 — workspace backend on WSL + GPU governed stack

**Status on 2026-04-08:** **Not executed** on the proof host (environment was **native Linux**). This folder is the **operator prerequisite + failure-proof** for a **WSL-based workspace backend**, not a green run transcript.

## Prerequisite checklist (PASS / FAIL)

| Check | PASS when |
|-------|-----------|
| WSL2 distro running | `WSL_DISTRO_NAME` set **inside WSL**, repo on Linux FS |
| Context Layer | `curl -sf http://127.0.0.1:8091/healthz` from **WSL** |
| GPU path reachable | From WSL: tunnel or direct URL to Plan-Gate **8089** + vLLM **8000** on GPU host |
| Same validation | Mirror `docs/validation/artifacts/b5_linux_backend_gpu/` steps (health → export → `/v0/ask`) |

## Exact startup path (reference)

1. **GPU server:** `runtime/scripts/governed_services.sh start` (needs `runtime/config/demo_stack.env` + `VLLM_BASE_MODEL`), or equivalent Plan-Gate + vLLM processes.
2. **WSL:** from repo root, `python3 -m runtime.context_layer_service` (or `runtime/scripts/run_local_stack.sh start-context`).
3. **Windows IDE:** SSH local forward **8089** and **8000** to GPU; Context Layer stays **8091** on WSL (`MOTADATA_CONTEXT_LAYER_URL`).

## Failure-proof

If Plan-Gate or vLLM is **unreachable** from WSL → **STOP**. Classify as **connectivity / SSH tunnel / firewall / wrong URL**, not application logic. Blocks **WSL workspace-backend** proof until network path is fixed.
