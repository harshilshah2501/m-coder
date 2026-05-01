# Debug narration — final shaping (pre-freeze)

Generated: **2026-05-01 09:50 UTC**

## Scope implemented (m-coder)

- **`runtime/ask_service/debug_output_finalize.py`**: `finalize_explain_debug_prose()` — removes habitual speculative /
  consulting-padding sentences, collapses **`logic_flow`** to **≤3** imperative lines, tightens **`likely_bug_risk`**
  when it lacks concrete branch/I/O/route/persistence cues.
- **`runtime/ask_service/reasoner.py`**: SNMP/trap-ish snippets still get trap-specific deepening; generic files no longer get
  fake “decrypt trap.db” branching unless trap/SNMP context is visible.
- **`runtime/ask_service/debug_narration_gate.py`**: CURATED fallbacks use **imperative** next steps instead of vague “might” prose.
- **`runtime/mcoder_cli/cli.py`**: **Next inspection** prints **up to three** `-` bullets (newline-separated **`logic_flow`**).
- Wired after `apply_debug_narration_gate` in **`v1_ingest.py`** and **`handlers.py`** — **no** retrieval, Ask, synthesis, governed reward changes.

## Preserved behaviors

- Missing selected file refusal path (evidence cues with `missing_in_context`).
- **EventBus inspection cues** and **API route inspection cues** (`cli.py`) unchanged in structure.
- **Limit:** line (`confidence_limits` / `_naturalize_debug_limit`) unchanged.

## Full debug scenario list

1. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java|Debug why availability correlation might skip enrichment branches.`
2. `motadata/src/main/java/com/mindarray/api/MailServerConfiguration.java|Debug why mail server updates are not reflected after API update.`
3. `motadata/src/main/java/com/mindarray/store/AbstractConfigStore.java|Debug null-return paths in AbstractConfigStore.getItem and related callers.`
4. `motadata/src/main/java/com/mindarray/nms/SNMPTrapProcessor.java|Debug where SNMP trap parsing can fail before alert generation.`
5. `motadata/src/main/java/com/mindarray/aiops/doesnotexist/MissingEngine.java|Explain failure points for a file that is not in retrieved context.`
6. `motadata/src/main/java/com/mindarray/api/APIServer.java|Why might a newly registered API route not appear at runtime despite a successful start()?`
7. `motadata/src/main/java/com/mindarray/api/MailServerConfiguration.java|What conditions could cause mail delivery settings to appear stale after an admin update?`

## Regenerate (Motadata workspace)

Unset governed Ask if you want deterministic comparison; restart Plan-Gate after pulling m-coder.

```bash
mcoder scenario --type debug --file ~/Harshil-PoCs/m-coder/docs/validation/scenario_lists/debug_scenarios.txt
```

## Unit coverage

```bash
PYTHONPATH=. python3 -m pytest runtime/tests/test_debug_output_finalize.py runtime/tests/test_reasoner_explain_debug_prompt.py -q
```

