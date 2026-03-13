"""Reconciliation using join key (request_id, plan_hash)."""

from __future__ import annotations

from .validate import plan_hash


def reconcile_items(items: list[dict]) -> list[dict]:
    """Check each item for join-key consistency. Returns sorted list of mismatch errors."""
    errors = []
    for item in items:
        req_id = item.get("request_id")
        plan = item.get("plan")
        ledger = item.get("ledger_row")
        dec = item.get("decision_response")
        if not req_id or not plan:
            errors.append({"request_id": req_id or "", "plan_hash": "", "error": "missing request_id or plan"})
            continue
        ph = (plan.get("integrity") or {}).get("plan_hash") or plan_hash(plan)
        lr_hash = (ledger or {}).get("plan_link", {}).get("plan_hash")
        if lr_hash and lr_hash != ph:
            errors.append({"request_id": req_id, "plan_hash": ph, "error": f"ledger plan_hash mismatch: {lr_hash}"})
        if dec and dec.get("plan_hash") and dec.get("plan_hash") != ph:
            errors.append({"request_id": req_id, "plan_hash": ph, "error": f"decision plan_hash mismatch: {dec.get('plan_hash')}"})
    return sorted(errors, key=lambda x: (x.get("request_id", ""), x.get("plan_hash", "")))
