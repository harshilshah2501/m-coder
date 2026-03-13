"""Compute stable metrics from items."""

from __future__ import annotations

from collections import Counter


def compute_metrics(items: list[dict]) -> dict:
    """Compute stable distributions. Deterministic sort order."""
    by_decision: Counter[str] = Counter()
    by_phase: Counter[str] = Counter()
    by_boundary: Counter[str] = Counter()
    by_authority: Counter[str] = Counter()
    by_reason: Counter[str] = Counter()
    lineage = {"base_id": 0, "variant_id": 0, "freeze_version_id": 0, "model_artifact_id": 0}
    total = len(items)
    unresolved = 0
    blocked = 0
    crossed = 0
    refusal = 0

    for item in items:
        ledger = item.get("ledger_row", {})
        dec = item.get("decision_response", {})
        v = ledger.get("verdicts", {})
        dec_val = dec.get("decision", "none") if dec else "none"
        by_decision[dec_val] += 1
        by_phase[v.get("phase_emitted", "unknown")] += 1
        bv = v.get("boundary_verdict", "unknown")
        by_boundary[bv] += 1
        av = v.get("authority_verdict", "unknown")
        by_authority[av] += 1
        for rc in ledger.get("reason_codes", []):
            by_reason[rc] += 1
        refs = item.get("lineage_refs") or {}
        if refs.get("base_id"):
            lineage["base_id"] += 1
        if refs.get("variant_id"):
            lineage["variant_id"] += 1
        if refs.get("freeze_version_id"):
            lineage["freeze_version_id"] += 1
        if refs.get("model_artifact_id"):
            lineage["model_artifact_id"] += 1
        prov = dec.get("provenance_resolution", {}) if dec else {}
        if prov.get("resolved_via") != "lineage_index" and not refs.get("base_id"):
            unresolved += 1
        if bv == "blocked":
            blocked += 1
        if bv == "crossed":
            crossed += 1
        if dec_val == "REFUSAL":
            refusal += 1

    return {
        "by_decision": dict(sorted(by_decision.items())),
        "by_phase_emitted": dict(sorted(by_phase.items())),
        "by_boundary_verdict": dict(sorted(by_boundary.items())),
        "by_authority_verdict": dict(sorted(by_authority.items())),
        "by_reason_code": dict(by_reason.most_common(20)),
        "lineage_links": lineage,
        "items_count": total,
        "unresolved_lineage_count": unresolved,
        "unresolved_lineage_rate": round(unresolved / total, 4) if total else 0,
        "blocked_count": blocked,
        "blocked_rate": round(blocked / total, 4) if total else 0,
        "refusal_count": refusal,
        "refusal_rate": round(refusal / total, 4) if total else 0,
        "crossed_count": crossed,
    }
