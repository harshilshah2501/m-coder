from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_repo_cli():
    repo_root = Path(__file__).resolve().parents[6]
    cli_path = repo_root / "ml" / "training" / "artifacts" / "cli.py"
    spec = importlib.util.spec_from_file_location("m_coder_artifacts_cli", cli_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load artifact CLI from {cli_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    module = _load_repo_cli()
    if argv is None:
        return int(module.main())
    return int(module.main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
