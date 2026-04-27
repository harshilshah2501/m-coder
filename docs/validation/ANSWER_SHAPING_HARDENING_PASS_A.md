# Answer Shaping Hardening Pass A

## Scope

Pass A only (CLI summary shaping only).  
No retrieval, Plan-Gate contract/schema, governance posture, execution path, model, or KG changes.

## Changed Files

- `runtime/mcoder_cli/answer_shaping.py`
- `runtime/mcoder_cli/cli.py`
- `runtime/scripts/motadata_query_cli.py`
- `runtime/tests/test_answer_shaping_pass_a.py`

## What Changed

- Added an intent-aware CLI summary shaper for prompt responses:
  - structural/base-class queries: direct answer first, suppress owner follow-up.
  - how/explain/architecture queries: concise explanation plus owner anchor guidance.
  - find/list queries: class-list-first rendering when multiple relevant classes are present.
  - why/debug-like prompt text: hypothesis-oriented shaping.
- Replaced raw snippet dump display (`Method-window excerpt`, `Visible method-window evidence`) in default human CLI summaries with readable inspection guidance.
- Preserved evidence honesty by using bounded wording (`Based on current evidence...`) in shaped outputs.

## Before / After (Representative)

### Base class prompt
- Before: direct answer + owner-anchor style follow-up in some cases.
- After: direct `AbstractAPI` answer only for structural base-class intent.

### How/architecture prompts
- Before: owner-first boilerplate and raw compressed method snippets in `next_step`.
- After: concise explanation with explicit class/method anchor and human-readable inspection guidance.

### Discovery prompt
- Before: single owner emphasis.
- After: list-style class output when evidence includes multiple relevant classes.

## Tests Run

- `pytest -q runtime/tests/test_answer_shaping_pass_a.py`
- `python3 -m py_compile runtime/mcoder_cli/answer_shaping.py runtime/mcoder_cli/cli.py runtime/scripts/motadata_query_cli.py`

## Known Limitations

- Pass A is presentation-level shaping only; it does not alter upstream plan-step generation.
- Discovery list quality depends on classes present in evidence/context bundle.
- Debug-depth synthesis remains bounded to existing explain payload and available context.

## Deferred to Pass B

Knowledge-graph / structural graph augmentation is explicitly deferred.  
Pass A does not introduce graph extraction, graph storage, Neo4j integration, or KG-backed reasoning.

