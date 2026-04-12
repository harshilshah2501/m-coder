"""
A6 — Bounded snippets + evidence bundles (v1) from A5 output.

Normative contract: ``evidence_bundle.v1.md`` / ``evidence_bundle.v1.schema.json``.
"""

from runtime.layer5.evidence.builder import build_evidence_bundle
from runtime.layer5.evidence.config import SnippetConfig
from runtime.layer5.evidence.identity_policy import (
    EVIDENCE_IDENTITY_MISMATCH_CODE,
    IdentityMismatchError,
)
from runtime.layer5.evidence.models import SCHEMA_HINT, EvidenceBundle, EvidenceEntry
from runtime.layer5.evidence.schema_validate import (
    EvidenceSchemaValidationError,
    validate_evidence_bundle_dict,
)
from runtime.layer5.evidence.selection_reason import (
    FROZEN_SELECTION_REASONS,
    SelectionReason,
    parse_selection_reason,
)
from runtime.layer5.evidence.snippet import SnippetSpan, extract_snippet

__all__ = [
    "EVIDENCE_IDENTITY_MISMATCH_CODE",
    "EvidenceSchemaValidationError",
    "FROZEN_SELECTION_REASONS",
    "IdentityMismatchError",
    "SCHEMA_HINT",
    "SelectionReason",
    "SnippetConfig",
    "SnippetSpan",
    "EvidenceBundle",
    "EvidenceEntry",
    "build_evidence_bundle",
    "extract_snippet",
    "parse_selection_reason",
    "validate_evidence_bundle_dict",
]
