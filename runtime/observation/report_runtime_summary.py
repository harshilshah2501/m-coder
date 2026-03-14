"""
M4.1 CLI Runtime Report — Command-line interface for runtime observability.

Requirements:
- Summary mode: aggregate statistics
- Request trace mode: trace by request_id
- Canonical hash trace mode: trace by canonical_hash

Usage:
    python -m runtime.observation.report_runtime_summary --summary
    python -m runtime.observation.report_runtime_summary --request-id <id>
    python -m runtime.observation.report_runtime_summary --canonical-hash <hash>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from runtime.observation.trace_builder import TraceBuilder
from runtime.observation.summary_queries import RuntimeSummaryQueries
from runtime.observation.explanation_builder import ExplanationBuilder


def print_summary(
    ledger_path: Path,
    output: TextIO = sys.stdout,
    json_output: bool = False,
) -> None:
    """
    Print aggregate runtime summary.
    
    Args:
        ledger_path: Path to the ledger database
        output: Output stream (default: stdout)
        json_output: If True, output as JSON
    """
    queries = RuntimeSummaryQueries.from_path(ledger_path)
    summary = queries.get_summary()
    
    if json_output:
        output.write(json.dumps(summary.to_dict(), indent=2))
        output.write("\n")
        return
    
    output.write("=" * 60 + "\n")
    output.write("RUNTIME SUMMARY\n")
    output.write("=" * 60 + "\n\n")
    
    # Totals
    output.write("TOTALS\n")
    output.write("-" * 40 + "\n")
    output.write(f"  Total requests:          {summary.total_requests}\n")
    output.write(f"  Total events:            {summary.total_events}\n")
    output.write(f"  Unique canonical hashes: {summary.unique_canonical_hashes}\n")
    output.write(f"  Replay count:            {summary.replay_count}\n")
    output.write("\n")
    
    # Time range
    if summary.earliest_event:
        output.write("TIME RANGE\n")
        output.write("-" * 40 + "\n")
        output.write(f"  Earliest: {summary.earliest_event}\n")
        output.write(f"  Latest:   {summary.latest_event}\n")
        output.write("\n")
    
    # Posture distribution
    output.write("POSTURE DISTRIBUTION\n")
    output.write("-" * 40 + "\n")
    postures = summary.postures
    total = postures.total or 1  # avoid div by zero
    output.write(f"  Refused:       {postures.refused:5d}  ({100*postures.refused/total:.1f}%)\n")
    output.write(f"  Deferred:      {postures.deferred:5d}  ({100*postures.deferred/total:.1f}%)\n")
    output.write(f"  Bounded Allow: {postures.bounded_allow:5d}  ({100*postures.bounded_allow/total:.1f}%)\n")
    output.write(f"  Safe Execute:  {postures.safe_execute:5d}  ({100*postures.safe_execute/total:.1f}%)\n")
    output.write(f"  Executed:      {postures.executed:5d}  ({100*postures.executed/total:.1f}%)\n")
    output.write(f"  Blocked:       {postures.blocked:5d}  ({100*postures.blocked/total:.1f}%)\n")
    output.write("\n")
    
    # Top refusal reasons
    if summary.top_refusal_reasons:
        output.write("TOP REFUSAL REASONS\n")
        output.write("-" * 40 + "\n")
        for i, refusal in enumerate(summary.top_refusal_reasons[:5], 1):
            output.write(f"  {i}. {refusal.reason} ({refusal.count} occurrences)\n")
        output.write("\n")
    
    # Backend distribution
    if summary.backend_distribution:
        output.write("BACKEND DISTRIBUTION\n")
        output.write("-" * 40 + "\n")
        for backend in summary.backend_distribution:
            success_rate = (
                100 * backend.success_count / backend.count if backend.count else 0
            )
            output.write(
                f"  {backend.backend}: {backend.count} executions "
                f"({backend.success_count} success, {backend.failure_count} failure, "
                f"{success_rate:.1f}% success rate)\n"
            )
        output.write("\n")
    
    # Recent events preview
    if summary.recent_events:
        output.write("RECENT EVENTS (most recent first)\n")
        output.write("-" * 40 + "\n")
        for event in summary.recent_events[:5]:
            output.write(f"  [{event.timestamp_utc}] {event.event_type}: {event.posture}\n")
            if event.reason:
                output.write(f"    Reason: {event.reason[:60]}...\n" if len(event.reason) > 60 else f"    Reason: {event.reason}\n")
        output.write("\n")


def print_request_trace(
    ledger_path: Path,
    request_id: str,
    output: TextIO = sys.stdout,
    json_output: bool = False,
) -> None:
    """
    Print execution trace for a request_id.
    
    Args:
        ledger_path: Path to the ledger database
        request_id: The request identifier to trace
        output: Output stream (default: stdout)
        json_output: If True, output as JSON
    """
    builder = TraceBuilder.from_path(ledger_path)
    trace = builder.build_by_request_id(request_id)
    
    if json_output:
        output.write(json.dumps(trace.to_dict(), indent=2))
        output.write("\n")
        return
    
    output.write("=" * 60 + "\n")
    output.write(f"TRACE: request_id={request_id}\n")
    output.write("=" * 60 + "\n\n")
    
    if not trace.events:
        output.write("No events found for this request_id.\n")
        return
    
    output.write(f"Total events: {trace.total_events}\n")
    output.write(f"Time range:   {trace.first_event_time} → {trace.last_event_time}\n")
    output.write(f"Final posture: {trace.final_posture}\n")
    if trace.canonical_hash:
        output.write(f"Canonical hash: {trace.canonical_hash}\n")
    output.write("\n")
    
    output.write("EVENTS (chronological order)\n")
    output.write("-" * 40 + "\n")
    
    explainer = ExplanationBuilder()
    for i, event in enumerate(trace.events, 1):
        output.write(f"\n[{i}] {event.event_type}\n")
        output.write(f"    Timestamp: {event.timestamp_utc}\n")
        output.write(f"    Posture:   {event.posture}\n")
        if event.reason:
            output.write(f"    Reason:    {event.reason}\n")
        if event.backend:
            output.write(f"    Backend:   {event.backend}\n")
        if event.exit_code is not None:
            output.write(f"    Exit code: {event.exit_code}\n")
        if event.duration_ms is not None:
            output.write(f"    Duration:  {event.duration_ms}ms\n")
        
        # Human-readable explanation
        explanation = explainer.build_from_trace_event(event)
        output.write(f"    → {explanation.explanation}\n")
    
    output.write("\n")


def print_canonical_hash_trace(
    ledger_path: Path,
    canonical_hash: str,
    output: TextIO = sys.stdout,
    json_output: bool = False,
) -> None:
    """
    Print execution trace for a canonical_hash.
    
    Args:
        ledger_path: Path to the ledger database
        canonical_hash: The canonical execution hash to trace
        output: Output stream (default: stdout)
        json_output: If True, output as JSON
    """
    builder = TraceBuilder.from_path(ledger_path)
    trace = builder.build_by_canonical_hash(canonical_hash)
    
    if json_output:
        output.write(json.dumps(trace.to_dict(), indent=2))
        output.write("\n")
        return
    
    output.write("=" * 60 + "\n")
    output.write(f"TRACE: canonical_hash={canonical_hash[:32]}...\n")
    output.write("=" * 60 + "\n\n")
    
    if not trace.events:
        output.write("No events found for this canonical_hash.\n")
        return
    
    output.write(f"Total events:   {trace.total_events}\n")
    output.write(f"Request IDs:    {', '.join(trace.request_ids)}\n")
    output.write(f"Time range:     {trace.first_event_time} → {trace.last_event_time}\n")
    output.write(f"Final posture:  {trace.final_posture}\n")
    output.write("\n")
    
    # Group events by request_id for clearer view
    output.write("EVENTS BY REQUEST (chronological within each)\n")
    output.write("-" * 40 + "\n")
    
    explainer = ExplanationBuilder()
    events_by_request: dict[str, list] = {}
    for event in trace.events:
        if event.request_id not in events_by_request:
            events_by_request[event.request_id] = []
        events_by_request[event.request_id].append(event)
    
    for request_id, events in events_by_request.items():
        output.write(f"\n  Request: {request_id}\n")
        for event in events:
            output.write(f"    [{event.timestamp_utc}] {event.event_type}: {event.posture}\n")
            explanation = explainer.build_from_trace_event(event)
            output.write(f"      → {explanation.explanation}\n")
    
    output.write("\n")


def main(args: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="M4.1 Runtime Observability Report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--ledger-path",
        type=Path,
        help="Path to the ledger database (default: MOTADATA_EXECUTE_LEDGER_PATH env var)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    
    # Mutually exclusive modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--summary",
        action="store_true",
        help="Print aggregate runtime summary",
    )
    mode_group.add_argument(
        "--request-id",
        type=str,
        help="Print trace for a specific request_id",
    )
    mode_group.add_argument(
        "--canonical-hash",
        type=str,
        help="Print trace for a specific canonical_hash",
    )
    
    parsed = parser.parse_args(args)
    
    # Determine ledger path
    ledger_path = parsed.ledger_path
    if not ledger_path:
        import os
        env_path = os.environ.get("MOTADATA_EXECUTE_LEDGER_PATH")
        if env_path:
            ledger_path = Path(env_path)
        else:
            print("Error: --ledger-path required or set MOTADATA_EXECUTE_LEDGER_PATH", file=sys.stderr)
            return 1
    
    if not ledger_path.exists():
        print(f"Error: Ledger file not found: {ledger_path}", file=sys.stderr)
        return 1
    
    try:
        if parsed.summary:
            print_summary(ledger_path, json_output=parsed.json)
        elif parsed.request_id:
            print_request_trace(ledger_path, parsed.request_id, json_output=parsed.json)
        elif parsed.canonical_hash:
            print_canonical_hash_trace(ledger_path, parsed.canonical_hash, json_output=parsed.json)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
