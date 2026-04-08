# Runtime config (m-coder)

**Topology:** one **distributed** setup — workspace-side **Context Layer** (WSL or native Linux); **Plan-Gate + vLLM** on the **GPU** host. Not separate deployment “profiles.” See **`docs/validation/B5_HOST_READINESS.md`** (Canonical Host Model).

| File | Purpose |
|------|---------|
| `demo_stack.env.example` | Copy to `demo_stack.env` for **`governed_services.sh`** (vLLM + Plan-Gate). Requires `VLLM_BASE_MODEL`. |
| `host_local.env.example` | Copy to `host_local.env` for **ports + URLs + `WORKSPACE_ROOT`** (Context Layer, plugin, validation sheet). |

Both `demo_stack.env` and `host_local.env` are gitignored.

**Quick start (HTTP validation without full GPU stack):**

1. `cp host_local.env.example host_local.env` and set `M_CODER_REPO_ROOT` to this repo’s absolute path.
2. `set -a && source host_local.env && set +a`
3. `../scripts/run_local_stack.sh start-context`
4. In another terminal, from repo root: `PLAN_GATE_PORT=8089 python3 -m runtime.plan_gate_service.app` (or use `governed_services.sh` when vLLM is configured).

See **`docs/validation/B5_HOST_READINESS.md`** for the full host-readiness audit.
