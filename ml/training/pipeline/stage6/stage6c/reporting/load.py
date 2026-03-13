from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from ..metrics.types import LedgerRow


# Minimal fields required for M5 reporting. Some have aliases in older/newer schemas.
_BASE_REQUIRED_FIELDS = {
    "run_id",
    "seed_id",
    "horizon_N",
    "shape",
    "severity",
    "BDA_norm",
    "code_fail_closed_erosions",
    "mix_dominance_flip",
    "collapse_labels",
}


class LedgerValidationError(ValueError):
    """Raised when the ledger JSONL is missing required fields."""


def _validate_rows(rows: Iterable[LedgerRow]) -> None:
    missing_any = False
    for idx, row in enumerate(rows):
        missing = set()
        for field in _BASE_REQUIRED_FIELDS:
            if field not in row:
                missing.add(field)

        # carryover / carryover_mode alias
        if "carryover_mode" not in row and "carryover" not in row:
            missing.add("carryover_mode/carryover")

        # injection profile alias
        if "injection_profile" not in row and "injection_profile_id" not in row:
            missing.add("injection_profile")

        if missing:
            missing_any = True
            raise LedgerValidationError(
                f"Ledger row {idx} (run_id={row.get('run_id')}) missing required fields: {sorted(missing)}"
            )

    if not missing_any and not list(rows):
        # Nothing to validate; empty ledger is allowed.
        return


def load_ledger(path: str | Path) -> List[LedgerRow]:
    """
    Load stage6c_ledger.jsonl into a list of LedgerRow dicts.

    Raises LedgerValidationError if required fields are missing.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Ledger file not found: {p}")

    rows: List[LedgerRow] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            rows.append(obj)

    # Validation over a shallow copy to avoid exhausting the list
    _validate_rows(list(rows))
    return rows


def normalize_carryover(row: LedgerRow) -> str | None:
    """Return canonical carryover_mode string from ledger row."""
    return row.get("carryover_mode") or row.get("carryover")


def normalize_injection_profile(row: LedgerRow) -> str | None:
    """Return canonical injection_profile_id string from ledger row."""
    return row.get("injection_profile") or row.get("injection_profile_id")

