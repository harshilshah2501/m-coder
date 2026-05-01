# mcoder-suite (single package)

Unified developer package for WSL/Linux:

- `mcoder` CLI (init/doctor/health/prompt/debug/plan/scenario)
- `motadata-context-layer` service

## Build wheel

Setuptools-scm produces **long**, unique wheel filenames (`mcoder_suite-<version>-py3-none-any.whl`). Use the scripted build so **`dist/` always has a stable name** plus optional pruning of older wheels:

```bash
cd packaging/mcoder-suite
pip install build   # once, in your venv
bash build_wheel.sh
```

`build_wheel.sh` runs `python3 -m build --wheel -o dist`, keeps the **newest N** concrete wheels (`MCODER_SUITE_WHEEL_KEEP`, default **1**), and updates:

- `dist/mcoder_suite-latest-py3-none-any.whl` → symlink to that newest wheel (relative symlink, safe across `rsync`).

Refresh only the symlink / prune layout in an existing folder (typical **on WSL** after copying wheels):

```bash
bash packaging/mcoder-suite/link_mcoder_suite_latest.sh [--keep N] [--no-prune] ~/motadata-wheel
```

## Install

**Stable path** (recommended on WSL after build or rsync/scp):

```bash
pip install --force-reinstall dist/mcoder_suite-latest-py3-none-any.whl
```

If you omitted the scripted layout, install the concrete file under `dist/` by name instead.

Copy to WSL: prefer **`rsync -av`** of the whole `dist/` directory so the symlink stays valid; or copy the concrete `.whl` plus run `link_mcoder_suite_latest.sh` on WSL.

**scp:** OpenSSH `-L` follows symlinks when copying — you can ship the stable-name file as ordinary wheel bytes:

```bash
scp -L user@gpu:~/Harshil-PoCs/m-coder/packaging/mcoder-suite/dist/mcoder_suite-latest-py3-none-any.whl ~/motadata-wheel/
```

## Verify

```bash
mcoder version
motadata-context-layer --help
```

