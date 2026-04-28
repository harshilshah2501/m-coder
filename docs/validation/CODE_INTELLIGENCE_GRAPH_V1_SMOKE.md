# Code Intelligence Graph v1 Smoke Validation

This note records the CI smoke command for deterministic Code Intelligence Graph (CIG) v1 buildability and baseline integrity.

## Scope

- Buildability of CIG v1 artifacts
- Artifact/manifest existence and schema checks
- Integrity gate pass
- Determinism (`content_hash` stable across two builds on same fixture)
- Traversal no-collapse baseline (branched traversal returns multiple paths)

Out of scope:
- Ask-path integration
- Retrieval/Plan-Gate/schema/governance/composer contract changes

## Command

Run:

`make cig-smoke`

Equivalent direct command:

`PYTHONPATH=. pytest -q runtime/tests/test_code_intelligence_graph_smoke.py`

## Pass Criteria

- `code_intelligence_graph.v1.jsonl` exists
- `code_intelligence_graph.v1.manifest.json` exists
- `code_intelligence_graph.v1.adjacency.json` exists
- `manifest.schema_version == "code_intelligence_graph.v1"`
- `manifest.stats.node_count > 0`
- `manifest.stats.edge_count > 0`
- integrity validation passes
- build #1 `content_hash ==` build #2 `content_hash`
- branched traversal exposes multiple call/flow paths (no single-anchor collapse)

