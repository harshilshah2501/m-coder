"""Integration tests for plan-gate service v0.1."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
STUB_EXAMPLES = REPO / "runtime" / "plan_gate_stub" / "examples"
STUB_GOLDEN_PR = REPO / "runtime" / "plan_gate_stub" / "golden_outputs" / "pr_merge_shadow"
STUB_GOLDEN_CFG = REPO / "runtime" / "plan_gate_stub" / "golden_outputs" / "config_change_shadow"
INGEST_GOLDEN = REPO / "observation" / "ingest" / "golden_reports"


def post_plan(url: str, plan_request: dict) -> tuple[int, dict]:
    data = json.dumps(plan_request).encode("utf-8")
    req = Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    with urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())


def post_plan_expect_error(url: str, plan_request: dict) -> tuple[int, dict | None]:
    data = json.dumps(plan_request).encode("utf-8")
    req = Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except HTTPError as e:
        body = e.read().decode() if e.fp else "{}"
        return e.code, json.loads(body) if body.strip() else None


class TestPlanGateService(unittest.TestCase):
    """Start service on ephemeral port, run tests, shutdown."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.mkdtemp()
        cls.spool = Path(cls.tmp) / "spool"
        env = {
            "PYTHONPATH": str(REPO),
            "PLAN_GATE_PORT": "0",  # ephemeral
            "PLAN_GATE_SPOOL_DIR": str(cls.spool),
            "PLAN_GATE_MODE": "shadow",
            "PLAN_GATE_FIXED_TIME": "2026-03-01T00:00:00Z",
            "PLAN_GATE_DETERMINISTIC": "true",
        }
        cls.env = {**os.environ, **env}
        from runtime.plan_gate_service.app import run_server

        cls.server = run_server(port=0, spool_dir=cls.spool)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.thread.join(timeout=2)

    def test_post_plan_returns_valid_decision_response(self) -> None:
        req = json.loads((STUB_EXAMPLES / "input_plan_request_pr_merge_shadow.json").read_text())
        status, resp = post_plan(f"{self.base_url}/v0/plan", req)
        self.assertEqual(status, 200)
        self.assertEqual(resp.get("schema_version"), "decision_response.v0.1")

        from runtime.plan_gate_stub.validate import validate_ide_rules

        errs = validate_ide_rules(resp)
        self.assertEqual(errs, [], f"IDE rule violations: {errs}")

    def test_service_emits_artifacts_schema_valid(self) -> None:
        req = json.loads((STUB_EXAMPLES / "input_plan_request_pr_merge_shadow.json").read_text())
        post_plan(f"{self.base_url}/v0/plan", req)

        outdir = self.spool / "2026-03-01T00:00:00Z" / "req-pr-merge-shadow"
        self.assertTrue(outdir.exists(), f"Spool dir not found: {outdir}")

        plan = json.loads((outdir / "plan.json").read_text())
        decision = json.loads((outdir / "decision_response.json").read_text())
        ledger = json.loads((outdir / "ledger_row.json").read_text())
        shadow = json.loads((outdir / "shadow_run_record.json").read_text())
        ingestion = json.loads((outdir / "ingestion_batch.json").read_text())

        from runtime.plan_gate_stub.validate import validate_schemas

        errs = validate_schemas(plan, decision, ledger, shadow, ingestion)
        self.assertEqual(errs, [], f"Schema errors: {errs}")

    def test_service_outputs_deterministic_matches_stub_golden(self) -> None:
        """Compare via observation ingest report equivalence (spool path differs)."""
        for example_path in [
            STUB_EXAMPLES / "input_plan_request_pr_merge_shadow.json",
            STUB_EXAMPLES / "input_plan_request_config_change_shadow.json",
        ]:
            req = json.loads(example_path.read_text())
            post_plan(f"{self.base_url}/v0/plan", req)

        for batch_rel, golden_report in [
            ("req-pr-merge-shadow", INGEST_GOLDEN / "pr_merge_report.json"),
            ("req-config-change-shadow", INGEST_GOLDEN / "config_change_report.json"),
        ]:
            batch_path = self.spool / "2026-03-01T00:00:00Z" / batch_rel / "ingestion_batch.json"
            out_report = Path(self.tmp) / batch_rel
            out_report.mkdir(parents=True, exist_ok=True)

            r = subprocess.run(
                [
                    "python3", "-m", "observation.ingest.cli",
                    "--input", str(batch_path),
                    "--outdir", str(out_report),
                    "--fixed-time", "2026-03-01T00:00:00Z",
                ],
                cwd=str(REPO),
                env={**os.environ, "PYTHONPATH": str(REPO)},
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)

            gen = json.loads((out_report / "report.json").read_text())
            golden = json.loads(golden_report.read_text())
            self.assertEqual(gen["counts"], golden["counts"], f"counts differ for {batch_rel}")
            self.assertEqual(gen["integrity"]["mismatches_count"], golden["integrity"]["mismatches_count"])

    def test_shadow_never_crosses_boundary(self) -> None:
        req = json.loads((STUB_EXAMPLES / "input_plan_request_pr_merge_shadow.json").read_text())
        post_plan(f"{self.base_url}/v0/plan", req)
        req2 = json.loads((STUB_EXAMPLES / "input_plan_request_config_change_shadow.json").read_text())
        post_plan(f"{self.base_url}/v0/plan", req2)

        for req_id in ["req-pr-merge-shadow", "req-config-change-shadow"]:
            outdir = self.spool / "2026-03-01T00:00:00Z" / req_id
            ledger = json.loads((outdir / "ledger_row.json").read_text())
            shadow = json.loads((outdir / "shadow_run_record.json").read_text())

            self.assertNotEqual(ledger["verdicts"]["boundary_verdict"], "crossed")
            self.assertFalse(ledger["boundary"]["boundary_crossed"])
            self.assertNotEqual(shadow["boundary_verdict"], "crossed")

            from runtime.plan_gate_stub.validate import validate_shadow_rules

            errs = validate_shadow_rules(shadow)
            self.assertEqual(errs, [], f"Shadow rule violations: {errs}")

    def test_invalid_request_returns_400(self) -> None:
        bad = {"schema_version": "plan_request.v0.1"}  # missing required fields
        status, _ = post_plan_expect_error(f"{self.base_url}/v0/plan", bad)
        self.assertEqual(status, 400)

    def test_healthz_returns_ok(self) -> None:
        req = Request(f"{self.base_url}/healthz", method="GET")
        with urlopen(req) as resp:
            data = json.loads(resp.read().decode())
        self.assertEqual(resp.status, 200)
        self.assertEqual(data.get("status"), "ok")

    def test_version_returns_supported_schemas(self) -> None:
        req = Request(f"{self.base_url}/version", method="GET")
        with urlopen(req) as resp:
            data = json.loads(resp.read().decode())
        self.assertEqual(resp.status, 200)
        self.assertEqual(data.get("service_version"), "v0.1")
        schemas = data.get("supported_schemas", {})
        self.assertEqual(schemas.get("plan_request"), "v0.1")
        self.assertEqual(schemas.get("decision_response"), "v0.1")

    def test_service_artifacts_byte_match_stub_when_normalized(self) -> None:
        """Artifacts match stub golden byte-for-byte (no spool path in JSON)."""
        # Stub golden was generated with lineage_index unavailable; patch to match
        with patch("runtime.plan_gate_stub.rules.load_lineage_index", return_value=None):
            for example_path, req_id in [
                (STUB_EXAMPLES / "input_plan_request_pr_merge_shadow.json", "req-pr-merge-shadow"),
                (STUB_EXAMPLES / "input_plan_request_config_change_shadow.json", "req-config-change-shadow"),
            ]:
                req = json.loads(example_path.read_text())
                post_plan(f"{self.base_url}/v0/plan", req)

                golden_dir = STUB_GOLDEN_PR if "pr_merge" in str(example_path) else STUB_GOLDEN_CFG
                svc_dir = self.spool / "2026-03-01T00:00:00Z" / req_id

                for name in ["plan.json", "decision_response.json", "ledger_row.json", "shadow_run_record.json", "ingestion_batch.json"]:
                    golden = (golden_dir / name).read_bytes()
                    svc = (svc_dir / name).read_bytes()
                    self.assertEqual(svc, golden, f"{name} byte mismatch for {req_id}")


if __name__ == "__main__":
    unittest.main()
