"""
Authority Registry Loader.

Loads and validates product_authority_registry.yaml.
Provides concept lookup and query matching.

Phase 1: No ranking integration. Data loading only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Tuple

import yaml


class AuthorityRegistryError(Exception):
    """Raised when registry loading or validation fails."""

    pass


@dataclass(frozen=True)
class PrimaryOwner:
    """Primary owner of a concept."""

    file: str
    class_name: str
    method: Optional[str] = None
    confidence: str = "high"

    def __post_init__(self) -> None:
        if self.confidence not in ("high", "medium", "low"):
            raise AuthorityRegistryError(
                f"Invalid confidence '{self.confidence}'; must be high/medium/low"
            )


@dataclass(frozen=True)
class Collaborator:
    """Secondary file that participates in a concept."""

    file: str
    role: str
    relationship: str


@dataclass(frozen=True)
class Distractor:
    """File that matches keywords but is NOT the owner."""

    file: str
    reason: str


@dataclass(frozen=True)
class Verification:
    """Drift control metadata."""

    last_verified_at: datetime
    verification_source: str
    verification_notes: Optional[str] = None
    staleness_threshold_days: int = 90

    def __post_init__(self) -> None:
        if self.verification_source not in ("code_trace", "human", "test"):
            raise AuthorityRegistryError(
                f"Invalid verification_source '{self.verification_source}'; "
                "must be code_trace/human/test"
            )


@dataclass(frozen=True)
class EntryPoint:
    """Known system entry point for a concept."""

    type: str
    file: str
    method: str
    event_type: Optional[str] = None
    endpoint: Optional[str] = None


@dataclass(frozen=True)
class Concept:
    """A product concept with ownership metadata."""

    name: str
    primary_owner: PrimaryOwner
    aliases: FrozenSet[str]
    collaborators: Tuple[Collaborator, ...]
    forbidden_distractors: Tuple[Distractor, ...]
    verification: Verification
    notes: Tuple[str, ...] = ()
    entry_points: Tuple[EntryPoint, ...] = ()
    control_flow: Optional[Dict[str, object]] = None


@dataclass
class AuthorityRegistry:
    """Loaded and validated authority registry."""

    schema_version: str
    last_updated: str
    maintainer: str
    concepts: Dict[str, Concept] = field(default_factory=dict)

    _alias_index: Dict[str, str] = field(default_factory=dict, repr=False)
    _token_index: Dict[str, List[str]] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._build_indices()

    def _build_indices(self) -> None:
        """Build alias and token indices for fast lookup."""
        self._alias_index.clear()
        self._token_index.clear()

        for concept_name, concept in self.concepts.items():
            concept_name_lower = concept_name.lower()
            self._alias_index[concept_name_lower] = concept_name

            for alias in concept.aliases:
                alias_lower = alias.lower()
                self._alias_index[alias_lower] = concept_name

            tokens = _tokenize(concept_name)
            for token in tokens:
                if token not in self._token_index:
                    self._token_index[token] = []
                self._token_index[token].append(concept_name)

    def get_concept(self, concept_name: str) -> Optional[Concept]:
        """Get concept by exact name."""
        return self.concepts.get(concept_name)

    def match_concept(self, query_text: str) -> Optional[Tuple[Concept, str, float]]:
        """
        Match query text to a concept.

        Returns:
            Tuple of (concept, match_type, confidence) or None.
            match_type: "exact" | "alias" | "partial"
        """
        query_lower = query_text.lower().strip()

        if query_lower in self._alias_index:
            concept_name = self._alias_index[query_lower]
            concept = self.concepts[concept_name]
            match_type = "exact" if query_lower == concept_name.lower() else "alias"
            return (concept, match_type, 1.0)

        for alias, concept_name in self._alias_index.items():
            if alias in query_lower:
                concept = self.concepts[concept_name]
                return (concept, "alias", 0.9)

        query_tokens = set(_tokenize(query_lower))
        if not query_tokens:
            return None

        best_match: Optional[Tuple[str, float]] = None
        for concept_name in self.concepts:
            concept_tokens = set(_tokenize(concept_name.lower()))
            if not concept_tokens:
                continue
            overlap = query_tokens.intersection(concept_tokens)
            if overlap:
                score = len(overlap) / len(concept_tokens)
                if score >= 0.5 and (best_match is None or score > best_match[1]):
                    best_match = (concept_name, score)

        if best_match:
            concept = self.concepts[best_match[0]]
            return (concept, "partial", best_match[1])

        return None

    def list_concepts(self) -> List[str]:
        """List all concept names."""
        return list(self.concepts.keys())


def _tokenize(text: str) -> Tuple[str, ...]:
    """Split text into lowercase tokens."""
    tokens = re.split(r"[_\s\-]+", text.lower())
    return tuple(t for t in tokens if len(t) >= 2)


def _parse_datetime(value: str) -> datetime:
    """Parse ISO datetime string."""
    if isinstance(value, datetime):
        return value
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise AuthorityRegistryError(f"Cannot parse datetime: {value}")


def _parse_primary_owner(data: dict) -> PrimaryOwner:
    """Parse primary_owner block."""
    if not isinstance(data, dict):
        raise AuthorityRegistryError("primary_owner must be a dict")

    required = ["file", "class"]
    for key in required:
        if key not in data:
            raise AuthorityRegistryError(f"primary_owner missing required field: {key}")

    return PrimaryOwner(
        file=str(data["file"]),
        class_name=str(data["class"]),
        method=data.get("method"),
        confidence=data.get("confidence", "high"),
    )


def _parse_verification(data: Optional[dict]) -> Verification:
    """Parse verification block."""
    if data is None:
        return Verification(
            last_verified_at=datetime.now(),
            verification_source="human",
            staleness_threshold_days=90,
        )

    if not isinstance(data, dict):
        raise AuthorityRegistryError("verification must be a dict")

    required = ["last_verified_at", "verification_source"]
    for key in required:
        if key not in data:
            raise AuthorityRegistryError(f"verification missing required field: {key}")

    return Verification(
        last_verified_at=_parse_datetime(data["last_verified_at"]),
        verification_source=str(data["verification_source"]),
        verification_notes=data.get("verification_notes"),
        staleness_threshold_days=int(data.get("staleness_threshold_days", 90)),
    )


def _parse_collaborators(data: Optional[list]) -> Tuple[Collaborator, ...]:
    """Parse collaborators list."""
    if not data:
        return ()

    result = []
    for item in data:
        if not isinstance(item, dict):
            raise AuthorityRegistryError("collaborator entry must be a dict")
        result.append(
            Collaborator(
                file=str(item.get("file", "")),
                role=str(item.get("role", "")),
                relationship=str(item.get("relationship", "")),
            )
        )
    return tuple(result)


def _parse_distractors(data: Optional[list]) -> Tuple[Distractor, ...]:
    """Parse forbidden_distractors list."""
    if not data:
        return ()

    result = []
    for item in data:
        if not isinstance(item, dict):
            raise AuthorityRegistryError("distractor entry must be a dict")
        result.append(
            Distractor(
                file=str(item.get("file", "")),
                reason=str(item.get("reason", "")),
            )
        )
    return tuple(result)


def _parse_entry_points(data: Optional[list]) -> Tuple[EntryPoint, ...]:
    """Parse entry_points list."""
    if not data:
        return ()

    result = []
    for item in data:
        if not isinstance(item, dict):
            raise AuthorityRegistryError("entry_point entry must be a dict")
        result.append(
            EntryPoint(
                type=str(item.get("type", "")),
                file=str(item.get("file", "")),
                method=str(item.get("method", "")),
                event_type=item.get("event_type"),
                endpoint=item.get("endpoint"),
            )
        )
    return tuple(result)


def _parse_concept(name: str, data: dict) -> Concept:
    """Parse a single concept definition."""
    if not isinstance(data, dict):
        raise AuthorityRegistryError(f"Concept '{name}' must be a dict")

    if "primary_owner" not in data:
        raise AuthorityRegistryError(f"Concept '{name}' missing primary_owner")

    aliases_raw = data.get("aliases", [])
    if not isinstance(aliases_raw, list):
        raise AuthorityRegistryError(f"Concept '{name}' aliases must be a list")

    notes_raw = data.get("notes", [])
    if not isinstance(notes_raw, list):
        notes_raw = []

    return Concept(
        name=name,
        primary_owner=_parse_primary_owner(data["primary_owner"]),
        aliases=frozenset(str(a) for a in aliases_raw),
        collaborators=_parse_collaborators(data.get("collaborators")),
        forbidden_distractors=_parse_distractors(data.get("forbidden_distractors")),
        verification=_parse_verification(data.get("verification")),
        notes=tuple(str(n) for n in notes_raw),
        entry_points=_parse_entry_points(data.get("entry_points")),
        control_flow=data.get("control_flow"),
    )


def load_registry(path: Path | str) -> AuthorityRegistry:
    """
    Load and validate authority registry from YAML file.

    Args:
        path: Path to product_authority_registry.yaml

    Returns:
        Validated AuthorityRegistry instance.

    Raises:
        AuthorityRegistryError: On invalid schema or missing required fields.
        FileNotFoundError: If file does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Registry file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise AuthorityRegistryError(f"Invalid YAML: {e}") from e

    if not isinstance(data, dict):
        raise AuthorityRegistryError("Registry root must be a dict")

    required_root = ["schema_version", "concepts"]
    for key in required_root:
        if key not in data:
            raise AuthorityRegistryError(f"Registry missing required field: {key}")

    concepts_raw = data.get("concepts", {})
    if not isinstance(concepts_raw, dict):
        raise AuthorityRegistryError("concepts must be a dict")

    concepts: Dict[str, Concept] = {}
    for concept_name, concept_data in concepts_raw.items():
        concepts[concept_name] = _parse_concept(concept_name, concept_data)

    return AuthorityRegistry(
        schema_version=str(data.get("schema_version", "")),
        last_updated=str(data.get("last_updated", "")),
        maintainer=str(data.get("maintainer", "")),
        concepts=concepts,
    )
