# Governed services (vLLM + Plan-Gate)

**Single entry point:** `runtime/scripts/governed_services.sh`

| Command | Action |
|---------|--------|
| `./runtime/scripts/governed_services.sh start` | Start vLLM then Plan-Gate (needs `runtime/config/demo_stack.env` with **`VLLM_BASE_MODEL`**) |
| `./runtime/scripts/governed_services.sh stop` | Stop Plan-Gate then vLLM; clears stray listeners on the service ports (`fuser` on Linux when available) |
| `./runtime/scripts/governed_services.sh restart` | Clean **stop → port cleanup → start** (no leaked processes on 8089/8000) |
| `./runtime/scripts/governed_services.sh status` | Pid files + HTTP checks |

**Config:** `runtime/config/demo_stack.env` (copy from `demo_stack.env.example`).

**Optional:** For boot automation, add your **own** systemd unit that runs `governed_services.sh start` / `stop` — there is **no** checked-in `motadata-orchestrator.service` in this repo anymore.

**Manual / debug:** `runtime/scripts/start_explain_vllm.sh` can still be used to bring up vLLM only; then start Plan-Gate by hand — see [MOTADATA_DEMO_SETUP_RUNBOOK.md](../MOTADATA_DEMO_SETUP_RUNBOOK.md) §11 (alternative manual vLLM + Plan-Gate).

The **legacy** FastAPI RAG stack (Qdrant, optional graph DB in archived compose, `rag_api.py`) lives under **`archive/legacy_runtime_rag/`** (retired from `runtime/rag/`). It is **not** started by `governed_services.sh` and is **not** the canonical Plan-Gate slice.
