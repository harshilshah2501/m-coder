# M4.1 Slice 1 — Implementation Note (Stages A & B)

**Slice:** Stage A (CanonicalExecutionIntent) + Stage B (CommandNormalizer) + targeted tests.

**Next:** Slice 2 wires these into the live path (handlers, loop_controller, DeterministicGuard, Plan-Gate). See [M4_1_SLICE2_IMPL_NOTE.md](M4_1_SLICE2_IMPL_NOTE.md).

## Files to add (Slice 1)

| File | Purpose |
|------|---------|
| `runtime/integrity/__init__.py` | Package init; export CanonicalExecutionIntent, compute_canonical_hash, CommandNormalizer, NormalizationError |
| `runtime/integrity/canonical_intent.py` | CanonicalExecutionIntent dataclass; serialize_for_hash(); compute_canonical_hash() |
| `runtime/integrity/command_normalizer.py` | CommandNormalizer.normalize(request) → CanonicalExecutionIntent; parse command once; reject malformed |
| `runtime/tests/test_canonical_intent.py` | Schema, serialization, canonical_hash determinism |
| `runtime/tests/test_command_normalizer.py` | Same request → same artifact; env ordering; path normalization; malformed rejected |

## Exact symbols

- **canonical_intent.py:** `CanonicalExecutionIntent` (dataclass), `serialize_for_hash(intent) -> bytes`, `compute_canonical_hash(intent) -> str`
- **command_normalizer.py:** `NormalizationError` (exception), `CommandNormalizer`, `CommandNormalizer.normalize(request: dict) -> CanonicalExecutionIntent`

## Compatibility bridge (Slice 1)

- No callers changed yet. New module is additive. Execute_service and loop_controller will be wired in Slice 2/3.
- Request shape accepted by normalizer: same as current execute_request (request_id, repo_root, command, plan_hash, revision, branch, task_id, env optional; command may be str or list).

## Hash design

- canonical_hash excludes `intent_id` so two intents with same execution content yield same hash (per CANONICAL_EXECUTION_INTENT_v1.md §6.1).
- Fields in hash: request_id, plan_hash, executable, argv, working_dir, env_delta (sorted keys), timeout_seconds, capture_artifacts. Fixed order; JSON with sort_keys for nested dicts.
