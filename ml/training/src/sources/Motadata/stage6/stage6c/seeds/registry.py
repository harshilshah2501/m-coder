"""
Abstract seed registry: read-only access to seed content.
Seed content must remain immutable; registries return immutable views.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional


class SeedView:
    """
    Immutable view of one seed. Callers must not mutate returned lists/strings.
    """
    __slots__ = ("seed_id", "governance_system_messages", "seed_system_messages",
                 "seed_user_messages", "seed_metadata")

    def __init__(
        self,
        seed_id: str,
        governance_system_messages: List[str],
        seed_system_messages: List[str],
        seed_user_messages: List[str],
        seed_metadata: dict,
    ) -> None:
        self.seed_id = seed_id
        self.governance_system_messages = tuple(governance_system_messages)  # immutable
        self.seed_system_messages = tuple(seed_system_messages)
        self.seed_user_messages = tuple(seed_user_messages)
        self.seed_metadata = dict(seed_metadata)  # shallow copy; treat as read-only

    def expected_phase(self) -> Optional[str]:
        return self.seed_metadata.get("expected_phase")

    def boundary_string(self) -> Optional[str]:
        return self.seed_metadata.get("boundary_string")


class SeedRegistry(ABC):
    """Read-only registry of seeds. No PHASE4 seed text embedded in code."""

    @abstractmethod
    def get(self, seed_id: str) -> Optional[SeedView]:
        """Return immutable view for seed_id, or None if not found."""
        ...

    @abstractmethod
    def list_seed_ids(self) -> List[str]:
        """Return list of available seed_ids."""
        ...
