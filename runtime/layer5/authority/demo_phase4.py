#!/usr/bin/env python3
"""
Phase 4 demo: authority evidence + Plan-Gate-style anchored synthesis (stdout).

No servers. Uses the same deterministic synthesis as /v1/ask plan path.
"""

from __future__ import annotations

import json
from pathlib import Path

from runtime.ask_service.authority_synthesis import synthesize_authority_plan_steps
from runtime.context.contracts import (
    ContextBundle,
    ContextBundleLimits,
    ContextBundleProvenance,
    ContextItem,
)
from runtime.layer5.authority.authority_evidence import build_authority_resolution
from runtime.layer5.authority.code_index_adapter import create_adapter
from runtime.layer5.authority.code_index_builder import build_index
from runtime.layer5.authority.registry_loader import load_registry


def _bundle(paths: list[str]) -> ContextBundle:
    from datetime import datetime, timezone

    items = [
        ContextItem(path=p, content="", byte_size=0, selection_reason="query_token_substring_anchor")
        for p in paths
    ]
    return ContextBundle(
        task_id="demo",
        revision="demo",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        items=items,
        limits=ContextBundleLimits(max_files=len(items), max_bytes=0, truncated=False),
        provenance=ContextBundleProvenance(
            root_path="/tmp",
            selectors=["demo_phase4"],
            requested_files=paths,
            symbol_hints=[],
        ),
    )


def main() -> None:
    repo = Path(__file__).resolve().parents[3]
    reg_path = Path(__file__).resolve().parent / "product_authority_registry.yaml"
    registry = load_registry(reg_path)

    try:
        adapter = create_adapter(code_index=build_index(repo))
    except Exception:
        adapter = None

    # A — validated-style owner (adapter may mark stale/unverified if files absent)
    q1 = "incident deduplication"
    ar1 = build_authority_resolution(q1, registry, adapter)
    paths1 = [
        "motadata/src/main/java/com/mindarray/aiops/integration/ServiceNowIntegration.java",
        "motadata/src/main/java/com/mindarray/aiops/correlation/IncidentDeduplicationProcessor.java",
    ]
    steps1, meta1 = synthesize_authority_plan_steps(q1, _bundle(paths1), ar1)
    print("=== A: Anchored owner (distractor ranked above owner in lexical top-k) ===")
    print(json.dumps({"authority_resolution": ar1, "synthesis_meta": meta1}, indent=2))
    for s in steps1:
        print("-", s)

    # B — weak / stale tone (force status in a synthetic dict for demo)
    ar2 = dict(ar1) if ar1 else {}
    ar2["authority_status"] = "stale_candidate"
    ar2["authority_confidence"] = "weak"
    steps2, meta2 = synthesize_authority_plan_steps(q1, _bundle(paths1), ar2)
    print("\n=== B: Stale / uncertain ===")
    print(json.dumps({"synthesis_meta": meta2}, indent=2))
    for s in steps2:
        print("-", s)

    # C — distractor suppression wording
    print("\n=== C: Distractor caution (high lexical rank) ===")
    for s in steps1:
        if "distractor" in s.lower() or "not owner" in s.lower():
            print("-", s)

    # D — compound
    q4 = "incident deduplication and alert correlation"
    ar4 = build_authority_resolution(q4, registry, adapter)
    paths4 = [
        "motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java",
        "motadata/src/main/java/com/mindarray/aiops/correlation/IncidentDeduplicationProcessor.java",
    ]
    steps4, meta4 = synthesize_authority_plan_steps(q4, _bundle(paths4), ar4)
    print("\n=== D: Compound query ===")
    print(json.dumps({"compound": ar4.get("compound") if ar4 else None, "meta": meta4}, indent=2))
    for s in steps4:
        print("-", s)


if __name__ == "__main__":
    main()
