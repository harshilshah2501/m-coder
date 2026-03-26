# PR6 Retrieval Baseline Invariants

PR-6 is closed and locked as the canonical Layer-5 retrieval baseline.

- Baseline policy: `retrieval_policy.v5` (`PR6_CLOSED_BASELINE`)
- Validation repo: `/home/harshil/Projects/Motadata` (WSL)
- Closure metrics: top-1 `10/10`, top-3 `10/10`, mean first-rank `1.00`, noise dominance `0.00`
- Any ranking logic change requires re-validation with the PR-6 closure audit suite.

## Contract Invariants

- Intent-gated retrieval for code/debug queries is required.
- Noise-class content suppression is required for code/debug intent.
- Owner-first ranking is required; broad generic files cannot win top-1 on content mass alone.
- Support/integration/event-handler demotions are part of the closure baseline.
- Main Java production bias is part of the closure baseline.
- Deterministic ranking is mandatory (stable ordering and diagnostics).
- Retrieval must remain lexical/symbol deterministic:
  - no embeddings
  - no AST parser introduction
  - no GPU retrieval path

## Change Control

Before merge of any retrieval ranking modification:

1. Run `pytest runtime/layer5/tests/`.
2. Run `PR6_AIOPS_ROOT=/home/harshil/Projects/Motadata python3 runtime/layer5/audit/pr6_real_repo_audit.py`.
3. Confirm closure metrics remain at PR-6 baseline (10/10 top-1 and top-3, 1.00 mean rank, 0.00 noise).
4. If behavior changes intentionally, bump fixture/policy version and document rationale.
