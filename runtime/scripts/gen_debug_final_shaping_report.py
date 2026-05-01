#!/usr/bin/env python3
"""
Emit docs/validation/DEBUG_FINAL_SHAPING_REPORT.md (policy + regenerate instructions).

Does not require a live Plan-Gate; run `mcoder scenario --type debug` separately.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "validation" / "DEBUG_FINAL_SHAPING_REPORT.md"
SCENARIOS = ROOT / "docs" / "validation" / "scenario_lists" / "debug_scenarios.txt"


def main() -> int:
    iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    scenarios = ""
    if SCENARIOS.is_file():
        lines = [ln.strip() for ln in SCENARIOS.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]
        scenarios = "\n".join(f"{i}. `{ln}`" for i, ln in enumerate(lines, start=1))

    body = f"""# Debug narration — final shaping (pre-freeze)

Generated: **{iso}**

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

{scenarios or "(scenario file not found)"}

## Regenerate (Motadata workspace)

Unset governed Ask if you want deterministic comparison; restart Plan-Gate after pulling m-coder.

```bash
mcoder scenario --type debug --file ~/Harshil-PoCs/m-coder/docs/validation/scenario_lists/debug_scenarios.txt
```

## Unit coverage

```bash
PYTHONPATH=. python3 -m pytest runtime/tests/test_debug_output_finalize.py runtime/tests/test_reasoner_explain_debug_prompt.py -q
```

"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body, encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
