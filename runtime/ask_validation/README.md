# Layer-5 Grounded Ask Validation Harness

A lightweight, repeatable validation harness for measuring grounded Ask progress.

## Purpose

This harness prevents subjective "it seems better" progress claims by enforcing concrete, measurable gates for grounded Ask behavior.

## Quick Start

```bash
# Run the full validation suite
pytest runtime/tests/test_ask_validation_harness.py -v

# Run with detailed output
pytest runtime/tests/test_ask_validation_harness.py::test_harness_full_suite -v -s
```

## Metrics

### Measured Directly

| Metric | Description |
|--------|-------------|
| **Empty Bundle Rate** | % of grounded queries that returned no files |
| **Relevant File Presence Rate** | % of grounded queries that found expected files |
| **Avg E2E Latency** | Mean end-to-end Ask latency (ms) |
| **Max E2E Latency** | Maximum end-to-end latency (ms) |
| **No-Match Justification Rate** | % of no-match queries with valid justification |

### Not Instrumented

| Metric | Status |
|--------|--------|
| **Retrieval Latency** | Requires ContextEngine instrumentation; currently unavailable |

> **Note**: Retrieval latency is NOT estimated as a percentage of E2E latency.
> The harness reports only what it can measure directly. To enable retrieval
> latency measurement, instrument `ContextEngine.build_context_bundle()` with
> timing data in the returned bundle or via a side-channel.

## Grounded Success Definition

A query is **grounded successfully** if ALL of these are true:

1. `context_bundle.files` is non-empty
2. At least one file matches expected patterns (if specified)
3. Expected selectors contributed to the result
4. `ui.severity` is `"info"` (not `"warning"`)
5. `ui.message` does not contain "ungrounded" or "no context"

## Valid No-Match Definition

A query returns a **valid no-match** if ALL of these are true:

1. `context_bundle.files` is empty
2. `plan_summary.notes` OR `ui.message` contains justification keywords
   - e.g., "no grounded", "ungrounded", "no context"
3. `ui.severity` is `"warning"`

An **invalid no-match** occurs when files are empty but no justification is provided.

## Latency Reporting

**End-to-End Latency** (measured directly):
- Total time from `handle_ask_request()` call to response return
- Includes context retrieval, planning, and response construction

**Retrieval Latency** (NOT instrumented):
- Would measure time for `ContextEngine.build_context_bundle()` specifically
- Requires engine-level instrumentation to measure accurately
- This harness does NOT estimate retrieval latency as a percentage of E2E
- When retrieval timing is needed, instrument the ContextEngine directly

## Golden Query Suite

The harness includes a curated set of golden queries:

### Grounded Queries (files MUST be found)
- `grounded_symbol_retry`: Symbol hint matching
- `grounded_symbol_config`: Configuration-related queries
- `grounded_symbol_database`: Database connection queries
- `grounded_explicit_file`: Explicit file selection
- `edge_case_insensitive`: Case-insensitive matching
- `edge_multiple_matches`: Multiple file matches

### No-Match Queries (valid justification required)
- `no_match_nonexistent_symbol`: Truly nonexistent symbols
- `no_match_unrelated_tech`: Technology mismatch
- `no_match_obscure_feature`: Feature not in codebase

## Wave Transition Gates

Example gate conditions for Wave 2 transition:

```python
gate_checks = {
    "empty_bundle_rate_below_50pct": metrics.empty_bundle_rate < 0.5,
    "file_presence_above_50pct": metrics.relevant_file_presence_rate > 0.5,
    "no_match_justified_above_80pct": metrics.no_match_justification_rate > 0.8,
    "e2e_latency_under_1s": metrics.max_e2e_latency_ms < 1000,
}
```

These thresholds should be tuned based on baseline measurements during Wave 1.

**Note on Retrieval Latency Gates**:
Retrieval latency gates cannot be enforced until ContextEngine instrumentation
is added. Until then, use E2E latency as the primary latency gate.

## Extending the Suite

Add new golden queries in `golden_queries.py`:

```python
GoldenQuery(
    id="my_new_query",
    query="What does the widget factory do?",
    expectation=QueryExpectation.GROUNDED,
    repo_files={
        "widgets/factory.py": "class WidgetFactory:\n    pass\n",
    },
    expected_file_patterns=["widget", "factory"],
    expected_selectors=["symbols"],
    description="Widget factory should be found",
)
```

## Architecture

```
runtime/ask_validation/
├── __init__.py           # Public API
├── golden_queries.py     # Query definitions
├── harness.py            # Validation harness
└── README.md             # This file

runtime/tests/
└── test_ask_validation_harness.py  # Pytest entrypoint
```

## Design Principles

1. **Lightweight**: Fast enough for iteration during Waves 1-2
2. **Repeatable**: Same command, same metrics, deterministic
3. **Enforceable**: Concrete pass/fail, no subjective judgments
4. **Extensible**: Easy to add queries and metrics
5. **Gate-Ready**: Can serve as Wave transition checkpoint
