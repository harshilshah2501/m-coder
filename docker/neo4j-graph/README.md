# Neo4j Graph Stack

This stack runs a local Neo4j instance plus a managed Java AST refresh loop for the Motadata workspace.

## What it does

- Starts Neo4j with persistent volumes.
- Waits for Neo4j health before indexing.
- Rebuilds the Java graph when the mounted Motadata Java tree changes.
- Uses full-reset ingest for consistency, so deleted classes do not linger in the graph.
- Writes a simple last-success state file used by the refresh container health check.

## Configure

Copy `.env.example` to `.env` in this directory and adjust `GRAPH_MOTADATA_ROOT` if needed.

## Commands

From repo root:

```bash
./scripts/graph_stack.sh up
./scripts/graph_stack.sh status
./scripts/graph_stack.sh logs
./scripts/graph_stack.sh refresh
./scripts/graph_stack.sh down
```

## Notes

- Neo4j is exposed on `127.0.0.1:7687` and `127.0.0.1:7474`.
- The refresh service mounts the repo read-only and the Motadata checkout read-only.
- For manual one-shot ingest outside Docker, `tools/ast_indexer/ingest_java_graph.py --reset` now clears stale graph nodes before loading the current workspace snapshot.