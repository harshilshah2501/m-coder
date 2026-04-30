# EventBus Topology Map v1 Freeze Report

## Scope
EventBus extractor only.

This freeze covers:
- EventBus topology extraction logic,
- EventBus-specific artifact generation,
- EventBus extractor validation and dry-build quality checks.

This freeze does **not** include narration integration work.

## Artifact Path
- `runtime/.cache/code_intelligence_graph_motadata/eventbus_topology_mapping.v1.json`

## Extraction Guarantees
- Deterministic static extraction of EventBus calls:
  - `publish(...)`
  - `send(...)`
  - `request(...)`
  - `consumer(...)`
  - `localConsumer(...)`
  - `@ConsumeEvent(...)`
- No inferred chains; only direct evidence-backed edges.
- EventBus constants resolution for resolvable constant forms.
- Explicit unknown emission for unresolved/dynamic address tokens.
- Explicit unresolved enclosing symbol marker when method ownership is not structurally provable:
  - `__unresolved_static_or_lambda_context__`

## Validation Summary (Current Frozen State)
- `bad_method_name_count = 0`
- `warnings = []`
- no bogus method names (`JsonObject`, `if`, `File`) in extracted edges
- unknowns remain explicit and typed (not hidden)

## Real Motadata Dry-Build Stats
From latest real-workspace dry build against Motadata:

- `edge_count = 1211`
- `unknown_count = 409`
- `resolved_address_count = 1192`
- `unresolved_address_count = 27`
- `dynamic_address_count = 382`
- `unknown_type_counts = {"DYNAMIC_ADDRESS": 382, "UNRESOLVED_ADDRESS": 27}`
- `address_kind_distribution = {"runtime": 1156, "test": 69, "control": 5, "websocket": 4, "unknown": 412}`

## Known Unknowns (Explicit by Design)
- `DYNAMIC_ADDRESS`
  - address expression is runtime-composed and not statically resolvable.
- `UNRESOLVED_ADDRESS`
  - constant/token cannot be resolved with deterministic static context.
- `__unresolved_static_or_lambda_context__`
  - enclosing symbol is not structurally provable in current static pass (for example static/lambda-like context).

These are retained as explicit outputs to preserve evidence integrity.

## Explicit Non-Goals (Freeze Boundary)
- No Ask/Debug/Plan/Code integration yet.
- No inferred chains.
- No cross-subsystem interaction composition yet.

## Acceptance Result
EventBus Topology Map v1 is **frozen for controlled integration planning**.

Next step is planning-only:
- EventBus -> `reasoning_context` integration design and safety gates.
