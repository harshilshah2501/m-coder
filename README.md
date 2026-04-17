# m-coder — Motadata AI Coding Assistant

This repository holds the **Motadata AI Coding Assistant** (governed runtime, ML compilation, validation) alongside **operator-oriented** material (for example optional host backup tooling and systemd service notes further below). **Program closure and per-layer status** are maintained in [`docs/LIVE_ROADMAP_TRACKER.md`](docs/LIVE_ROADMAP_TRACKER.md); if anything in this file disagrees with the tracker, **trust the tracker**.

## Status

This repository contains a **production-grade validated vertical slice** of the Motadata AI Coding Assistant.

### What is proven

- Retrieval correctness and generalization closure (B1)
- Plugin truthfulness closure for MVP scope (B3)
- Observability and trace reconstruction closure (B4)
- Host reproducibility on WSL and native Linux backend placements (B5)
- Stage 3 burn-in closure (B7)
- Final acceptance run PASS (Action 14)

### What is not yet included

- **Stage 2.5 proactive / influence-enabled** Assist in production (Assist Layer v1 is **implemented** and **advisory-only**; see `docs/LIVE_ROADMAP_TRACKER.md` §1 and §1.5)
- Background sync
- Active-file UX improvements

### Primary evidence

- Action 14 final acceptance: `docs/validation/artifacts/action14_final_acceptance/ACTION14_FINAL_ACCEPTANCE_REPORT.md`
- Live canonical program state: `docs/LIVE_ROADMAP_TRACKER.md`
- B5 host readiness closure: `docs/validation/B5_HOST_READINESS.md`
- Stage 3 burn-in closure: `docs/validation/STAGE3_BURN_IN_REPORT.md`
- MVP validation rollup: `docs/validation/AIOPS_MVP_FINAL_REPORT_TEMPLATE.md`

Production-ready AI services deployment with version-agnostic model naming and systemd service management.

## Current System Status (4-layer core + Layer-5 product extension)

The **four constitutional layers** (L1–L4) are the doctrine and enforcement core. **Layer-5** is **workspace intelligence** (Context Layer, evidence bundles, retrieval, optional Assist advisory) — a **product extension** that feeds Plan-Gate; it does not replace Layer-3 authority. See `docs/ARCHITECTURE_4_LAYER.md` and `docs/PRODUCT_SLICE.md`.

- **Layer-1 — Governance (Constitution)**: **LOCKED**  
  - Constitutional manifest, phase doctrine (REF, CONF, DES, MIX, CODE, REACH), dominance rules, and golden exemplar governance are ratified and immutable without GREG. See `docs/MASTER_SYSTEM_SPEC.md` and `governance/CONSTITUTIONAL_MANIFEST_v1.0.md`.
- **Layer-2 — ML Compilation (Stages 1–8)**: **LOCKED**  
  - Base→variants→Stage-6 mutation→freeze→SFT pipeline is closed. Stage-6C agent-loop mutation harness PASS, deterministic dataset freeze, SFT training and post-SFT revalidation PASS. See `docs/LIVE_ROADMAP_TRACKER.md` §2.1.1, §4.2.1, §4.2.2, §6.1, `ml/artifacts/LAYER2_RELEASE_VERIFICATION.json`, and `ml/training/FREEZE_CERTIFICATE_v1.json`.
- **Layer-3 — Runtime Enforcement / Execution**: **COMPLETE** (M3.0–M3.12 on `main`)  
  - Core runtime milestones **M3.0–M3.11** and **M3.12** (narrow doc manifest + `doc_selector`) are **complete on `main`** — see `docs/LIVE_ROADMAP_TRACKER.md` §6.16.1. Follow-on (**M3.13+**) is tracked in the same file. **Governed execute** (`POST /v0/execute`) is validated for the closed MVP slice; Stage 3 controlled-loop burn-in is closed (**B7**). Canonical numbering is **M3.0–M3.18** in the tracker (do not use legacy labels such as M3.E0 in place of the M3.x table). See `docs/LAYER3_RUNTIME_SPEC.md`, `docs/runtime/RUNTIME_STATE_TRANSITIONS.md`, and `docs/LIVE_ROADMAP_TRACKER.md` (§1, §4.3, §6.20).
- **Layer-4 — Observation / Drift Detection**: **COMPLETE** (M4.1–M4.6 + Track-C on `main`)  
  - **M4.1–M4.6** merged on `main` (see tracker §1 and merge report referenced there). Ongoing observation product work, if any, is tracked in `docs/LIVE_ROADMAP_TRACKER.md` and `observation/README.md`; do not infer “Layer-4 partial” from older summaries without checking the tracker.
- **Layer-5 — Workspace intelligence (product extension)**: **CLOSED** (MVP slice) — waves, evidence bundle, Context Layer packaging, and grounded-Ask harness scope per `docs/LIVE_ROADMAP_TRACKER.md` §1 / §4.5.  
  - Primary paths: `runtime/context_layer_service/`, `runtime/layer5/`, `packaging/motadata-context-layer/`, `runtime/assist_layer/` (Assist is **advisory-only**). Not a substitute for Plan-Gate / Layer-3 governance.

### Roadmaps & Governance Navigation

- **Sole canonical architecture entry (doctrine + spec navigation):** `docs/MASTER_SYSTEM_SPEC.md` (includes **Hierarchy of truth**; overrides narrative-only guides for binding behavior)
- **4-layer core + Layer-5 mapping & axes**: `docs/ARCHITECTURE_4_LAYER.md`
- **Layer-5 / product slice (scope, validation stance)**: `docs/PRODUCT_SLICE.md`
- **Layer-2 ML Compilation spec**: `docs/LAYER2_COMPILATION_SPEC.md`
- **Layer-3 Runtime spec**: `docs/LAYER3_RUNTIME_SPEC.md`
- **Execution roadmaps**:
  - Live execution tracker: `docs/LIVE_ROADMAP_TRACKER.md` (single source of truth for Layer statuses and evidence)
  - End-to-end execution view: `docs/SYSTEM_EXECUTION_ROADMAP.md`
  - Archived (historical): `docs/archive/ROADMAP_L2_L3_L4.md` — entry/exit/failure tables; do not use for current status
- **Master System Guide v1.7** (`MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md`): long-form narrative, demos, Appendix H — **supporting**; **canonical spec entry and gates:** `docs/MASTER_SYSTEM_SPEC.md` + `docs/LIVE_ROADMAP_TRACKER.md`

## 🚀 Quick Start

### Start Services (Current Flow)
```bash
bash runtime/scripts/governed_services.sh start
```

### Check Status
```bash
bash runtime/scripts/governed_services.sh status
```

### View Logs
```bash
bash runtime/scripts/governed_services.sh logs
```

For more details, see [docs/guides/ORCHESTRATOR_SERVICE_GUIDE.md](docs/guides/ORCHESTRATOR_SERVICE_GUIDE.md) and [docs/guides/ORCHESTRATOR_GUIDE.md](docs/guides/ORCHESTRATOR_GUIDE.md).

---

## Architecture overview (4-layer core + Layer-5)

The **constitutional** structure is four layers (Governance, ML Compilation, Runtime, Observation). **Layer-5** adds **workspace intelligence** (indexing, `layer5.evidence_bundle.v1`, Context Layer) and optional **Assist** — see **[docs/ARCHITECTURE_4_LAYER.md](docs/ARCHITECTURE_4_LAYER.md)** and **[docs/MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md](docs/MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md)**.

- **[docs/ARCHITECTURE_4_LAYER.md](docs/ARCHITECTURE_4_LAYER.md)** — Directory philosophy, L1–L5 boundaries, axis separation
- **[docs/PRODUCT_SLICE.md](docs/PRODUCT_SLICE.md)** — What is in scope for the current product slice (includes Layer-5 HTTP path)
- **[docs/archive/ROADMAP_L2_L3_L4.md](docs/archive/ROADMAP_L2_L3_L4.md)** — archived L2/L3/L4 entry/exit tables (use **`docs/LIVE_ROADMAP_TRACKER.md`** for live milestones)
- **[docs/architecture/Golden_Exemplars_Architecture_Map.md](docs/architecture/Golden_Exemplars_Architecture_Map.md)** — Golden Exemplars system map
- **[observation/README.md](observation/README.md)** — Layer-4 (Observation) boundaries

The system uses hybrid control: **policy-governed rendering** for REF and CONF (final outputs are policy-rendered and policy-scored), and **model-expressive generation** for DES and CODE. This doctrine was adopted after CONF→DES drift remained unresolved under SFT-only attempts; deterministic CONF runtime rendering achieved the cure.

---

## Model/Dataset artifact storage (DVC + Local Disk)

Prototype/evaluation stage: Git stores only source, config, and DVC pointer files. Large artifacts are tracked by **DVC** and stored on **local disk**. No cloud credentials required. R2 deferred for later.

- **[docs/DVC_ARTIFACTS_README.md](docs/DVC_ARTIFACTS_README.md)** — Setup and end-to-end usage
- **[ml/artifacts/REGISTRY.md](ml/artifacts/REGISTRY.md)** — Artifact contracts and naming

```bash
./scripts/setup_dvc_local.sh
make dvc-pull-checkpoints RUN_ID=<run_id>
make dvc-pull-dataset FREEZE_ID=<freeze_id>
```

---

## Host backup (optional tooling)

Automated backup of a remote GPU host using Unison sync (legacy operator scripts; paths and script names may still contain older `h100` prefixes on disk).

## 📋 Quick Start

```bash
# Run backup manually
./backup-gpu-host.sh

# View what will be backed up
./verify-backup-contents.sh

# Check backup logs
ls -lt logs/ | head -5
```

## 📊 Backup Summary

- **Source:** `harshil@152.228.213.249:/home/harshil/Harshil-PoCs`
- **Destination (example):** `/root/gpu-host-backups`
- **Backup Size:** ~49 GB (optimized from 75 GB)
- **Space Saved:** ~25 GB by excluding virtual environments
- **Sync Type:** One-way (Remote → Local)

## ✅ What's Backed Up

| Category | Size | Examples |
|----------|------|----------|
| **Finetuned Models** | ~44 GB | `*.safetensors`, model checkpoints |
| **Configuration** | ~10 MB | `config.json`, `requirements.txt`, `*.yaml` |
| **Documentation** | ~5 MB | `README.md`, `*.md` files |
| **Source Code** | ~50 MB | `*.py`, `*.sh`, `*.ipynb` |
| **Data Files** | ~1 GB | `*.jsonl`, `*.json`, `*.csv` |

### Important Files Included:
- ✅ All finetuned models in `model-backups/`
- ✅ All training checkpoints in `Finetuning-Iter*/`
- ✅ Latest models in `motadata-coder-iter9/`
- ✅ All configuration and requirements files
- ✅ All documentation and README files
- ✅ All source code and scripts

## ❌ What's Excluded

| Category | Size Saved | Reason |
|----------|------------|--------|
| **Virtual Environments** | ~25 GB | Recreatable from requirements.txt |
| **Python Cache** | ~500 MB | Auto-generated |
| **Build Artifacts** | ~100 MB | Regeneratable |
| **IDE Files** | ~10 MB | Personal settings |
| **Logs** | ~50 MB | Temporary data |

## 📚 Documentation

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Common commands and quick help
- **[BACKUP_SETUP_GUIDE.md](BACKUP_SETUP_GUIDE.md)** - Complete setup instructions
- **[BACKUP_CONTENTS.md](BACKUP_CONTENTS.md)** - Detailed list of backed up files

## 🚀 Setup Periodic Backups

### Option 1: Cron (Recommended for simplicity)

```bash
crontab -e
# Add this line for backups every 6 hours:
0 */6 * * * /root/gpu-host-backups/backup-gpu-host.sh
```

### Option 2: Systemd (Recommended for advanced users)

```bash
sudo cp systemd/*.service systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gpu-host-backup.timer
```

See [systemd/README.md](systemd/README.md) for details.

## 🔧 Configuration

**Unison Profile (example):** `~/.unison/gpu-host-backup.prf`

Key settings:
- One-way sync (remote always wins)
- Automatic conflict resolution
- Excludes virtual environments and cache
- Includes all models and configurations

## 📝 Logs

Backup logs are stored in `logs/` directory:
- Timestamped log for each backup run
- Automatically cleaned up after 30 days
- Unison detailed log (example): `~/.unison/gpu-host-backup.log`

## ⚠️ Important Notes

1. **One-way sync:** Changes on local machine will be overwritten
2. **First sync:** Takes 1-2 hours to copy all files
3. **Subsequent syncs:** Only transfer changed files (much faster)
4. **Virtual environments:** Not backed up - recreate from requirements.txt
5. **Models:** All finetuned models ARE backed up

## 🛠️ Troubleshooting

### Backup is slow
- First sync copies everything (~49 GB)
- Later syncs only copy changes
- Virtual environments excluded to save time

### Connection issues
```bash
# Test SSH connection
ssh harshil@152.228.213.249 "echo 'OK'"
```

### Version mismatch
```bash
# Check Unison versions match
unison -version
ssh harshil@152.228.213.249 "unison -version"
```

See [BACKUP_SETUP_GUIDE.md](BACKUP_SETUP_GUIDE.md) for more troubleshooting.

## 📦 Files in This Directory

```
gpu-host-backups/
├── README.md                      # This file
├── QUICK_REFERENCE.md             # Quick command reference
├── BACKUP_SETUP_GUIDE.md          # Complete setup guide
├── BACKUP_CONTENTS.md             # Detailed backup contents
├── backup-gpu-host.sh             # Main backup script (rename if your tree differs)
├── verify-backup-contents.sh      # Verification script
├── logs/                          # Backup logs (auto-cleaned)
├── systemd/                       # Systemd service files
│   ├── gpu-host-backup.service
│   ├── gpu-host-backup.timer
│   └── README.md
└── [synced data from remote host] # Your backed up files
```

## 🎯 Next Steps

1. ✅ Unison profile configured with smart exclusions
2. ✅ Backup script created
3. ✅ Documentation complete
4. ⏳ **TODO:** Set up periodic backups (cron or systemd)
5. ⏳ **TODO:** Run first backup: `./backup-gpu-host.sh`

## 💡 Tips

- Run `./verify-backup-contents.sh` to see what will be backed up
- Check `logs/` directory for backup history
- First backup takes time - be patient!
- Subsequent backups are much faster
- Virtual environments can be recreated: `pip install -r requirements.txt`

---

**Need Help?** See [BACKUP_SETUP_GUIDE.md](BACKUP_SETUP_GUIDE.md) or [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

