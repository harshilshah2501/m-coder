"""Normalization helpers for Lane A intelligence documents."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Collection, Dict, List, Mapping, Sequence, Tuple


@dataclass(frozen=True)
class IntelligenceWarning:
    """Non-fatal normalization warning."""

    code: str
    message: str
    behavior_id: str
    address: str


def derive_eventbus_addresses_from_mechanisms(stages: Sequence[Mapping[str, Any]]) -> Dict[str, List[str]]:
    """
    Build compatibility eventbus addresses from authoritative mechanisms.

    Heuristic:
    - source_symbol present -> publish side
    - target_symbol present -> consume side
    - neither present -> publish side (conservative default)
    """
    publishes: List[str] = []
    consumes: List[str] = []

    for stage in stages:
        mechanisms = stage.get("mechanisms", [])
        if not isinstance(mechanisms, list):
            continue
        for mechanism in mechanisms:
            if not isinstance(mechanism, Mapping):
                continue
            if mechanism.get("type") != "EVENTBUS":
                continue
            address = mechanism.get("address")
            if not isinstance(address, str) or not address.strip():
                continue

            has_source = bool(mechanism.get("source_symbol"))
            has_target = bool(mechanism.get("target_symbol"))

            if has_source or not has_target:
                publishes.append(address)
            if has_target:
                consumes.append(address)

    return {
        "publishes": _stable_unique(publishes),
        "consumes": _stable_unique(consumes),
    }


def validate_eventbus_addresses_against_constants(
    behavior_id: str,
    eventbus_addresses: Mapping[str, Sequence[str]],
    extracted_constants: Collection[str],
) -> List[IntelligenceWarning]:
    """Return warnings for derived addresses that do not resolve to extracted constants."""
    warnings: List[IntelligenceWarning] = []
    known = {value for value in extracted_constants if isinstance(value, str) and value.strip()}
    for side in ("publishes", "consumes"):
        for address in eventbus_addresses.get(side, []):
            if address not in known:
                warnings.append(
                    IntelligenceWarning(
                        code="UNRESOLVED_EVENTBUS_ADDRESS",
                        message=f"Derived {side} address not found in extracted constants",
                        behavior_id=behavior_id,
                        address=address,
                    )
                )
    return warnings


def normalize_behavior_flows_document(
    document: Mapping[str, Any],
    extracted_eventbus_constants: Collection[str] | None = None,
) -> Tuple[Dict[str, Any], List[IntelligenceWarning]]:
    """
    Normalize behavior flows with mechanisms as the sole source of truth.

    - authored eventbus_addresses are ignored and replaced
    - compatibility eventbus_addresses are always derived from mechanisms
    """
    normalized: Dict[str, Any] = deepcopy(dict(document))
    warnings: List[IntelligenceWarning] = []
    flows = normalized.get("behavior_flows", [])
    if not isinstance(flows, list):
        return normalized, warnings

    constants = extracted_eventbus_constants
    for behavior in flows:
        if not isinstance(behavior, dict):
            continue
        stages = behavior.get("stages", [])
        if not isinstance(stages, list):
            continue

        derived = derive_eventbus_addresses_from_mechanisms(stages)
        behavior["eventbus_addresses"] = derived

        if constants is not None:
            behavior_id = str(behavior.get("behavior_id", "unknown_behavior"))
            warnings.extend(
                validate_eventbus_addresses_against_constants(
                    behavior_id=behavior_id,
                    eventbus_addresses=derived,
                    extracted_constants=constants,
                )
            )

    return normalized, warnings


def _stable_unique(values: Sequence[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
