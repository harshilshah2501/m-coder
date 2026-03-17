"""
M4.1 CLI Runtime Report Tests — Verify CLI modes and output.

Tests:
- Summary mode output
- Request trace mode
- Canonical hash trace mode
- JSON output format
- Error handling
"""

import io
import json
import tempfile
from pathlib import Path

import pytest

from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore
from runtime.observation.report_runtime_summary import (
    print_summary,
    print_request_trace,
    print_canonical_hash_trace,
    print_request_explanation,
    print_canonical_hash_explanation,
    main,
)


@pytest.fixture
def ledger_path():
    """Create a temporary ledger with test data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = Path(f.name)
    
    store = SandboxLedgerStore(path, fixed_time="2026-03-13T10:00:00Z")
    
    # Add test events
    store.append(
        ledger_row_id="row-1",
        event_type="plangate_refused",
        outcome_type="refused",
        request_id="req-001",
        plan_hash="plan-001",
        payload={
            "reason": "protected branch mutation",
            "canonical_hash": "hash-abc-123",
        },
    )
    
    store.append(
        ledger_row_id="row-2",
        event_type="plangate_safe_execute",
        outcome_type="safe_execute",
        request_id="req-002",
        plan_hash="plan-002",
        payload={"canonical_hash": "hash-def-456"},
    )
    
    store.append(
        ledger_row_id="row-3",
        event_type="sandbox_executed",
        outcome_type="executed",
        request_id="req-002",
        plan_hash="plan-002",
        payload={
            "canonical_hash": "hash-def-456",
            "backend": "local_process",
            "exit_code": 0,
            "duration_ms": 150,
        },
    )
    
    yield path
    
    path.unlink(missing_ok=True)


class TestPrintSummary:
    """Tests for print_summary function."""
    
    def test_summary_text_output(self, ledger_path):
        """Test text format summary output."""
        output = io.StringIO()
        print_summary(ledger_path, output=output)
        
        result = output.getvalue()
        
        assert "RUNTIME SUMMARY" in result
        assert "TOTALS" in result
        assert "Total requests:" in result
        assert "POSTURE DISTRIBUTION" in result
        assert "Refused:" in result
    
    def test_summary_json_output(self, ledger_path):
        """Test JSON format summary output."""
        output = io.StringIO()
        print_summary(ledger_path, output=output, json_output=True)
        
        result = output.getvalue()
        data = json.loads(result)
        
        assert "total_requests" in data
        assert "total_events" in data
        assert "postures" in data
        assert data["total_requests"] == 2
    
    def test_summary_shows_postures(self, ledger_path):
        """Test that summary includes posture distribution."""
        output = io.StringIO()
        print_summary(ledger_path, output=output)
        
        result = output.getvalue()
        
        assert "Safe Execute:" in result
        assert "Executed:" in result


class TestPrintRequestTrace:
    """Tests for print_request_trace function."""
    
    def test_request_trace_text_output(self, ledger_path):
        """Test text format request trace output with C1 fields."""
        output = io.StringIO()
        print_request_trace(ledger_path, "req-002", output=output)

        result = output.getvalue()

        assert "TRACE: request_id=req-002" in result
        assert "request_id:      req-002" in result
        assert "replay:" in result
        assert "started_at:" in result
        assert "ended_at:" in result
        assert "Total events:" in result and "2" in result
        assert "PLAN_APPROVED" in result
        assert "EXECUTION_COMPLETED" in result
    
    def test_request_trace_json_output(self, ledger_path):
        """Test JSON format request trace output with C1 fields."""
        output = io.StringIO()
        print_request_trace(ledger_path, "req-002", output=output, json_output=True)

        result = output.getvalue()
        data = json.loads(result)

        assert data["trace_id"] == "req-002"
        assert data["lookup_type"] == "request_id"
        assert "request_id" in data
        assert "started_at" in data
        assert "ended_at" in data
        assert "is_replay" in data
        assert len(data["events"]) == 2
    
    def test_request_trace_not_found(self, ledger_path):
        """Test trace for non-existent request."""
        output = io.StringIO()
        print_request_trace(ledger_path, "req-nonexistent", output=output)
        
        result = output.getvalue()
        
        assert "No events found" in result
    
    def test_request_trace_shows_explanation(self, ledger_path):
        """Test that trace includes human-readable explanations."""
        output = io.StringIO()
        print_request_trace(ledger_path, "req-001", output=output)
        
        result = output.getvalue()
        
        # Should include explanation arrow
        assert "→" in result
        assert "refused" in result.lower()


class TestPrintCanonicalHashTrace:
    """Tests for print_canonical_hash_trace function."""
    
    def test_canonical_hash_trace_text_output(self, ledger_path):
        """Test text format canonical hash trace output (latest request group)."""
        output = io.StringIO()
        print_canonical_hash_trace(ledger_path, "hash-def-456", output=output)

        result = output.getvalue()

        assert "TRACE: canonical_hash=hash-def-456" in result
        assert "lookup:          canonical_hash (latest request group)" in result
        assert "canonical_hash:  hash-def-456" in result
        assert "req-002" in result
    
    def test_canonical_hash_trace_json_output(self, ledger_path):
        """Test JSON format canonical hash trace output."""
        output = io.StringIO()
        print_canonical_hash_trace(
            ledger_path, "hash-def-456", output=output, json_output=True
        )
        
        result = output.getvalue()
        data = json.loads(result)
        
        assert data["trace_id"] == "hash-def-456"
        assert data["lookup_type"] == "canonical_hash"
        assert "req-002" in data["request_ids"]
    
    def test_canonical_hash_trace_not_found(self, ledger_path):
        """Test trace for non-existent canonical hash."""
        output = io.StringIO()
        print_canonical_hash_trace(ledger_path, "hash-nonexistent", output=output)

        result = output.getvalue()

        assert "No events found" in result


class TestPrintRequestExplanation:
    """Tests for print_request_explanation (C2 explanation by request_id)."""

    def test_request_explanation_text_output(self, ledger_path):
        """Test text format request explanation output."""
        output = io.StringIO()
        print_request_explanation(ledger_path, "req-002", output=output)

        result = output.getvalue()

        assert "EXPLANATION: request_id=req-002" in result
        assert "final_outcome:" in result
        assert "summary:" in result
        assert "decisive_factors:" in result
        assert "evidence_refs:" in result
        assert "is_replay:" in result

    def test_request_explanation_json_output(self, ledger_path):
        """Test JSON format request explanation output."""
        output = io.StringIO()
        print_request_explanation(
            ledger_path, "req-002", output=output, json_output=True
        )

        result = output.getvalue()
        data = json.loads(result)

        assert "request_id" in data
        assert "final_outcome" in data
        assert "summary" in data
        assert "decisive_factors" in data
        assert "evidence_refs" in data
        assert "is_replay" in data

    def test_request_explanation_not_found(self, ledger_path):
        """Test explanation for non-existent request_id."""
        output = io.StringIO()
        print_request_explanation(
            ledger_path, "req-nonexistent", output=output
        )

        result = output.getvalue()
        assert "No explanation" in result
        assert "request_id" in result or "req-nonexistent" in result

    def test_request_explanation_not_found_json(self, ledger_path):
        """Test explanation not-found JSON output."""
        output = io.StringIO()
        print_request_explanation(
            ledger_path, "req-nonexistent", output=output, json_output=True
        )

        result = output.getvalue()
        data = json.loads(result)
        assert data.get("error") == "not_found"
        assert data.get("request_id") == "req-nonexistent"


class TestPrintCanonicalHashExplanation:
    """Tests for print_canonical_hash_explanation (C2 by canonical_hash)."""

    def test_canonical_hash_explanation_text_output(self, ledger_path):
        """Test text format canonical hash explanation output."""
        output = io.StringIO()
        print_canonical_hash_explanation(
            ledger_path, "hash-def-456", output=output
        )

        result = output.getvalue()

        assert "EXPLANATION: canonical_hash=hash-def-456" in result
        assert "lookup:            canonical_hash (latest request group)" in result
        assert "final_outcome:" in result
        assert "summary:" in result
        assert "is_replay:" in result

    def test_canonical_hash_explanation_json_output(self, ledger_path):
        """Test JSON format canonical hash explanation output."""
        output = io.StringIO()
        print_canonical_hash_explanation(
            ledger_path, "hash-def-456", output=output, json_output=True
        )

        result = output.getvalue()
        data = json.loads(result)

        assert "final_outcome" in data
        assert "summary" in data
        assert "is_replay" in data

    def test_canonical_hash_explanation_not_found(self, ledger_path):
        """Test explanation for non-existent canonical_hash."""
        output = io.StringIO()
        print_canonical_hash_explanation(
            ledger_path, "hash-nonexistent", output=output
        )

        result = output.getvalue()
        assert "No explanation" in result
        assert "canonical_hash" in result

    def test_canonical_hash_explanation_not_found_json(self, ledger_path):
        """Test canonical hash explanation not-found JSON output."""
        output = io.StringIO()
        print_canonical_hash_explanation(
            ledger_path, "hash-nonexistent", output=output, json_output=True
        )

        result = output.getvalue()
        data = json.loads(result)
        assert data.get("error") == "not_found"
        assert data.get("canonical_hash") == "hash-nonexistent"


class TestMain:
    """Tests for CLI main function."""
    
    def test_main_summary(self, ledger_path):
        """Test main with --summary flag."""
        exit_code = main(["--ledger-path", str(ledger_path), "--summary"])
        assert exit_code == 0
    
    def test_main_request_id(self, ledger_path):
        """Test main with --request-id flag."""
        exit_code = main(["--ledger-path", str(ledger_path), "--request-id", "req-002"])
        assert exit_code == 0
    
    def test_main_canonical_hash(self, ledger_path):
        """Test main with --canonical-hash flag."""
        exit_code = main(
            ["--ledger-path", str(ledger_path), "--canonical-hash", "hash-def-456"]
        )
        assert exit_code == 0

    def test_main_request_explanation(self, ledger_path):
        """Test main with --request-explanation flag."""
        exit_code = main(
            [
                "--ledger-path",
                str(ledger_path),
                "--request-explanation",
                "req-002",
            ]
        )
        assert exit_code == 0

    def test_main_canonical_hash_explanation(self, ledger_path):
        """Test main with --canonical-hash-explanation flag."""
        exit_code = main(
            [
                "--ledger-path",
                str(ledger_path),
                "--canonical-hash-explanation",
                "hash-def-456",
            ]
        )
        assert exit_code == 0

    def test_main_request_explanation_not_found(self, ledger_path):
        """Test main --request-explanation with missing request_id."""
        exit_code = main(
            [
                "--ledger-path",
                str(ledger_path),
                "--request-explanation",
                "req-nonexistent",
            ]
        )
        assert exit_code == 0

    def test_main_canonical_hash_explanation_not_found(self, ledger_path):
        """Test main --canonical-hash-explanation with missing hash."""
        exit_code = main(
            [
                "--ledger-path",
                str(ledger_path),
                "--canonical-hash-explanation",
                "hash-nonexistent",
            ]
        )
        assert exit_code == 0

    def test_main_json_output(self, ledger_path):
        """Test main with --json flag."""
        exit_code = main(["--ledger-path", str(ledger_path), "--summary", "--json"])
        assert exit_code == 0
    
    def test_main_missing_ledger(self):
        """Test main with missing ledger file."""
        exit_code = main(["--ledger-path", "/nonexistent/path.db", "--summary"])
        assert exit_code == 1
    
    def test_main_no_ledger_path_without_env(self, monkeypatch):
        """Test main without ledger path or env var."""
        monkeypatch.delenv("MOTADATA_EXECUTE_LEDGER_PATH", raising=False)
        exit_code = main(["--summary"])
        assert exit_code == 1


class TestEmptyLedger:
    """Tests with empty ledger."""
    
    def test_summary_empty_ledger(self):
        """Test summary with empty ledger."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = Path(f.name)
        
        try:
            SandboxLedgerStore(path)
            
            output = io.StringIO()
            print_summary(path, output=output)
            
            result = output.getvalue()
            assert "Total requests:" in result
            assert "0" in result
        finally:
            path.unlink(missing_ok=True)
