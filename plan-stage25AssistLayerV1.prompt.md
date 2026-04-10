## Plan: Stage 2.5 Assist Layer v1 (Tightened)

Assist v1 is an advisory normalization layer that can improve readability and user guidance while being structurally incapable of changing governance meaning, retrieval authority, or execution posture. It preserves the original query as a hard invariant, accepts metadata-only context, and emits explicit observable status on every path.

1. Responsibilities
- Assist Layer v1 DOES:
  - Preserve and carry original_query unchanged on all paths.
  - Optionally produce augmented_query only through conservative deterministic normalization.
  - Produce reason and suggestions as non-authoritative guidance.
  - Emit bounded confidence_enum (none|low|medium), never numeric confidence.
  - Emit explicit assist_status for success and all degradations/failures.
- Assist Layer v1 MUST NOT:
  - Execute tools/commands/code or trigger side effects.
  - Decide policy posture or alter Plan-Gate outcomes.
  - Bypass Plan-Gate routing.
  - Fabricate evidence, symbols, files, classes, causes, or hypotheses.
  - Change task intent/type.
  - Consume raw code or unstructured repository text.

Augmentation policy boundary (hard policy)
- Allowed transforms (deterministic only):
  - Whitespace normalization: collapse repeated spaces, trim leading/trailing whitespace.
  - Punctuation normalization: remove duplicated punctuation artifacts and normalize spacing around punctuation.
  - Typo-light normalization: deterministic correction of obvious keyboard-adjacent single-token typos only when unambiguous.
  - Deterministic abbreviation expansion: expand only approved static abbreviations from a fixed map (for example repo->repository, cfg->config) with no semantic branching.
  - Neutral repo-scope qualifier append only when already implied by explicit user text or explicit metadata task scope (for example "in this workspace").
- Forbidden transforms:
  - Adding unstated symbols, files, modules, classes, APIs, stack traces, or root causes.
  - Changing task type (for example explain->fix, where->why, debug->plan).
  - Introducing new hypotheses or technical claims.
  - Adding unstated constraints, deadlines, environments, or ownership assumptions.
  - Resolving ambiguity into specific choices not present in user input/metadata.
  - Reordering multi-part requests in a way that changes priority or meaning.

2. Boundaries
- Start:
  - After Plugin receives user query and identifiers, before Plan-Gate invocation.
- Stop:
  - After emitting advisory object with original_query, optional augmented_query, reason, suggestions, confidence_enum, assist_status.
- Plugin interaction:
  - Plugin remains thin client; renders Assist output as guidance only.
  - Plugin sends both original_query and augmented_query (if present) to downstream path.
- Context Layer interaction:
  - Assist reads metadata-level context only.
  - Allowed v1 context fields:
    - active_file_path
    - evidence_file_paths_or_ids
    - selector_names_used
    - task_type_label
    - evidence_presence_or_count
    - diagnostics_labels (already structured labels only)
  - Disallowed v1 context inputs:
    - raw snippets
    - code bodies
    - free-form repository text
    - raw unstructured logs
- Plan-Gate interaction:
  - Plan-Gate always receives original_query.
  - augmented_query is advisory-only adjunct.
  - Assist cannot alter Plan-Gate contract semantics, routing invariants, or outcomes.

3. Data Flow
1. User submits query in Plugin.
2. Plugin creates/propagates request_id, trace_id, session_id.
3. Plugin sends request to Assist with original_query and allowed metadata-only context.
4. Assist validates input envelope and context field allowlist.
5. Assist applies deterministic augmentation policy:
  - If allowed transform applies, set augmented_query.
  - If not, set augmented_query equal to original_query.
6. Assist derives reason and template-based suggestions from allowed sources only.
7. Assist sets confidence_enum (none|low|medium) and assist_status.
8. Assist emits observability event.
9. Plugin forwards original_query plus assist advisory block to Plan-Gate path.
10. Plan-Gate executes unchanged governance logic.
11. Final response includes unchanged governed outcome plus Assist metadata.

What is modified:
- Additive assist advisory metadata only.

What is untouched:
- Original query text, Plan-Gate authority, retrieval contracts, governance semantics, execution semantics.

Original-query invariant (hard)
- original_query is always preserved byte-for-byte as received after transport decoding.
- original_query is always logged (or hashed/redacted per policy) as the canonical user input.
- original_query is always available to Plan-Gate.
- Assist failure/uncertainty never erases, replaces, or blocks original_query.

4. Failure Modes
- Empty/insufficient metadata context:
  - Behavior: passthrough original_query; augmented_query=original_query; suggestions limited to clarification templates.
  - Status: degraded_empty_context.
- Invalid input envelope:
  - Behavior: passthrough original_query; no augmentation; structured error details in assist metadata.
  - Status: input_invalid.
- Timeout/internal Assist failure:
  - Behavior: passthrough original_query unchanged; explicit assist_error metadata.
  - Status: timeout_or_internal_error.
- Policy violation detected in candidate augmentation:
  - Behavior: reject candidate; fallback to original_query.
  - Status: blocked_by_policy.

Hard runtime behavior invariants
- On any Assist failure/degradation, governed core path continues unchanged.
- Assist cannot block the main path.
- No silent drop; assist_status is always emitted.
- No mutation of governance contracts/outcomes.

5. Observability
- Trace propagation:
  - request_id, trace_id, session_id must be identical across Plugin, Assist, Plan-Gate handoff.
- Required Assist event fields:
  - event_name=assist_layer_event
  - timestamp_utc
  - request_id
  - trace_id
  - session_id
  - assist_version
  - assist_status
  - confidence_enum
  - reason_code
  - transform_codes_applied (array)
  - suggestions_source_tags (array)
  - latency_ms
  - input_hash
  - input_hash_scope
  - canonicalization_version
  - error_class (nullable)
- input_hash definition (exact):
  - Scope for v1: hash(original_query_canonicalized) only.
  - Canonicalization rule v1:
    - UTF-8 encode
    - Unicode NFC normalization
    - convert CRLF to LF
    - trim trailing whitespace per line
    - preserve case and token order
  - Hash algorithm: SHA-256 hex.
  - Reason: stable request correlation without granting Assist extra semantic authority from metadata mixing.
- Step-level events:
  - validate_input
  - validate_context_allowlist
  - apply_deterministic_transforms
  - generate_suggestions_from_templates
  - emit_assist_result
  - forward_to_plan_gate

6. API Contract
- Assist input (internal additive envelope):
  - request_id: string (required)
  - trace_id: string (required)
  - session_id: string (optional)
  - original_query: string (required)
  - context_meta: object (optional, allowlisted keys only)
  - task_type_label: string (optional)
- Assist output:
  - request_id: string (required)
  - trace_id: string (required)
  - original_query: string (required, unchanged)
  - augmented_query: string (required, equals original_query when no safe transform)
  - reason: string (required)
  - suggestions: array<string> (required, empty allowed)
  - confidence_enum: string (required; none|low|medium)
  - assist_status: string (required; ok|degraded_empty_context|input_invalid|timeout_or_internal_error|blocked_by_policy)
  - transform_codes_applied: array<string> (required, empty allowed)
  - suggestion_sources: array<string> (required; values only from user_input|context_meta|static_template)
  - errors: array<object> (optional)

Contract constraints
- original_query is mandatory on input and output.
- No float confidence field in v1.
- Additive only; no breaking changes to existing governed contracts.

7. Implementation Plan
- Phase A: Policy and schema hardening
  1. Define deterministic transform allowlist and forbidden list in spec.
  2. Define context_meta allowlist and explicit disallow list.
  3. Define confidence_enum and assist_status enums.
- Phase B: Integration (no refactor)
  4. Add a single Assist hook before Plan-Gate.
  5. Ensure downstream payload always carries original_query.
  6. Ensure Assist output is advisory-only metadata.
- Phase C: Observability hardening
  7. Emit required assist event fields including transform_codes_applied and suggestion_sources.
  8. Enforce input_hash canonicalization versioning.
- Phase D: Documentation and UX constraints
  9. Document non-authoritative labeling and original-vs-augmented visibility.
  10. Document policy boundary examples and forbidden cases.

No-refactor rule
- No Plan-Gate logic change.
- No Context retrieval behavior change.
- No code/snippet ingestion by Assist.
- No multi-step assist refinement loops.
- No new background subsystem.

8. Risks
- Residual risk: deterministic typo correction may still alter nuance.
  - Control: strict unambiguous-only typo policy; else no-op.
- Residual risk: suggestions perceived as recommendations with authority.
  - Control: source tags + non-authoritative UI label + no directive wording templates.
- Residual risk: retrieval impact from subtle query normalization.
  - Control: retrieval-drift validation gate and strict fail criteria.
- Residual risk: policy creep in future versions.
  - Control: versioned allowlists, explicit v1 scope lock, change-control reviews.

9. Validation Plan
- A. Contract and invariant tests
  - Verify original_query preserved end-to-end and present in all downstream envelopes.
  - Verify augmented_query equals original_query when no allowed deterministic transform applies.
  - Verify confidence is enum-only and never numeric.
- B. Policy-boundary tests
  - Positive tests for each allowed transform code.
  - Negative tests for each forbidden transform category.
  - Ensure blocked_by_policy status on forbidden candidate transforms.
- C. Suggestion-source provenance tests
  - Verify each suggestion has valid source tag user_input/context_meta/static_template.
  - Fail if suggestion references unstated files/symbols/facts.
- D. Failure-path invariants
  - Inject timeout, invalid input, empty context, internal errors.
  - Assert main governed path continues, original_query unchanged, explicit assist_status emitted.
- E. Retrieval drift / evidence impact validation (new mandatory gate)
  - Run fixed benchmark suite comparing baseline (no Assist transform) vs Assist-enabled.
  - Compare top-k evidence set overlap and grounding outcome parity.
  - Acceptable drift policy v1:
    - No decrease in grounding-pass rate.
    - Top-k overlap must remain above fixed threshold (for example >=0.9 Jaccard on controlled suite).
    - No increase in unsupported-claim incidents.
  - Fail conditions:
    - Statistically significant drop in grounding metrics.
    - Meaningful top-k divergence tied to Assist transforms.
    - Any increase in governance-mismatch or hallucination flags.
- F. Observability completeness tests
  - Verify required assist event fields always present.
  - Verify input_hash reproducibility under canonicalization v1.

PASS criteria
- Zero violations of original-query invariant.
- Zero forbidden transforms accepted.
- Zero silent Assist failures.
- Governance outcomes unchanged relative to control.
- Retrieval drift gate passes all thresholds.

FAIL criteria
- Any missing original_query downstream.
- Any unstated symbol/file/hypothesis introduced by Assist.
- Any numeric confidence output.
- Any Assist path that blocks governed core flow.
- Any retrieval drift failure against fixed policy thresholds.

## Revision Summary
- Tightened:
  - Deterministic-only augmentation allowlist and explicit forbidden transform policy.
  - Hard original_query invariant across processing, logging, and Plan-Gate availability.
  - Metadata-only context scope with explicit disallow list (no raw code/snippets/log text).
  - Suggestion provenance policy limited to user_input/context_meta/static_template.
  - Confidence changed from float to bounded enum none|low|medium.
  - Failure behavior formalized as non-blocking passthrough with mandatory assist_status.
  - Added strict retrieval drift/evidence impact gate.
  - input_hash now precisely defined and canonicalized.
- Risk removed:
  - Reduced hidden semantic rewrites and indirect retrieval authority.
  - Reduced false authority from numeric confidence precision.
  - Reduced hallucination risk from broad context/suggestion sourcing.
- Intentionally deferred:
  - Any code/snippet-aware Assist behavior.
  - Any LLM-heavy or multi-step refinement behavior.
  - Any expansion beyond advisory v1 scope.