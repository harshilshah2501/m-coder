# Snapshot Identity Correctness Fix (2026-04-06)

## Problem (old behavior)

`workspace_identity_hash` was path-based (`canonical_root` hash), not content/snapshot-based.
This allowed the same workspace root to reuse stale in-process indexes after content changed,
which could diverge local proof runs vs HTTP `export_evidence` behavior over time.

## New behavior

Retrieval/export now carries snapshot-aware identity metadata derived from workspace state:

- Path identity remains: `workspace_identity_hash` (canonical-root hash, unchanged semantics).
- Snapshot identity added: `workspace_snapshot_hash`.
- Snapshot source added: `workspace_snapshot_source`.
- Dirty marker added: `workspace_is_dirty`.
- Commit metadata added when available: `workspace_commit_sha`.

Snapshot fingerprint policy:

1. Git repo, clean tree:
- source: `git_head_clean`
- fingerprint basis: `git:<HEAD_SHA>:clean`

2. Git repo, dirty tree:
- source: `git_head_dirty_manifest_v1`
- fingerprint basis: `git:<HEAD_SHA>:dirty:<manifest_sha256>`
- manifest fields: relative path + size + mtime(ns)
- cache bypassed by default while dirty

3. Non-git workspace:
- source: `manifest_v1`
- fingerprint basis: `manifest:<manifest_sha256>`
- manifest fields: relative path + size + mtime(ns)

## Cache alignment

Context Layer in-process index cache key is now snapshot-based:

- key: `canonical_root + workspace_snapshot_hash`
- same root + same snapshot => cache hit allowed
- same root + changed snapshot => miss (stale entry not reused)
- dirty git workspace => deterministic cache bypass

## Validation added

Targeted tests were added in runtime test suite to prove:

- local retrieval and export share snapshot identity on same snapshot
- changed snapshot forces identity change and cache miss
- dirty git state is reflected and bypasses cache
- fixed snapshot repeated export is reproducible
- no-cache path still works as before
