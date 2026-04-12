"""
v1 freeze: strict schema, selection_reason enum, golden fingerprint, identity policy.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.layer5.evidence.identity_policy import EVIDENCE_IDENTITY_MISMATCH_CODE, IdentityMismatchError
from runtime.layer5.evidence.fingerprint import bundle_masked_fingerprint_sha256, masked_bundle_dict
from runtime.layer5.evidence.schema_validate import EvidenceSchemaValidationError, validate_evidence_bundle_dict
from runtime.layer5.evidence.selection_reason import FROZEN_SELECTION_REASONS, parse_selection_reason
from runtime.layer5.index import build_file_index
from runtime.layer5.retrieval import LexicalRetrievalConfig, retrieve_lexical
from runtime.layer5.evidence import SnippetConfig, build_evidence_bundle
from runtime.layer5.workspace.identity import WorkspaceIdentity

_LAYER5 = Path(__file__).resolve().parents[1]
_GOLDEN = _LAYER5 / "evidence" / "golden"
_FIXTURE_ROOT = _GOLDEN / "fixture_workspace"


def _golden_bundle():
    root_s = str(_FIXTURE_ROOT.resolve())
    ident = WorkspaceIdentity(
        canonical_root=root_s,
        identity_hash=WorkspaceIdentity.compute_identity_hash(root_s),
        original_input=root_s,
        path_type="posix",
        is_git_repo=False,
    )
    idx = build_file_index(ident)
    r = retrieve_lexical(idx, "hello", top_k=1, config=LexicalRetrievalConfig())
    return build_evidence_bundle(
        r,
        idx,
        snippet_config=SnippetConfig(context_lines_before=2, context_lines_after=2),
    )


class TestSelectionReasonEnum:
    def test_parse_accepts_all_frozen_values(self):
        for v in sorted(FROZEN_SELECTION_REASONS):
            assert parse_selection_reason(v).value == v

    def test_parse_rejects_unknown(self):
        with pytest.raises(ValueError, match="invalid selection_reason"):
            parse_selection_reason("not_a_real_reason")


class TestStrictSchema:
    def test_valid_bundle_passes(self):
        b = _golden_bundle()
        validate_evidence_bundle_dict(json.loads(b.to_json()))

    def test_rejects_extra_top_level_key(self):
        b = _golden_bundle()
        d = json.loads(b.to_json())
        d["extra_field"] = 1
        with pytest.raises(EvidenceSchemaValidationError, match="additional property"):
            validate_evidence_bundle_dict(d)

    def test_rejects_wrong_selection_reason(self):
        b = _golden_bundle()
        d = json.loads(b.to_json())
        d["entries"][0]["snippet"]["selection_reason"] = "bogus_reason"
        with pytest.raises(EvidenceSchemaValidationError, match="not in enum"):
            validate_evidence_bundle_dict(d)

    def test_rejects_provisional_true(self):
        b = _golden_bundle()
        d = json.loads(b.to_json())
        d["provisional"] = True
        with pytest.raises(EvidenceSchemaValidationError, match="const"):
            validate_evidence_bundle_dict(d)

    def test_schema_enum_matches_code_enum(self):
        schema_path = _LAYER5 / "evidence" / "evidence_bundle.v1.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        enum_vals = schema["definitions"]["snippet"]["properties"]["selection_reason"]["enum"]
        assert frozenset(enum_vals) == FROZEN_SELECTION_REASONS


class TestGoldenFixture:
    def test_masked_bundle_matches_golden_file(self):
        b = _golden_bundle()
        expected = json.loads((_GOLDEN / "evidence_bundle.v1.masked.json").read_text(encoding="utf-8"))
        assert masked_bundle_dict(b) == expected

    def test_fingerprint_sha256_stable(self):
        b = _golden_bundle()
        expected = (_GOLDEN / "evidence_bundle.v1.fingerprint.sha256").read_text(encoding="utf-8").strip()
        assert bundle_masked_fingerprint_sha256(b) == expected


class TestIdentityPolicy:
    def test_mismatch_error_has_stable_code(self):
        from types import SimpleNamespace

        b = _golden_bundle()
        r = SimpleNamespace(
            query_raw=b.query_raw,
            query_tokens=b.query_tokens,
            top_k=b.top_k,
            hits=(),
            index_schema_version=b.index_schema_version,
            workspace_identity_hash="0" * 64,
        )
        bad_index = SimpleNamespace(
            schema_version=b.index_schema_version,
            workspace_identity_hash=b.workspace_identity_hash,
            canonical_root=b.canonical_root,
            files=(),
        )
        with pytest.raises(IdentityMismatchError) as exc:
            build_evidence_bundle(r, bad_index, require_identity_match=True)
        assert EVIDENCE_IDENTITY_MISMATCH_CODE in str(exc.value)

    def test_require_identity_match_false_skips_check(self):
        from types import SimpleNamespace

        b = _golden_bundle()
        idx = SimpleNamespace(
            schema_version=b.index_schema_version,
            workspace_identity_hash=b.workspace_identity_hash,
            canonical_root=b.canonical_root,
            files=(),
        )
        r = SimpleNamespace(
            query_raw=b.query_raw,
            query_tokens=b.query_tokens,
            top_k=b.top_k,
            hits=(),
            index_schema_version=b.index_schema_version,
            workspace_identity_hash="deadbeef" * 8,
        )
        out = build_evidence_bundle(r, idx, require_identity_match=False)
        assert out.workspace_identity_hash == "deadbeef" * 8
