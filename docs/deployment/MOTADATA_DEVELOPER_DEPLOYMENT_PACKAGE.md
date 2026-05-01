# Motadata developer deployment package

## Goal

A Motadata developer should install m-coder and use **Ask** and **Debug** in **under 20 minutes**, given:

- A Motadata workspace checkout (WSL path)
- Network reachability to **Plan-Gate** (direct or via SSH tunnel)
- A GPU operator who can keep **Plan-Gate + vLLM** alive on the governed path (or shared dev GPU)

This document is the **production-oriented** packaging and operations view. Design rationale and phased rollout notes remain in [`../design/MOTADATA_DEVELOPER_DEPLOYMENT_PACKAGE_V1.md`](../design/MOTADATA_DEVELOPER_DEPLOYMENT_PACKAGE_V1.md). Deep verification, Pass A/B/C, and graph/CIG drills live in [`../guides/MOTADATA_VERIFICATION_GUIDE.md`](../guides/MOTADATA_VERIFICATION_GUIDE.md). Wheel-only CLI posture is spelled out in [`../guides/MCODER_API_ONLY_DEVELOPER_SETUP.md`](../guides/MCODER_API_ONLY_DEVELOPER_SETUP.md).

---

## Audience and assumptions

- **Developer side:** Windows + WSL2, Python 3.10+, systemd user units optional but recommended for Context Layer.
- **Governance defaults:** Ask/Debug surfaces default to **plan-oriented** narration; execution paths outside this scope are intentionally not part of “first run.”
- **Golden rule:** IDEs and the developer CLI talk to **Context Layer** and **Plan-Gate** over HTTP contracts; **vLLM** is reached only via Plan-Gate.

---

## 1. Package contents

What a “distribution” bundle should expose to Motadata engineers (today: repo paths + artifact names; tomorrow: zipped release with the same layout).

| Category | What ships | Canonical location / notes |
|----------|-------------|----------------------------|
| **Unified wheel** | `mcoder-suite` (`mcoder` + `motadata-context-layer` entrypoints) | Build: `packaging/mcoder-suite/` — use `bash build_wheel.sh` so **`dist/mcoder_suite-latest-py3-none-any.whl`** is always the stable pip target (symlink). See [`../../packaging/mcoder-suite/README.md`](../../packaging/mcoder-suite/README.md). |
| **Config templates** | Project-first YAML + projected service env | `mcoder init` writes **`<Motadata>/.mcoder/config.yaml`** and **`context.env`**. Override discovery via **`MCODER_CONFIG_PATH`**. |
| **Bootstrap / stack scripts** | WSL orchestrator; GPU governed launcher; MVP stack helper | `scripts/mcoder_wsl_e2e_bootstrap.sh`, `scripts/wsl_plugin_mvp_stack.sh`, `runtime/scripts/governed_services.sh` (Plan-Gate + vLLM on GPU), `runtime/config/demo_stack.env.example` → **`demo_stack.env`**. |
| **Scenario lists** | Ask / Debug / Plan batch smoke inputs | `docs/validation/scenario_lists/ask_scenarios.txt`, `debug_scenarios.txt`, `plan_scenarios.txt`. |
| **Health / validation** | CLI gates + optional behavioral harness | **`mcoder health`**, **`mcoder doctor`**, **`mcoder bootstrap`**; fuller stack: **`motadata_behavior_verify`** / verification guide workflows. |

**Not required on the developer machine for API-only flow:** Full `m-coder` Git checkout (wheel + templates + scenarios can be copied from CI or internal artifact storage).

---

## 2. Architecture topology

Logical flow (contracts, not VPC diagrams):

```text
┌─────────────────────┐
│ Windows IDE / Shell │
└─────────┬───────────┘
          │ SSH into WSL (optional)
          ▼
┌─────────────────────────────────────────────┐
│ WSL — Motadata repo                         │
│  • Context Layer HTTP  :8091 (evidence)     │
│  • mcoder CLI           (client)            │
│  • ~/.mcoder/ or ./.mcoder/config.yaml       │
└─────────┬───────────────────────┬───────────┘
          │ export_evidence        │ POST /v1/ask (and relatives)
          ▼                         ▼
                    ┌───────────────────────────┐
                    │ GPU host — Plan-Gate :8089│
                    │  → vLLM (explain path)    │
                    └───────────────────────────┘
```

**Split topology (common):**

- **WSL:** Motadata checkout, Context Layer, `mcoder` — evidence is read from **`workspace_root`**.
- **GPU:** `governed_services.sh` wraps **Plan-Gate** bound to loopback **`127.0.0.1:8089`** and **vLLM** on **`8000`** by default (`runtime/config/demo_stack.env`).
- **Join:** Developer uses **`plan_gate_url: http://127.0.0.1:8089`** plus **`plan_gate_ssh_target`** so **`mcoder bootstrap`** can establish **`ssh -L`** when Plan-Gate is not directly reachable.

---

## 3. Installation flow (target: under 20 minutes)

Times are indicative for someone who already has GPU services running and SSH keys configured.

### 3.1 One-time machine prep (≈ 5–10 min)

1. **Python venv** beside Motadata (recommended):

```bash
cd /path/to/Motadata
mkdir -p .mcoder
python3 -m venv .mcoder/venv
source .mcoder/venv/bin/activate
pip install -U pip
```

2. **Install wheel** — prefer the stable name after build or **`rsync`/`scp -L`** of `mcoder_suite-latest-py3-none-any.whl`:

```bash
pip install --no-deps --force-reinstall /path/to/mcoder_suite-latest-py3-none-any.whl
mcoder version
```

3. **Initialize config** — set real paths and URLs:

```bash
mcoder init \
  --workspace-root /path/to/Motadata \
  --plan-gate-url http://127.0.0.1:8089 \
  --plan-gate-ssh user@gpu-host.example \
  --force
```

If Plan-Gate is directly reachable from WSL, use its URL and omit SSH metadata; see [`../guides/MCODER_API_ONLY_DEVELOPER_SETUP.md`](../guides/MCODER_API_ONLY_DEVELOPER_SETUP.md) § WSL / tunnel.

4. **Context Layer as a service (recommended):** install a **user** `systemd` unit that loads **`.mcoder/context.env`** and runs **`motadata-context-layer`**. Template and steps: same API-only guide, § Context Layer User Service.

### 3.2 GPU / shared stack (operator or advance setup, ≈ 5–15 min if cold)

On the machine that hosts Plan-Gate + vLLM:

```bash
cd /path/to/m-coder
cp runtime/config/demo_stack.env.example runtime/config/demo_stack.env
# Set VLLM_BASE_MODEL, ASK_DEFAULT_REPO_ROOT, etc.
./runtime/scripts/governed_services.sh restart
./runtime/scripts/governed_services.sh status
```

Plan-Gate **Ask narration flags** (e.g. synthesis) must be set **before** the Plan-Gate process starts — export them in **`demo_stack.env`** or the launcher environment, not only in an interactive shell (see comments in `demo_stack.env.example`).

### 3.3 Validate endpoints (≈ 2–3 min)

From WSL, with venv active:

```bash
mcoder health
mcoder doctor
mcoder bootstrap
```

If **`plan_gate_url`** is loopback and the tunnel is down, **`mcoder bootstrap`** should attempt SSH port-forwarding when **`plan_gate_ssh_target`** is configured (see CLI hints and [`../guides/MCODER_API_ONLY_DEVELOPER_SETUP.md`](../guides/MCODER_API_ONLY_DEVELOPER_SETUP.md) § stack check / watch).

---

## 4. First-run flow

After §3 succeeds:

| Step | Command | Success signal |
|------|---------|----------------|
| 1 | `mcoder bootstrap` (or `--check-only` for read-only) | Context + Plan-Gate checks green; tunnel up if required |
| 2 | `mcoder prompt "How does alert correlation work in this repo?"` | Non-error response; evidence-backed answer shape |
| 3 | `mcoder scenario --type ask --file docs/validation/scenario_lists/ask_scenarios.txt` | Batch completes; failures point to config or service |
| 4 | `mcoder scenario --type debug --file docs/validation/scenario_lists/debug_scenarios.txt` | Batch completes; missing-file cases refuse cleanly |

**Optional deeper validation:** `motadata_behavior_verify` and production-style scenarios — see [`../guides/MOTADATA_VERIFICATION_GUIDE.md`](../guides/MOTADATA_VERIFICATION_GUIDE.md).

---

## 5. Troubleshooting

### 5.1 SSH tunnel issues

| Symptom | Likely cause | What to do |
|---------|----------------|------------|
| `Connection refused` to `127.0.0.1:8089` | Tunnel not established; GPU binds Plan-Gate to loopback only | Run **`mcoder bootstrap`**; ensure **`plan_gate_ssh_target`** and **BatchMode** SSH keys work. Manual: see verification guide §3.3 SSH tunnel from WSL. |
| Tunnel dies after idle | SSH/TCP timeouts | Use **`mcoder stack watch --auto-tunnel`** or systemd-wrapped reconnect policy; widen server `ClientAlive` settings where you control SSH. |

### 5.2 Health failures

| Symptom | Likely cause | What to do |
|---------|----------------|------------|
| Context Layer **`/healthz`** fails | Service not running; wrong port; **`context.env`** paths | **`systemctl --user status mcoder-context`** (or start script); verify **`8091`** and **`workspace_root`** in config. |
| Plan-Gate **`/healthz`** fails | GPU stack down; wrong URL; tunnel missing | **`governed_services.sh status`** on GPU; curl loopback on GPU vs tunneled URL on WSL. |

### 5.3 Stale Plan-Gate / “wrong schema” behavior

| Symptom | Likely cause | What to do |
|---------|----------------|------------|
| Plan-Gate **`/version`** mismatch with CLI contracts | Wheel and GPU revision drift | Align Git SHA across wheel install and **`governed_services`** rebuild; reinstall wheel; **`governed_services.sh restart`**. Verification guide warns on schema mismatch similarly. |

### 5.4 Missing or stale authority / graph cache (WSL indexer)

| Symptom | Likely cause | What to do |
|---------|----------------|------------|
| Thin evidence bundles; recurring “insufficient chain” narration | Authority index not built or outdated | **`mcoder bootstrap --verify-authority-index`**; run **`scripts/mcoder_wsl_e2e_bootstrap.sh`** without **`--skip-authority-index`**; for graph/CIG-heavy flows see verification guide **Pass B** sections. |

### 5.5 Config and venv hygiene

| Symptom | Likely cause | What to do |
|---------|----------------|------------|
| `pip` warns install is **outside** project venv | **`PYTHONPATH`**, stray **`.pth`**, editable install bleed | Follow **“Venv hygiene”** in [`../guides/MCODER_API_ONLY_DEVELOPER_SETUP.md`](../guides/MCODER_API_ONLY_DEVELOPER_SETUP.md). |

---

## 6. Upgrade / update workflow

**Developer wheel update (API-only machines):**

```bash
cd /path/to/Motadata
source .mcoder/venv/bin/activate
pip install --no-deps --force-reinstall /path/to/mcoder_suite-latest-py3-none-any.whl
mcoder version
mcoder doctor
mcoder bootstrap
```

**GPU stack update (operators with m-coder checkout):**

```bash
cd /path/to/m-coder
git pull --ff-only   # or your release process
./runtime/scripts/governed_services.sh restart
```

**WSL “full dev” refresh (optional orchestrator):**

```bash
bash scripts/mcoder_wsl_e2e_bootstrap.sh \
  --repo-root /path/to/m-coder \
  --motadata-root /path/to/Motadata \
  --branch <expected-branch>
```

Logs default under **`runtime/.run/mcoder_wsl_e2e_bootstrap_<UTC>.log`** (see script header).

**After Motadata codebase changes:** restart Context Layer (or reload service) so evidence export reflects current files; **`MOTADATA_CONTEXT_LAYER_ALLOW_DIRTY_CACHE=1`** trades safety for speed (dev-only).

---

## 7. Minimal one-command installer opportunities

| Approach | Status | Notes |
|---------|--------|--------|
| **`mcoder init` + documented venv + wheel pip** | Implemented | Baseline zero-installer flow; aligns with [<20 min] if artifacts are cached. |
| **`mcoder bootstrap`** as session multiplexer | Implemented | Covers health, optional tunnel, and checklist output. |
| **`scripts/mcoder_wsl_e2e_bootstrap.sh`** | Implemented | Opinionated repo + Motadata orchestration for developers who **do** keep an m-coder clone on WSL. |
| **`scripts/wsl_plugin_mvp_stack.sh`** | Implemented helper | Brings MVP Context Layer (+ optional tunnel knobs); pair with GPU **`governed_services`**. |
| **Single downloadable `.tar.gz` / internal PyPI** | Future | Ship: wheel, scenario lists, **`config.yaml.example`**, **`context.env.example`**, **`install.sh`** wrapping venv + `pip` + **`mcoder init`**. |
| **Windows `.msi` / WinGet** | Future | Thin wrapper around “open WSL, run install.sh”; highest polish, not required for v1 ROI. |

**Suggested future `install.sh` contract** (illustrative, not shipped):

```text
install.sh [--wheel-url URL] [--motadata-root PATH]
  → create .mcoder/venv
  → pip install mcoder_suite-latest-py3-none-any.whl
  → mcoder init --workspace-root … --plan-gate-url … [--plan-gate-ssh …]
  → print: systemctl instructions + mcoder bootstrap
```

---

## Quick reference checklist

- [ ] `mcoder_suite-latest-py3-none-any.whl` installed in **project venv**
- [ ] `<Motadata>/.mcoder/config.yaml`: **`workspace_root`**, **`context_url`**, **`plan_gate_url`**, optional **`plan_gate_ssh_target`**
- [ ] Context Layer healthy on **`8091`**
- [ ] Plan-Gate reachable (direct or tunnel) on **`8089`**
- [ ] GPU: **`demo_stack.env`** complete; **`governed_services.sh status`** OK
- [ ] **`mcoder bootstrap`** then **`mcoder prompt`** then **`mcoder scenario`** (ask + debug lists)

Once this checklist passes for a cohort, treating **Ask** and **Debug** as **frozen** interfaces for the slice is justified; remaining work shifts to packaging polish and operational velocity — not reasoning architecture rework.
