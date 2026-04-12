from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple


PR6_MODE_BASELINE = "baseline_real_repo"
PR6_MODE_FIXTURE = "fixture_diagnostic"
PR6_MODE_INVALID = "invalid"

DEFAULT_CANONICAL_ROOT = Path("/home/harshil/Projects/Motadata")
_FIXTURE_ROOT = Path(__file__).resolve().parent / "fixture_noisy_aiops_workspace"


@dataclass(frozen=True)
class PR6Context:
    mode: str
    root: Path
    reason: str


def pr6_fixture_root() -> Path:
    return _FIXTURE_ROOT.resolve()


def _anchors_exist_under_root(root: Path, anchors: Iterable[str]) -> bool:
    for anchor in anchors:
        if (root / anchor).exists():
            return True
    return False


def classify_pr6_context(root: Path, anchors: Tuple[str, ...], canonical_root: Path) -> PR6Context:
    rr = root.resolve()
    fixture_root = pr6_fixture_root()
    canonical = canonical_root.resolve()

    if rr == fixture_root:
        return PR6Context(
            mode=PR6_MODE_FIXTURE,
            root=rr,
            reason="Root is bundled PR-6 fixture workspace; diagnostic-only context.",
        )

    # Explicitly reject shifted sub-roots to prevent motadata/ prefix mismatch.
    if rr != fixture_root and fixture_root in rr.parents:
        return PR6Context(
            mode=PR6_MODE_INVALID,
            root=rr,
            reason="Root is inside bundled fixture subtree (shifted-root corpus not allowed).",
        )

    if rr == canonical:
        if not _anchors_exist_under_root(rr, anchors):
            return PR6Context(
                mode=PR6_MODE_INVALID,
                root=rr,
                reason="Canonical root selected but PR-6 anchor prefix mismatch detected.",
            )
        return PR6Context(
            mode=PR6_MODE_BASELINE,
            root=rr,
            reason="Canonical PR-6 real-repo baseline context.",
        )

    if not _anchors_exist_under_root(rr, anchors):
        return PR6Context(
            mode=PR6_MODE_INVALID,
            root=rr,
            reason="No PR-6 anchors found under provided root (invalid baseline corpus).",
        )

    return PR6Context(
        mode=PR6_MODE_INVALID,
        root=rr,
        reason="Root is non-canonical and non-fixture for PR-6 baseline contract.",
    )
