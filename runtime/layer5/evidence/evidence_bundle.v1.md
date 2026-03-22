# Evidence bundle v1 — normative contract (`layer5.evidence_bundle.v1`)

**Status:** Frozen contract surface for Wave-2.5. Validate payloads with `evidence_bundle.v1.schema.json` (`additionalProperties: false` on bundle, entry, snippet, breakdown).

**Schema identifiers**

- `schema_hint` (payload): constant `layer5.evidence_bundle.v1`
- JSON Schema `$id`: `urn:motadata:layer5:evidence_bundle:v1`

## Authority

- **A5:** `retrieval_score`, `retrieval_breakdown`, and hit **order** are authoritative. A6 must not rescore or reorder from snippet text.
- **Identity:** Default `build_evidence_bundle(..., require_identity_match=True)` raises `IdentityMismatchError` if `RetrievalResult.workspace_identity_hash != WorkspaceFileIndex.workspace_identity_hash`. With `require_identity_match=False`, no check is performed; caller assumes risk.

## Root fields

| Field | Notes |
|-------|--------|
| `provisional` | Must be `false` for v1 |
| `schema_hint` | Must be `layer5.evidence_bundle.v1` |
| `query_raw`, `query_tokens`, `top_k` | Echo A5 |
| `index_schema_version`, `workspace_identity_hash`, `canonical_root` | Echo A4/A5 / index root |
| `a5_authority_note` | Exact const string (see schema) |
| `entries` | Same order as A5 `hits`; `rank` = 0-based index |

## `retrieval_breakdown`

Exactly three integer keys: `path_substrings`, `basename_substrings`, `content_substrings`. No other keys.

## Snippet byte offsets (normative)

Let `raw = read_bytes(path)[:max_file_bytes]` and `T = decode(raw, utf-8, errors="replace")`.

- `start_byte_utf8` / `end_byte_utf8` are measured in **UTF-8 encoding of `T`**, not raw file bytes when replacement occurred.
- `start_byte_utf8` is **inclusive**; `end_byte_utf8` is **exclusive** (half-open interval on bytes of `T.encode("utf-8")`).
- Equivalently: if `s` / `e` are character indices in `T` for the snippet span, `start_byte_utf8 = len(T[:s].encode("utf-8"))`, `end_byte_utf8 = len(T[:e].encode("utf-8"))`.
- Offsets are always within the capped logical text; they do not address bytes beyond `max_file_bytes` of raw read.

## `selection_reason` (frozen enum)

Exact strings only (see `selection_reason.py`):

- `query_token_substring_anchor`
- `no_query_token_in_body_file_start`
- `no_query_tokens_file_start`
- `file_missing`
- `file_unreadable`
- `empty_file`

## Line numbers

`start_line`, `end_line`, `anchor_line` are 1-based inclusive lines in the **capped** decoded text, except `0` for missing-file / unreadable spans where no snippet applies.

## Fingerprint (cross-machine stability)

`bundle_masked_fingerprint_sha256` clears `canonical_root` and `workspace_identity_hash` to `""`, then SHA-256 of canonical JSON (`sort_keys=True`, `separators=(",", ":")`). Golden: `golden/evidence_bundle.v1.masked.json` + `golden/evidence_bundle.v1.fingerprint.sha256`.
