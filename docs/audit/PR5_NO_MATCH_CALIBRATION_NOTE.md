# PR-5 NO_MATCH / INSUFFICIENT Calibration Note

## 1) Failing case buckets (from harness / PR-4)

| Bucket | Example | Issue |
|--------|---------|--------|
| **Fixture vs metric mismatch** | `no_match_k8s_autoscaler` | System returned **WEAK** (generic, empty bundle); `no_match_correct` required **exact NO_MATCH** → false negative. |
| **Logic: empty bundle** | `no_match_quantum_handler` | **CODE_INTENT** with **n=0** paths was **INSUFFICIENT**; semantically “no evidence for this code ask” is **NO_MATCH**. |
| **Logic: symbol miss with files** | Symbol queries with unrelated paths | **NO_SYMBOL_MATCH** was folded into **WEAK** via dominance reasons; symbol-not-in-evidence should be **NO_MATCH**. |
| **Intent punctuation** | `"Explain the highlighted code."` | Token `code.` satisfied **`.` in base** → false **CODE_INTENT** + **NO_SYMBOL_MATCH** → blocked v1 happy path. |

## 2) Semantic rules applied

### `NO_MATCH`

- **Empty path list** (`n == 0`): **CODE_INTENT**, **DEBUG_INTENT**, **PLAN_INTENT** → **NO_MATCH** (nothing to ground on). **GENERIC_INTENT** stays **WEAK** + `QUERY_TOO_GENERIC` (under-grounded, not “absence of entity”).
- **`NO_SYMBOL_MATCH`** with symbol signal and **n > 0**: **NO_MATCH** (requested symbol not present in evidence paths), evaluated **before** the WEAK/dominance branch.
- **`code_count == 0`**, **no symbol**: unchanged **INSUFFICIENT** (noise-only junk, not a clean symbol miss).

### `INSUFFICIENT`

- Unchanged for **noise-only** non-symbol code asks (`code_count == 0`, no symbol).
- Still blocked; not used for “empty bundle + concrete code ask” anymore.

## 3) Code changes

| File | Change |
|------|--------|
| `runtime/layer5/retrieval/quality_gate.py` | `n==0`: generic → **WEAK**; else → **NO_MATCH**. New **elif**: `NO_SYMBOL_MATCH` + symbol → **NO_MATCH** before WEAK. |
| `runtime/layer5/retrieval/intent.py` | Strip trailing `.` from symbol candidate **base** so sentence-ending `code.` is not a dotted identifier. |
| `runtime/ask_validation/harness.py` | `no_match_correct` := `evidence_quality in expected_quality_set` for **NO_MATCH_VALID** queries. |

## 4) Fixture changes

- **`no_match_k8s_autoscaler`**: Comment only — allowed set already included **WEAK**; harness fix makes the metric match semantics.
- **`no_match_quantum_handler`**: Comment only — expects strict **NO_MATCH**; satisfied by gate change.

## 5) Before / after `no_match_correctness_rate`

| | Before PR-5 | After PR-5 |
|---|-------------|------------|
| **Rate** (3 no-match fixtures) | **~0.33** (1/3: only strict `NO_MATCH` counted) | **1.0** |
| **`min_no_match_correctness_rate` threshold** | FAIL | PASS |

## 6) `false_strong_rate`

- Remains **0.0** on full harness run (no relaxation of STRONG criteria).

## 7) What remains open

- **GENERIC** + empty bundle still returns **WEAK** (not blocked); product may still want optional UI treatment — out of PR-5 scope.
- **Out-of-domain** without empty bundle (manifest selects unrelated files) still depends on retrieval/context selection; not redefined here beyond **NO_SYMBOL_MATCH** when a symbol is explicit.

## 8) Tests run

```bash
pytest runtime/layer5/tests/test_intent_and_quality_gate.py \
       runtime/tests/test_ask_validation_harness.py \
       runtime/tests/test_ask_service.py \
       runtime/tests/test_ask_v1_ingest.py -q
```

Threshold computation unchanged; only quality semantics and harness correctness definition changed.
