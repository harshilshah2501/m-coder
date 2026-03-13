# Stage-7 Compiler Parsing Contract v1.0

**Deterministic, Failure-Forward**

This contract defines how the Stage-7 deterministic compiler MUST parse canonical doctrine and produce JSONL rows conforming to `dataset_schema.json`. No heuristics, no LLM calls, no best-effort parsing. Any structural ambiguity or missing required section MUST abort compilation.

---

## A) Inputs and Immutability

### Default Input Path

When no override is provided, the compiler uses:

- `ml/training/pipeline/STAGE4_VARIANT_GENERATION.md`

### Override Mechanism

A single override path MAY be supplied via configuration (e.g. `--doctrine <path>` or `config.doctrine_path`). If an override is provided, the default path is ignored. Exactly one doctrine file is permitted per compilation run. No multiple doctrine inputs or directory scanning is allowed.

### Immutability

- The compiler reads doctrine as **read-only**.
- The compiler **never edits** the doctrine file.
- Any mismatch versus the expected structure defined below **aborts** compilation.

### SHA256 and Encoding

- `doctrine_sha256` MUST be computed on **raw bytes** of the selected doctrine file (no newline normalization).
- Doctrine MUST be decoded as **UTF-8**; invalid UTF-8 **aborts** compilation.
- The compiler MUST record the actual selected doctrine path in `source.doctrine_file`.

---

## B) Deterministic Ordering Guarantees

Output JSONL row order MUST be:

- BASE-001 V1, V2, V3, V4
- BASE-002 V1, V2, V3, V4
- ...
- BASE-025 V1, V2, V3, V4

- **Base ordering:** Numeric ascending on the 3-digit base number (001..025).
- **Variant ordering:** Ascending on V index (V1, V2, V3, V4).

---

## C) Base and Variant Segmentation Rules (Exact)

### Base Header

A base section header line MUST match exactly:

```
/^##\s+BASE-(\d{3})\s+Variants\s*$/
```

### Variant Header

A variant section header line MUST match exactly:

```
/^###\s+BASE-(\d{3})-V([1-4])\s*$/
```

### Rules

1. Every base section MUST contain **exactly 4 variant sections** (V1..V4); no duplicates, no missing.
2. All variant headers' base id MUST match the enclosing base section's base id; otherwise **abort**.
3. Total bases MUST equal **25** (BASE-001..BASE-025); if not, **abort**.
4. No extra bases outside BASE-001..BASE-025; **abort**.

---

## D) Section Extraction Rules per Variant (Exact)

Within each variant section, the following sub-section labels MUST exist **exactly once** and in this **exact order** (case sensitive):

1. `**Context:**`
2. `**Boundary Phrase:**`
3. `**Phase:**`
4. `**Response Posture:**`
5. `**Allow:**`
6. `**Block at Boundary:**`
7. `**Validation:**`

### Parsing Rules

- Text for a section is everything after its label line until the next label line (or end of variant block).
- Empty or whitespace-only section text is **forbidden**; **abort**.
- Trailing whitespace trimmed; leading whitespace preserved except for uniform indentation stripping (see Section G).
- A label appearing inside content is allowed ONLY if it is not on a standalone line matching the exact label pattern; otherwise **abort** (prevents accidental nested headings).

---

## E) Field Mapping to dataset_schema.json (Exact)

For each variant, emit one JSON object with:

| Field | Source | Notes |
|-------|--------|-------|
| `base_id` | From base/variant headers | `"BASE-###"` (3 digits) |
| `variant_id` | From variant header | `"V1"`..`"V4"` |
| `phase` | Phase section | Uppercased; must be exactly REF, CONF, DES, MIX, or CODE; else **abort** |
| `instruction` | Context section | After normalization (Section G) |
| `response.posture` | Response Posture section | |
| `response.allow` | Allow section | |
| `response.block` | Block at Boundary section | |
| `response.validation` | Validation section | |
| `boundary_phrase` | Boundary Phrase section | Display form (trimmed); see G |
| `invariants` | Extracted from Response Posture | See Section F |
| `boundary_hash` | SHA256 of normalized boundary | See Section G |
| `ids.sample_id` | Constructed | `"BASE-###-V#"` |
| `ids.phase_id` | Must equal `phase` | |
| `source.doctrine_file` | Selected doctrine path (default or override) | |
| `source.doctrine_sha256` | SHA256 hex of doctrine raw bytes | |
| `source.compiler_version` | Fixed | `"stage7-compiler-v1.0"` |
| `source.compiled_at_utc` | Timestamp | ISO 8601 UTC ending with `Z` |

`additionalProperties` MUST remain `false` per schema. No extra top-level or nested properties.

---

## F) Invariant Extraction Rules (Deterministic, No Heuristics)

Invariants are explicit bullet lines inside the **Response Posture** section ONLY.

### Accepted Formats (Exact)

- Lines beginning with `- ` OR `* ` OR `• ` are candidates.
- An invariant line MUST contain the token `INVARIANT:` (case sensitive) to qualify.

Example:
```
- INVARIANT: Unknown → block.
```

### Rules

- Extract the substring after `INVARIANT:` and trim.
- The `invariants` array MUST contain at least 1 entry; otherwise **abort**.
- Duplicates are removed only if identical after normalization; if removal leads to an empty array, **abort**.

---

## G) Normalization Rules (Minimal and Deterministic)

### 1) Line Endings

- When computing `doctrine_sha256`: use raw file bytes; **no** line-ending normalization.
- For parsing: decode to text and normalize line endings to `\n` for internal processing only.

### 2) Section Text Trimming

- Remove leading and trailing blank lines from each section.
- Trim trailing spaces per line.

### 3) Indentation

- If all non-empty lines in a section share a common leading indentation of N spaces, strip exactly N spaces from each line (uniform deindent).
- Otherwise, preserve indentation.

### 4) boundary_phrase Normalization for boundary_hash

- After section trim, collapse any internal runs of whitespace (spaces/tabs) to a single space.
- Preserve arrows/symbols exactly (e.g. `→`).
- Convert to **NFC** Unicode normalization.
- Compute SHA256 over the UTF-8 bytes of this normalized string; emit as hex.

**Note:** The `boundary_phrase` stored in JSON remains the display form (trimmed) but NOT whitespace-collapsed, unless the schema explicitly requires the normalized form.

---

## H) Failure Conditions (Explicit List)

Compilation MUST abort on any of the following:

1. Missing or extra bases
2. Missing or extra variants (not exactly 4 per base)
3. Variant base id does not match enclosing base id
4. Total bases ≠ 25
5. Bases outside BASE-001..BASE-025
6. Out-of-order section labels
7. Duplicate section labels within a variant
8. Empty or whitespace-only section content
9. Invalid phase (not one of REF, CONF, DES, MIX, CODE)
10. No invariants found (or all removed as duplicates)
11. `boundary_phrase` length &lt; 3 after trim
12. Any SHA computation error
13. Non-UTF-8 input
14. Mismatch between `ids.phase_id` and `phase`
15. JSON serialization failure

---

## I) Compiler Outputs (Contract Only)

Future output paths (for reference):

| Path | Description |
|------|-------------|
| `ml/training/generated/golden_exemplars_v1.jsonl` | One JSON object per line |
| `ml/training/generated/dataset_manifest.json` | Manifest with counts, provenance, schema version |

Outputs are **generated artifacts**; never hand-edited.

---

## J) Appendix

### Exact Regexes (Copy/Paste Ready)

**Base header:**
```
^##\s+BASE-(\d{3})\s+Variants\s*$
```

**Variant header:**
```
^###\s+BASE-(\d{3})-V([1-4])\s*$
```

### Worked Example

**Mini variant block (doctrine):**

```markdown
### BASE-003-V2

**Context:**
When the system detects an anomaly, it must not publish before validation.

**Boundary Phrase:**
publishEvent(data)

**Phase:**
CONF

**Response Posture:**
CONDITIONAL ALLOWANCE – Allow pre-boundary checks.
- INVARIANT: Unknown → block.
Block at irreversible boundary: publishEvent(data)

**Allow:**
- Pre-boundary validation
- Anomaly detection

**Block at Boundary:**
- publishEvent()
- Any alert dispatch

**Validation:**
- Boundary phrase exact match - PASS
```

**Corresponding JSON object shape (fields only):**

```json
{
  "base_id": "BASE-003",
  "variant_id": "V2",
  "phase": "CONF",
  "instruction": "<Context section text>",
  "response": {
    "posture": "<Response Posture text>",
    "allow": "<Allow text>",
    "block": "<Block at Boundary text>",
    "validation": "<Validation text>"
  },
  "boundary_phrase": "publishEvent(data)",
  "invariants": ["Unknown → block."],
  "boundary_hash": "<sha256 hex of normalized boundary>",
  "ids": {
    "sample_id": "BASE-003-V2",
    "phase_id": "CONF"
  },
  "source": {
    "doctrine_file": "ml/training/pipeline/STAGE4_VARIANT_GENERATION.md",
    "doctrine_sha256": "<64 hex chars>",
    "compiler_version": "stage7-compiler-v1.0",
    "compiled_at_utc": "YYYY-MM-DDThh:mm:ss.sssZ"
  }
}
```
