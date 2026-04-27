# mcoder-suite (single package)

Unified developer package for WSL/Linux:

- `mcoder` CLI (init/doctor/health/prompt/debug/plan/scenario)
- `motadata-context-layer` service

## Build wheel

```bash
cd packaging/mcoder-suite
python3 -m build --wheel -o dist
```

## Install

```bash
pip install dist/mcoder_suite-0.1.0-py3-none-any.whl
```

## Verify

```bash
mcoder version
motadata-context-layer --help
```

