# PR3 Validation and Metrics Note

## 1) What PR-3 adds

PR-3 adds deterministic validation and closure-gate measurement for grounded Ask quality.  
It expands golden query coverage, enriches harness outputs with quality metadata and dominance metrics, and evaluates closure thresholds in a reproducible way.

## 2) Metrics now available

- Dominance: `core_code_pct_top_k`, `code_pct_top_k`, `noise_pct_top_k`
- Outcome distribution: `strong_rate`, `weak_rate`, `insufficient_rate`, `no_match_rate`
- Truthfulness: `false_strong_rate`, `weak_correctness_rate`, `no_match_correctness_rate`, `ambiguity_false_confidence_rate`
- Existing latency/coverage: empty bundle, relevant file presence, retrieval/e2e latency, no-match justification
- Grouped suite summary and per-query outputs with intent/quality/reasons/metrics

## 3) Thresholds defined

Validation-only closure thresholds:

- `MIN_CORE_CODE_PCT_FOR_CODE_INTENT = 0.60`
- `MAX_FALSE_STRONG_RATE = 0.0`
- `MIN_WEAK_CORRECTNESS_RATE = 0.80`
- `MIN_NO_MATCH_CORRECTNESS_RATE = 0.95`

Harness emits deterministic threshold pass/fail under `threshold_results`.

## 4) How to run the harness

```bash
pytest runtime/tests/test_ask_validation_harness.py -v
```

For direct harness invocation in code, use `run_validation_harness(tmp_root)` from `runtime/ask_validation/harness.py`.

## 5) What PR-3 does NOT solve

- It does not change retrieval ranking or quality-gate semantics.
- It does not change evidence bundle schema.
- It does not add embeddings, rerankers, or semantic retrieval.
- It does not include plugin/UI changes.

## 6) Expected next step

Use PR-3 metrics to target retrieval improvements where failures cluster (noise-dominated top-k, low core-code share, missing core-in-top3), then re-run the same deterministic harness to confirm closure progression.
