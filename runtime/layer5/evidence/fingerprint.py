"""
Deterministic fingerprint for evidence bundles (clone-independent).

Byte-offset and snippet semantics still refer to the real workspace; only
``canonical_root`` and ``workspace_identity_hash`` are cleared so fingerprints
are stable across machines and checkout paths.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from runtime.layer5.evidence.models import EvidenceBundle


def masked_bundle_dict(bundle: EvidenceBundle) -> Dict[str, Any]:
    """Same JSON shape as ``to_dict`` but with root identity fields blanked."""
    d = bundle.to_dict()
    d["canonical_root"] = ""
    d["workspace_identity_hash"] = ""
    return d


def bundle_masked_fingerprint_sha256(bundle: EvidenceBundle) -> str:
    """SHA-256 (hex) of canonical JSON for the masked dict (UTF-8)."""
    payload = json.dumps(masked_bundle_dict(bundle), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
