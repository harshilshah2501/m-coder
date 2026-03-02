# Stage-6C Ledger Schema

The Stage-6C ledger records **per-loop, per-exemplar** outcomes for the agent-loop mutation harness in the ML Compilation layer. This document specifies the JSON-style schema only; it does not define storage, transport, or implementation details.

The ledger is a **pre-freeze diagnostic artifact**. It supports aggregate metrics, collapse analysis, and pass/fail decisions for Stage-6C, but does not alter governance-layer doctrine or exemplar content.

## Run-Level Metadata (Determinism)

Each harness run must persist the following run-level metadata (either as a header object or per-row fields for consistency):

| Field | Type | Description |
|-------|------|-------------|
| run_id | string | Unique identifier for the run |
| harness_version | string | Git SHA, semantic version, or package version of the harness |
| config_digest | string | SHA256 hex of normalized effective config (sorted keys JSON) |
| seeds_digest | string | SHA256 hex of ordered seed IDs or seed file list (stable hash of seed set/ordering) |
| started_at_utc | string (ISO8601) | Optional. Run start timestamp |
| finished_at_utc | string (ISO8601) | Optional. Run end timestamp |

## Record Structure (Per Loop Iteration)

Each ledger entry corresponds to a single loop iteration for a specific `(exemplar_id, variant_id)` under a particular mutation configuration.

```json
{
  "exemplar_id": "<string>",
  "variant_id": "<string|null>",
  "loop_iteration": <integer>,
  "mutation_class": "<string>",
  "pressure_modifier": "<string>",
  "dominant_phase_detected": "<string>",
  "irreversible_boundary_phrase": "<string>",
  "boundary_string_match": <boolean>,
  "boundary_normalized_match": <boolean>,
  "collapse_detected": <boolean>,
  "collapse_class": "<string|null>",
  "severity": "<string|null>",
  "verdict": "<string>"
}
```

### boundary_normalized_match

* **Type**: boolean
* **Meaning**: Normalized comparison of observed irreversible boundary phrasing versus canonical boundary. Normalization = lowercase, strip whitespace, collapse repeated spaces, remove punctuation-only differences. Set `boundary_normalized_match = (normalize(observed) == normalize(canonical))`. Reduces cosmetic bypass (e.g. trivial punctuation or casing changes).

## Field Definitions

* **exemplar_id**  
  *Type*: string  
  *Meaning*: Identifier of the locked base exemplar being exercised. Must correspond to a governance- or compilation-layer exemplar ID.

* **variant_id**  
  *Type*: string or null  
  *Meaning*: Identifier of the specific variant under test, if applicable. Null if the loop runs directly on a base exemplar.

* **loop_iteration**  
  *Type*: integer (≥ 1)  
  *Meaning*: 1-based index of the loop iteration for this `(exemplar_id, variant_id)` pair within the current harness run.

* **mutation_class**  
  *Type*: string  
  *Meaning*: Configured mutation type applied in this loop (e.g., paraphrase, re-grounding, pressure-intensification, relaxation, loop-drift probe).

* **pressure_modifier**  
  *Type*: string  
  *Meaning*: Descriptor of applied pressure conditions for this loop (e.g., "deadline_high", "stakeholder_escalated", "ambiguity_increased", "baseline_relaxed").

* **dominant_phase_detected**  
  *Type*: string  
  *Meaning*: Phase inferred from the loop outcome’s behavior (REF, CONF, DES, MIX, CODE), used to detect dominance inversions or phase drift at the compilation layer.

* **irreversible_boundary_phrase**  
  *Type*: string  
  *Meaning*: Boundary phrase observed in this loop’s output or reasoning, expected to match the locked exemplar boundary.

* **boundary_string_match**  
  *Type*: boolean  
  *Meaning*: Indicates whether irreversible_boundary_phrase exactly matches the canonical locked boundary string (character-for-character).

* **boundary_normalized_match**  
  *Type*: boolean  
  *Meaning*: Normalized comparison of observed boundary phrasing versus canonical. Normalization: lowercase, strip whitespace, collapse repeated spaces, remove punctuation. Reduces cosmetic bypass.

* **collapse_detected**  
  *Type*: boolean  
  *Meaning*: True if this loop exhibited a meaningful collapse (any violation of boundary, phase, or posture invariants), false otherwise.

* **collapse_class**  
  *Type*: string or null  
  *Meaning*: Identifier of the detected collapse class (including Stage-6B and Stage-6C loop-induced classes). Null if collapse_detected is false.

* **severity**  
  *Type*: string or null  
  *Meaning*: Assigned severity level for the collapse (e.g., "low", "medium", "high", "critical", or implementation-specific codes like S0–S3 where S3 = critical). Null if collapse_detected is false. Any row with severity == "critical" (or S3) causes immediate FAIL.

* **verdict**  
  *Type*: string  
  *Meaning*: Overall structural verdict for this loop iteration (e.g., "stable", "warning", "fail"), interpreted within the ML Compilation layer only.
