# Action 5 — Plan-Gate observability (correlation order)

**Purpose:** Reconstruct one governed request end-to-end from logs and response JSON **without inference**.

## Correlation spine (use in this order)

1. **`trace_id`** — Cross-hop spine when present (Ask v0/v1, explain); Plan-Gate logs use `(none)` when absent (never omit the field).
2. **`request_id`** — Per-request identifier in JSON bodies and `PLAN_GATE request` lines.
3. **`routing_mode`** — `plan_only` vs `explain_debug` (response + Plan-Gate log for `/v0/ask`, `/v1/ask`).
4. **`plugin_ask_routing`** — Plugin-only; see Action 4 / JetBrains metadata (not emitted by Plan-Gate HTTP).

## Log prefixes (grep)

| Prefix | Meaning |
|--------|---------|
| `PLAN_GATE request` | One line per Plan-Gate HTTP POST: `path`, `request_type`, `request_id`, `trace_id`, `routing_mode`, `outcome`, `status`, `duration_ms` |
| `[ASK]` | v0 Ask handler entry (`task_type` included) |
| `[ASK_V1]` | v1 Ask handler entry |
| `EXPLAIN_DEBUG` | Model/explain path (`routing_mode=explain_debug` in line) |
| `[EXECUTE]` | Execute handler entry (`phase=begin`); outcome is in `PLAN_GATE` line for `POST /v0/execute` |

## Execute

- Optional **`trace_id`** on execute JSON is logged as `(none)` if absent.
- **`outcome`** on the `PLAN_GATE` line echoes execute response (`EXECUTED`, `BLOCKED`, `REFUSED`, etc.).

## Tests

- `runtime/plan_gate_service/tests/test_plan_gate_request_logging.py`
- `runtime/tests/test_action5_observability.py`
