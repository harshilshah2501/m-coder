# RETRIEVAL_DOMINANCE_POLICY_IMPLEMENTATION_PLAN

## 1. Executive Summary

This slice introduces a deterministic retrieval control layer that makes Motadata AIOps grounding trustworthy before any advanced retrieval intelligence work. The goal is to ensure code-intent asks are backed by AIOps implementation-dominant evidence, with explicit weak/insufficient detection and hard refusal paths when grounding quality is not acceptable.

This is a production-slice quality gate, not a retrieval architecture rewrite.

---

## 2. Scope

### In Scope

- Deterministic file classification policy, including subsystem awareness.
- Deterministic query intent classification.
- Deterministic ranking bias and path priors for AIOps code dominance.
- Code-vs-noise dominance policy and diversity constraints.
- Query normalization upgrades for identifier-aware lexical retrieval.
- Weak-evidence detection and quality labeling.
- No-match / insufficient-evidence behavior definitions.
- Validation harness expansion with success and failure probes.

### Out of Scope

- Embeddings / vector search.
- Learned rerankers.
- SFT / LoRA model changes.
- Broad semantic retrieval redesign.
- Plugin UX and front-end interaction changes.

---

## 3. Current Implementation Map

### Indexing

- **Path:** `runtime/layer5/index/builder.py`
- **Function/Class:** `build_file_index`, `index_matches_workspace`
- **Role:** Deterministic workspace file walk and file-level index build.
- **Likely Change Surface:** Optional index-time classification hooks or downstream classification utility usage.

- **Path:** `runtime/layer5/index/config.py`
- **Function/Class:** `FileIndexConfig`
- **Role:** Directory-level traversal pruning and symlink policy.
- **Likely Change Surface:** Deterministic exclusion inputs for noise-heavy directories.

### Retrieval Scoring and Query Normalization

- **Path:** `runtime/layer5/retrieval/lexical.py`
- **Function/Class:** `retrieve_lexical`, `_score_entry`
- **Role:** Lexical scoring by path/basename/content substring counts with deterministic ordering.
- **Likely Change Surface:** Add policy components (`path_prior`, `subsystem_boost`, `noise_penalty`, `module_bias`) and post-ranking diversity correction.

- **Path:** `runtime/layer5/retrieval/query.py`
- **Function/Class:** `normalize_query`
- **Role:** Basic lowercased alphanumeric token extraction.
- **Likely Change Surface:** Deterministic identifier-aware normalization and stopword suppression.

- **Path:** `runtime/layer5/retrieval/models.py`
- **Function/Class:** `RetrievalHit`, `RetrievalResult`
- **Role:** Ranked hit model with score and breakdown.
- **Likely Change Surface:** Extend breakdown fields for policy transparency.

- **Path:** `runtime/layer5/retrieval/config.py`
- **Function/Class:** `LexicalRetrievalConfig`
- **Role:** Lexical weight controls and content read cap.
- **Likely Change Surface:** Add deterministic policy and threshold config values.

### Evidence Bundling and Contract

- **Path:** `runtime/layer5/evidence/builder.py`
- **Function/Class:** `build_evidence_bundle`
- **Role:** Builds evidence bundle from retrieval output while preserving A5 ranking authority.
- **Likely Change Surface:** Keep ranking authority unchanged; no dominance logic here.

- **Path:** `runtime/layer5/evidence/models.py`
- **Function/Class:** `EvidenceBundle`, `EvidenceEntry`
- **Role:** v1 evidence dataclasses.
- **Likely Change Surface:** No changes in this slice unless contract bump is explicitly approved.

- **Path:** `runtime/layer5/evidence/evidence_bundle.v1.schema.json`
- **Role:** Strict schema for evidence bundle v1.
- **Likely Change Surface:** No change for this slice (quality metadata remains outside bundle).

### Ask Validation and Runtime Behavior

- **Path:** `runtime/ask_service/evidence_bridge.py`
- **Function/Class:** `try_build_layer5_evidence`, `context_bundle_from_evidence_dict`
- **Role:** Bridges retrieval output/evidence into ask context path.
- **Likely Change Surface:** Pass quality metadata from retrieval policy layer to ask response.

- **Path:** `runtime/ask_service/handlers.py`
- **Function/Class:** `handle_ask_request`, `_build_plan_only_response`
- **Role:** Handles ask request, evidence-first flow, and response formation.
- **Likely Change Surface:** Enforce quality-based reasoning guard and refusal-style behavior for insufficient/no-match.

- **Path:** `runtime/ask_service/v1_ingest.py`
- **Function/Class:** `handle_ask_v1_request`
- **Role:** v1 evidence ingest path with schema checks and planning response.
- **Likely Change Surface:** Apply quality gate and hard block behavior for insufficient/no-match.

### Validation Harness

- **Path:** `runtime/ask_validation/harness.py`
- **Function/Class:** `AskValidationHarness`
- **Role:** Golden query execution and metric aggregation.
- **Likely Change Surface:** Add dominance, weak-evidence correctness, and failure-probe metrics.

- **Path:** `runtime/ask_validation/golden_queries.py`
- **Role:** Current golden query set.
- **Likely Change Surface:** Add AIOps-focused and adversarial failure-case query sets.

---

## 4. Proposed Retrieval Dominance Policy

### 4.1 Deterministic Intent Classifier

Introduce new module:

- `runtime/layer5/retrieval/intent.py`

Output enum:

- `CODE_INTENT`
- `DEBUG_INTENT`
- `PLAN_INTENT`
- `GENERIC_INTENT`

Deterministic signal precedence:

1. Identifier/symbol patterns (CamelCase, snake_case, method-like tokens, package-like strings) -> strong code signal.
2. Code verbs (`where implemented`, `class`, `function`, `method`, `module`) -> `CODE_INTENT`.
3. Debug verbs (`why failing`, `error`, `exception`, `not working`, `traceback`) -> `DEBUG_INTENT`.
4. Change verbs (`plan`, `change`, `update`, `add`, `modify`, `refactor`) -> `PLAN_INTENT`.
5. Otherwise -> `GENERIC_INTENT`.

Guardrail application rule:

- Dominance guardrails apply only to `CODE_INTENT`, `DEBUG_INTENT`, and `PLAN_INTENT`.
- `GENERIC_INTENT` does not trigger strict dominance failure, but still emits quality metadata.

### 4.2 File and Subsystem Classification

Introduce deterministic file classing utility (proposed `runtime/layer5/retrieval/policy.py`).

Top-level classes:

- `core_aiops_code`
- `supporting_prod_code`
- `config`
- `tests`
- `logs`
- `vendor_static`
- `generated_metrics_data`

For `core_aiops_code`, add subsystem labels:

- `alerting`
- `correlation`
- `topology`
- `ingestion`
- `metrics`
- `unknown`

Classification inputs (first-match deterministic rule order):

- Path prefixes and package structure.
- Folder names.
- Stable keyword maps.
- Extension and filename patterns.

### 4.3 Ranking and Post-Ranking Policy

Scoring framework:

`final_score = lexical_score + path_prior + subsystem_boost + module_bias + symbol_boost - noise_penalty`

Components:

- `lexical_score`: Existing deterministic lexical path/basename/content score.
- `path_prior`: Boost core AIOps paths, moderate support-code boost, penalties for tests/logs/vendor/generated data.
- `subsystem_boost`: If query tokens map to a subsystem, boost files in matching subsystem.
- `module_bias`: Prefer same-package/same-module proximity when detectable from query or selected file hints.
- `symbol_boost`: Exact/normalized identifier matches in basename/path/content.
- `noise_penalty`: Strong negative weights for noise classes.

Post-ranking diversity correction (deterministic):

- For intent-gated queries, `top_3` must include at least one `core_aiops_code` hit.
- No more than two consecutive noise-class hits in top-k.
- If constraints cannot be satisfied with available candidates, mark quality down (weak or insufficient).

### 4.4 Query Normalization

Deterministic normalization enhancements in `runtime/layer5/retrieval/query.py`:

- Case normalization.
- Symbol literal preservation (keep raw identifier forms).
- CamelCase split while retaining joined form.
- Separator handling across `_`, `-`, `.`, `/`, `:`.
- Stopword suppression using stable list for non-code tokens.
- Short-token retention exceptions for code-like literals and known acronyms.

---

## 5. Weak-Evidence / No-Match Policy

### 5.1 Evidence Quality Labels

Deterministic quality outcomes:

- `STRONG`
- `WEAK`
- `INSUFFICIENT`
- `NO_MATCH`

For intent-gated queries (`CODE/DEBUG/PLAN`), quality is computed from:

- Core-code ratio in top-k.
- Overall code ratio in top-k.
- Noise ratio in top-k.
- Core presence in top-3.
- Diversity rule pass/fail.
- Identifier/symbol hit presence for symbol-heavy queries.

### 5.2 Hard Reasoning Guard (Truthfulness Safety)

Allowed behavior matrix:

- `STRONG`: full reasoning permitted.
- `WEAK`: constrained reasoning permitted with explicit caveats.
- `INSUFFICIENT`: no reasoning; return grounding-failure response.
- `NO_MATCH`: no reasoning; return no-match response.

Enforcement points:

- `runtime/ask_service/handlers.py`
- `runtime/ask_service/v1_ingest.py`

This guard prevents confident generation when evidence quality is below safety threshold.

### 5.3 Metadata Placement

Do not change evidence bundle v1 schema in this slice.

Attach quality metadata at ask response level:

- `metadata.intent_type`
- `metadata.evidence_quality`
- `metadata.quality_reasons`
- `metadata.dominance_metrics`

This preserves contract stability while enabling policy iteration.

---

## 6. Validation Plan

### 6.1 Query Suites

Add deterministic suites:

1. AIOps repository-understanding queries.
2. Debug queries tied to implementation behavior.
3. Plan/change queries requiring grounded file targeting.
4. No-match queries for absent features/symbols.
5. Adversarial ambiguity probes (failure cases), e.g.:
   - `engine`
   - `this not working`
   - `fix bug`
   - `in this system`

Expected behavior for ambiguity probes:

- Must resolve to `WEAK` or `INSUFFICIENT` unless strong code evidence exists.

### 6.2 Before/After Evaluation Method

- Freeze deterministic query fixtures.
- Run baseline on current retrieval policy.
- Run candidate with dominance policy enabled.
- Compare per-query and aggregate metrics.
- Keep deterministic config snapshots for reproducibility.

### 6.3 Metrics

Required metrics:

- `% core_aiops_code files in top-k`
- `% code-class files in top-k`
- `% noise-class files in top-k`
- false positives (noise marked strong)
- false negatives (strong code cases marked insufficient/weak)
- weak-evidence correctness rate
- no-match correctness rate
- ambiguity false-confidence rate

Optional but tracked:

- retrieval latency delta vs baseline
- end-to-end ask latency delta vs baseline

### 6.4 Harness Additions

- Extend `runtime/ask_validation/golden_queries.py` with AIOps + adversarial sets.
- Extend `runtime/ask_validation/harness.py` metrics model for quality outcomes.
- Add retrieval policy unit tests under `runtime/layer5/tests/`:
  - intent classifier determinism
  - file/subsystem classification determinism
  - scoring component correctness
  - diversity correction behavior
  - quality label correctness

---

## 7. Documentation / Roadmap Updates Needed

After implementation (not now), update:

- `docs/LIVE_ROADMAP_TRACKER.md`
- `docs/PRODUCT_SLICE_CHARTER.md`
- `docs/Backend Production Validation Sheet.md`
- `docs/audit/RETRIEVAL_QUALITY_REMEDIATION.md`

Create new policy spec doc after code lands:

- `docs/audit/RETRIEVAL_POLICY.md`

Include:

- class/subsystem rules
- intent classifier rules
- scoring weights and thresholds
- quality reason codes
- validation pass/fail gates

---

## 8. Phased Implementation Sequence

### Phase 1: Deterministic Policy Skeleton (Required for Production Closure)

Scope:

- Add file class + subsystem classifier.
- Add policy config surface and reason-code model.
- Add unit tests for deterministic behavior.

Likely files:

- New: `runtime/layer5/retrieval/policy.py`
- Existing: `runtime/layer5/retrieval/config.py`
- Tests: `runtime/layer5/tests/*`

Risk: Low-Medium (classification misses).
Expected outcome: Stable classification baseline with explicit policy hooks.

### Phase 2: Query Normalization + Scoring (Required for Production Closure)

Scope:

- Upgrade query normalization.
- Add policy score components (`path_prior`, `subsystem_boost`, `module_bias`, `symbol_boost`, `noise_penalty`).
- Keep deterministic tie-breaking.

Likely files:

- `runtime/layer5/retrieval/query.py`
- `runtime/layer5/retrieval/lexical.py`
- `runtime/layer5/retrieval/models.py`
- Tests under `runtime/layer5/tests/`

Risk: Medium (ranking regressions).
Expected outcome: Core AIOps code dominates top-k for code-intent queries.

### Phase 3: Intent + Weak-Evidence Gating + Hard Guard (Required for Production Closure)

Scope:

- Add deterministic intent classifier.
- Add quality gate and diversity constraint pass.
- Enforce hard reasoning guard in ask handlers.

Likely files:

- New: `runtime/layer5/retrieval/intent.py`
- New: `runtime/layer5/retrieval/quality_gate.py`
- `runtime/ask_service/handlers.py`
- `runtime/ask_service/v1_ingest.py`
- `runtime/ask_service/evidence_bridge.py`

Risk: Medium-High (runtime behavior changes).
Expected outcome: System explicitly refuses to over-speak on insufficient grounding.

### Phase 4: Validation Harness and Metrics (Required for Production Closure)

Scope:

- Expand harness query sets and metrics.
- Add adversarial/failure-case probes.
- Set closure thresholds for production gate.

Likely files:

- `runtime/ask_validation/golden_queries.py`
- `runtime/ask_validation/harness.py`
- `runtime/tests/test_ask_validation_harness.py`

Risk: Low-Medium (metric calibration).
Expected outcome: measurable, reproducible evidence of retrieval trustworthiness.

---

## 9. Risks / Open Questions

1. Exact subsystem path maps may vary across deployments; require canonical rulebook.
2. Over-penalization risk for logs/config in debug intent; thresholds need calibrated floor.
3. Generic-intent handling must avoid false refusal while maintaining honesty.
4. v1 response metadata shape needs stable naming to avoid downstream churn.
5. Diversity correction must stay deterministic and cheap under large index sizes.

---

## 10. Recommended First Coding Slice

Implement only the following in PR-1:

- File classification with subsystem labels.
- Ranking score adjustments (`path_prior`, `subsystem_boost`, `noise_penalty`, `symbol_boost`).
- Deterministic unit tests for classification and ranking behavior.

Do not implement quality gating or hard reasoning guard in PR-1.

Rationale:

- Maximum retrieval quality gain with minimal runtime behavior risk.
- Cleanly isolates ranking correctness before introducing refusal semantics.
- Produces immediate measurable signal for top-k dominance targets.

