"""Tests for CI Backstop Gate v0.1."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
CI_EXAMPLES = REPO / "runtime" / "ci_gate" / "examples"


def run_ci_gate(
    input_path: Path,
    endpoint: str,
    mode: str = "shadow",
    fail_on: str = "REFUSAL,CONDITIONAL_BLOCK",
    fixed_time: str = "2026-03-01T00:00:00Z",
    strict: bool = True,
) -> tuple[int, str]:
    env = {**os.environ, "PYTHONPATH": str(REPO)}
    cmd = [
        "python3", "-m", "runtime.ci_gate.cli",
        "--input", str(input_path),
        "--endpoint", endpoint,
        "--mode", mode,
        "--fail-on", fail_on,
        "--fixed-time", fixed_time,
    ]
    if not strict:
        cmd.append("--no-strict")
    r = subprocess.run(cmd, cwd=str(REPO), env=env, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


class TestCIGate(unittest.TestCase):
    """Uses running Plan-Gate Service in background."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.mkdtemp()
        cls.spool = Path(cls.tmp) / "spool"
        env = {
            "PYTHONPATH": str(REPO),
            "PLAN_GATE_PORT": "0",
            "PLAN_GATE_SPOOL_DIR": str(cls.spool),
            "PLAN_GATE_MODE": "shadow",
            "PLAN_GATE_FIXED_TIME": "2026-03-01T00:00:00Z",
            "PLAN_GATE_DETERMINISTIC": "true",
        }
        cls.env = {**os.environ, **env}
        from runtime.plan_gate_service.app import run_server

        cls.server = run_server(port=0, spool_dir=cls.spool)
        cls.port = cls.server.server_address[1]
        cls.endpoint = f"http://127.0.0.1:{cls.port}/v0/plan"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.thread.join(timeout=2)

    def test_ci_gate_blocks_on_refusal(self) -> None:
        """Config change without evidence -> REFUSAL -> exit 1."""
        code, out = run_ci_gate(
            CI_EXAMPLES / "ci_input_config_change.json",
            self.endpoint,
        )
        self.assertEqual(code, 1, out)
        data = json.loads(out)
        self.assertEqual(data.get("decision"), "REFUSAL")

    def test_ci_gate_allows_bounding(self) -> None:
        """PR merge with evidence -> BOUNDING -> exit 0."""
        code, out = run_ci_gate(
            CI_EXAMPLES / "ci_input_pr_merge.json",
            self.endpoint,
        )
        self.assertEqual(code, 0, out)
        data = json.loads(out)
        self.assertEqual(data.get("decision"), "BOUNDING")

    def test_ci_gate_blocks_on_conditional_block(self) -> None:
        """When decision is CONDITIONAL_BLOCK, exit 1 (stub never produces it; mock response)."""
        ci = {"repo": "x", "action_type": "OTHER"}
        ci_path = Path(self.tmp) / "ci_cond.json"
        ci_path.write_text(json.dumps(ci))

        fake_body = json.dumps({
            "schema_version": "decision_response.v0.1",
            "request_id": "req-test",
            "decision": "CONDITIONAL_BLOCK",
        }).encode()

        class FakeResp:
            def read(self):
                return fake_body
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass

        def fake_urlopen(req, timeout=10):
            return FakeResp()

        with patch("runtime.ci_gate.cli.urlopen", fake_urlopen):
            import sys
            orig = sys.argv
            sys.argv = ["ci_gate", "--input", str(ci_path), "--endpoint", "http://x/v0/plan"]
            try:
                from runtime.ci_gate.cli import main
                code = main()
                self.assertEqual(code, 1)
            finally:
                sys.argv = orig

    def test_ci_gate_handles_service_unreachable(self) -> None:
        """When service is unreachable, strict mode -> exit 2."""
        code, out = run_ci_gate(
            CI_EXAMPLES / "ci_input_pr_merge.json",
            "http://127.0.0.1:19999/v0/plan",  # unreachable port
            strict=True,
        )
        self.assertEqual(code, 2, out)
