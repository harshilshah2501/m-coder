"""
Canonical Execution Intent — M4.1 schema and identity.

Single semantic source of truth for execution identity. argv is canonical;
shell text is not. Hash derives from normalized execution content only;
intent_id is excluded so same execution content yields same canonical_hash.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


# Fixed field order for deterministic serialization (hash input).
_HASH_FIELD_ORDER = (
    "request_id",
    "plan_hash",
    "executable",
    "argv",
    "working_dir",
    "env_delta",
    "timeout_seconds",
    "capture_artifacts",
)


@dataclass(frozen=True)
class CanonicalExecutionIntent:
    """
    Canonical representation of what will be executed.

    All policy evaluation and execution use this structure (or a strict
    lossless projection). No downstream re-parsing of command text.
    """

    # Identity / provenance
    request_id: str
    plan_hash: str
    intent_id: str
    canonical_hash: str

    # Execution fields (canonical)
    executable: str
    argv: tuple[str, ...]
    working_dir: str
    env_delta: tuple[tuple[str, str], ...]  # (k, v) pairs, sorted by k for stability
    timeout_seconds: int | None
    capture_artifacts: tuple[str, ...]
    repo_root: str = ""  # repository root (may differ from working_dir; after required for dataclass order)

    # Optional policy-relevant (not part of hash in MVP; guard/gate may use)
    filesystem_intent: str = ""
    network_intent: str = ""
    side_effect_class: str = ""
    authority_context: str = ""  # serialized if dict
    irreversibility_class: str = ""

    # Optional metadata (not used for hashing; guard may use branch for protected_branch_mutation)
    backend_hint: str = ""
    execution_surface: str = ""
    notes: str = ""
    branch: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Dictionary for ledger/serialization. env_delta as dict with sorted keys."""
        env = dict(self.env_delta)
        return {
            "request_id": self.request_id,
            "plan_hash": self.plan_hash,
            "intent_id": self.intent_id,
            "canonical_hash": self.canonical_hash,
            "executable": self.executable,
            "argv": list(self.argv),
            "working_dir": self.working_dir,
            "repo_root": self.repo_root,
            "env_delta": env,
            "timeout_seconds": self.timeout_seconds,
            "capture_artifacts": list(self.capture_artifacts),
            "filesystem_intent": self.filesystem_intent,
            "network_intent": self.network_intent,
            "side_effect_class": self.side_effect_class,
            "authority_context": self.authority_context,
            "irreversibility_class": self.irreversibility_class,
            "backend_hint": self.backend_hint,
            "execution_surface": self.execution_surface,
            "notes": self.notes,
            "branch": self.branch,
        }


def serialize_for_hash(intent: CanonicalExecutionIntent) -> bytes:
    """
    Stable serialization for canonical_hash.

    Fixed field order; intent_id excluded so same execution content
    yields same hash. env_delta serialized with sorted keys.
    """
    env_dict = dict(intent.env_delta)
    obj: dict[str, Any] = {
        "request_id": intent.request_id,
        "plan_hash": intent.plan_hash,
        "executable": intent.executable,
        "argv": list(intent.argv),
        "working_dir": intent.working_dir,
        "env_delta": json.dumps(env_dict, sort_keys=True, ensure_ascii=False),
        "timeout_seconds": intent.timeout_seconds,
        "capture_artifacts": list(intent.capture_artifacts),
    }
    # Emit in fixed order
    out: dict[str, Any] = {}
    for key in _HASH_FIELD_ORDER:
        if key in obj:
            out[key] = obj[key]
    return json.dumps(out, sort_keys=True, ensure_ascii=False).encode("utf-8")


def compute_canonical_hash(intent: CanonicalExecutionIntent) -> str:
    """
    SHA-256 hash of normalized execution content (hex).

    Same artifact → same hash. intent_id is excluded.
    """
    return hashlib.sha256(serialize_for_hash(intent)).hexdigest()
