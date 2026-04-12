"""
Frozen identity-mismatch policy for evidence bundle construction.

Policy (v1)
-----------
- When ``require_identity_match`` is True (default), ``build_evidence_bundle`` raises
  ``IdentityMismatchError`` if ``RetrievalResult.workspace_identity_hash`` differs from
  ``WorkspaceFileIndex.workspace_identity_hash``. This refuses cross-snapshot pairing.
- When ``require_identity_match`` is False, no check is performed; the caller accepts
  full responsibility for inconsistent retrieval/index pairs (no warning is emitted).
"""

from __future__ import annotations

EVIDENCE_IDENTITY_MISMATCH_CODE = "layer5.evidence.identity_mismatch"


class IdentityMismatchError(ValueError):
    """Raised when retrieval and index workspace identity hashes disagree (strict mode)."""

    def __init__(self, retrieval_hash: str, index_hash: str) -> None:
        self.retrieval_hash = retrieval_hash
        self.index_hash = index_hash
        msg = (
            f"{EVIDENCE_IDENTITY_MISMATCH_CODE}: "
            f"RetrievalResult.workspace_identity_hash ({retrieval_hash}) != "
            f"WorkspaceFileIndex.workspace_identity_hash ({index_hash}); "
            "refuse to build evidence for mismatched snapshots."
        )
        super().__init__(msg)
