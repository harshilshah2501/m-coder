"""Load and normalize intelligence documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Collection, Dict, List

import yaml

from runtime.intelligence.normalize import IntelligenceWarning, normalize_behavior_flows_document
from runtime.intelligence.schema import (
    IntelligenceSchemaError,
    validate_behavior_flows_document,
    validate_convention_playbooks_document,
)


class IntelligenceLoaderError(RuntimeError):
    """Raised when loading intelligence docs fails."""


@dataclass(frozen=True)
class IntelligenceBundle:
    """Loaded intelligence payload."""

    behavior_flows: Dict[str, Any]
    convention_playbooks: Dict[str, Any]
    warnings: List[IntelligenceWarning]


def load_intelligence(
    repo_root: Path | str,
    extracted_eventbus_constants: Collection[str] | None = None,
) -> IntelligenceBundle:
    """Load docs/intelligence behavior flows and playbooks with validation."""
    root = Path(repo_root)
    behavior_path = root / "docs" / "intelligence" / "behavior_flows.yaml"
    playbooks_path = root / "docs" / "intelligence" / "convention_playbooks.yaml"

    behavior_flows = _load_yaml(behavior_path)
    playbooks = _load_yaml(playbooks_path)

    validate_behavior_flows_document(behavior_flows)
    validate_convention_playbooks_document(playbooks)

    normalized_behavior_flows, warnings = normalize_behavior_flows_document(
        behavior_flows,
        extracted_eventbus_constants=extracted_eventbus_constants,
    )

    # Validate post-normalization payload too, so downstream sees strict shape.
    validate_behavior_flows_document(normalized_behavior_flows)

    return IntelligenceBundle(
        behavior_flows=normalized_behavior_flows,
        convention_playbooks=playbooks,
        warnings=warnings,
    )


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Intelligence document not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise IntelligenceLoaderError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise IntelligenceSchemaError(f"{path} root must be a mapping")
    return payload
