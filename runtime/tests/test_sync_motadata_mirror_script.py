from __future__ import annotations

import subprocess
from pathlib import Path


def test_sync_motadata_mirror_to_gpu_script_shell_syntax() -> None:
    repo = Path(__file__).resolve().parents[2]
    script = repo / "runtime" / "scripts" / "sync_motadata_mirror_to_gpu.sh"
    proc = subprocess.run(
        ["bash", "-n", str(script)],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
