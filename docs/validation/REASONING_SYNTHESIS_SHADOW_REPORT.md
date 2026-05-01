# Reasoning synthesis shadow report

Generated: 2026-05-01 06:08 UTC

Compares **legacy narration** (`articulated_answer` or `explain_debug` stub) with **metadata.reasoning_synthesis** (Phase A/B only; Ask prose unchanged). Explain/Debug calls are **stubbed** to avoid vLLM.

## Summary rollup

- Scenarios: **16**
- Synthesis `method_collapse_risk.detected` true: **0**
- Rubric `method_collapse_detected` true: **0**
- Avg depth / fluency / grounding: **3.00** / **2.00** / **2.00**
- Overclaim histogram: `{1: 16}`

## Per scenario

| Suite | # | Subsystem | Collapse | Distinct | depth | fluency | grounding | overclaim | m-collapse | Legacy (excerpt) |
|-------|---|-----------|----------|----------|-------|---------|-----------|-----------|------------|------------------|
| ask | 1 | api_layer | False | 9 | 3 | 2 | 2 | 1 | False | `AbstractAPI` is the shared superclass for concrete REST/API handler classes. Confirm `extends` on concrete `*API` classes when the graph chain is partial or shows only deployment types. |
| ask | 2 | mail_configuration | False | 7 | 3 | 2 | 2 | 1 | False | Available context is insufficient to confirm a full architecture flow. The full downstream chain is not fully visible in this snapshot. |
| ask | 3 | config_store | False | 7 | 3 | 2 | 2 | 1 | False | Available context is insufficient to confirm a full architecture flow. The full downstream chain is not fully visible in this snapshot. |
| ask | 4 | api_layer | False | 7 | 3 | 2 | 2 | 1 | False | Available context is insufficient to confirm a full architecture flow. The full downstream chain is not fully visible in this snapshot. |
| ask | 5 | api_layer | False | 13 | 3 | 2 | 2 | 1 | False | Notification flow is coordinated by `NotificationEngine`. Channel and trigger concerns are handled by `EmailNotification`, `Notification`, and `SMSNotification`. Selected EventBus addresses include `change.notification`, `change.local.notification`. The full downstream chain is n… |
| ask | 6 | api_layer | False | 7 | 3 | 2 | 2 | 1 | False | `AbstractAPI` is the shared superclass for concrete REST/API handler classes. Confirm `extends` on concrete `*API` classes when the graph chain is partial or shows only deployment types. |
| ask | 7 | api_layer | False | 7 | 3 | 2 | 2 | 1 | False | Available context is insufficient to confirm a full architecture flow. The full downstream chain is not fully visible in this snapshot. |
| ask | 8 | api_layer | False | 13 | 3 | 2 | 2 | 1 | False | Notification flow is coordinated by `NotificationEngine`. Channel and trigger concerns are handled by `EmailNotification`, `Notification`, and `SMSNotification`. Selected EventBus addresses include `change.notification`, `change.local.notification`. The full downstream chain is n… |
| ask | 9 | general | False | 7 | 3 | 2 | 2 | 1 | False | For alert/enrichment changes, use phased rollout with feature-flag gating, pre/post validation checks, and a rollback path tied to concrete risk signals. Ground the work against classes in this snapshot, e.g. `sample`. This is architectural guidance in ASK mode; use PLAN mode for… |
| debug | 10 | api_layer | False | 10 | 3 | 2 | 2 | 1 | False | Shadow stub: inspect branching and validation near the selected anchor.  Shadow stub: trace callers from the snippet outward. |
| debug | 11 | general | False | 7 | 3 | 2 | 2 | 1 | False | Shadow stub: inspect branching and validation near the selected anchor.  Shadow stub: trace callers from the snippet outward. |
| debug | 12 | general | False | 7 | 3 | 2 | 2 | 1 | False | Shadow stub: inspect branching and validation near the selected anchor.  Shadow stub: trace callers from the snippet outward. |
| debug | 13 | general | False | 7 | 3 | 2 | 2 | 1 | False | Shadow stub: inspect branching and validation near the selected anchor.  Shadow stub: trace callers from the snippet outward. |
| debug | 14 | general | False | 7 | 3 | 2 | 2 | 1 | False | Shadow stub: inspect branching and validation near the selected anchor.  Shadow stub: trace callers from the snippet outward. |
| debug | 15 | general | False | 7 | 3 | 2 | 2 | 1 | False | Shadow stub: inspect branching and validation near the selected anchor.  Shadow stub: trace callers from the snippet outward. |
| debug | 16 | general | False | 7 | 3 | 2 | 2 | 1 | False | Shadow stub: inspect branching and validation near the selected anchor.  Shadow stub: trace callers from the snippet outward. |

## Regenerate

```bash
PYTHONPATH=. python3 runtime/scripts/gen_reasoning_synthesis_shadow_report.py
```
