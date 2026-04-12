# Wave-2 / Wave-2.5 freeze checklist (Layer-5 evidence bundle v1)

## Contract

- [x] `schema_hint` version bumped and documented (`layer5.evidence_bundle.v1`)
- [x] Normative spec matches shipped JSON shape (`evidence_bundle.v1.md`)
- [x] Strict JSON Schema with `$id` (`evidence_bundle.v1.schema.json`, `additionalProperties: false`)
- [x] Byte offset semantics documented (UTF-8 of capped decoded `T`; exclusive `end_byte_utf8`)
- [x] `selection_reason` enum frozen in schema + `selection_reason.py`

## Cross-layer alignment

- [ ] A4 index schema version compatibility matrix written (still optional product doc)
- [ ] A5 ranking rules single canonical link only (minor doc dedup)
- [x] A6 authority rule (no rescoring) in code + `a5_authority_note` + tests

## Operational

- [ ] Max read caps (`max_file_bytes`) agreed for prod vs dev (policy)
- [x] Staleness story documented in v1 spec + existing handoffs
- [ ] PII / secrets handling in snippet text reviewed (security signoff)

## Testing

- [x] Golden bundle fixture + masked JSON + fingerprint SHA-256 + CI test
- [x] Identity-mismatch behavior defined (`IdentityMismatchError` vs `require_identity_match=False`) + tests

## Explicitly deferred (post-freeze candidates)

- Plugin envelope
- Plan-Gate ingestion
- Snippet highlighting columns
- Multi-span evidence per file
