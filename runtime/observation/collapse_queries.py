"""
Collapse Query Service — M4.3 query helpers for collapse events.

Provides filtering, aggregation, and retrieval of collapse events from
in-memory collections or persistent stores. Supports time-range queries,
class/severity filtering, and linkage lookups.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from runtime.observation.collapse_models import (
    CollapseClass,
    CollapseEvent,
    CollapseSeverity,
    CollapseSummary,
)


@dataclass
class CollapseFilter:
    """
    Filter criteria for collapse event queries.
    
    All criteria are optional; events must match all specified criteria.
    """
    
    collapse_classes: list[CollapseClass] | None = None
    severities: list[CollapseSeverity] | None = None
    request_ids: list[str] | None = None
    plan_hashes: list[str] | None = None
    canonical_hashes: list[str] | None = None
    session_ids: list[str] | None = None
    start_time: str | None = None
    end_time: str | None = None
    min_severity: CollapseSeverity | None = None
    
    def matches(self, event: CollapseEvent) -> bool:
        """Check if an event matches all filter criteria."""
        if self.collapse_classes and event.collapse_class not in self.collapse_classes:
            return False
        
        if self.severities and event.severity not in self.severities:
            return False
        
        if self.request_ids and event.request_id not in self.request_ids:
            return False
        
        if self.plan_hashes and event.plan_hash not in self.plan_hashes:
            return False
        
        if self.canonical_hashes:
            if not event.canonical_hash or event.canonical_hash not in self.canonical_hashes:
                return False
        
        if self.session_ids and event.session_id not in self.session_ids:
            return False
        
        if self.start_time and event.timestamp_utc < self.start_time:
            return False
        
        if self.end_time and event.timestamp_utc > self.end_time:
            return False
        
        if self.min_severity:
            severity_order = [
                CollapseSeverity.LOW,
                CollapseSeverity.MEDIUM,
                CollapseSeverity.HIGH,
                CollapseSeverity.CRITICAL,
            ]
            event_idx = severity_order.index(event.severity)
            min_idx = severity_order.index(self.min_severity)
            if event_idx < min_idx:
                return False
        
        return True
    
    def to_dict(self) -> dict[str, Any]:
        """Convert filter to dictionary for serialization."""
        d: dict[str, Any] = {}
        if self.collapse_classes:
            d["collapse_classes"] = [c.value for c in self.collapse_classes]
        if self.severities:
            d["severities"] = [s.value for s in self.severities]
        if self.request_ids:
            d["request_ids"] = self.request_ids
        if self.plan_hashes:
            d["plan_hashes"] = self.plan_hashes
        if self.canonical_hashes:
            d["canonical_hashes"] = self.canonical_hashes
        if self.session_ids:
            d["session_ids"] = self.session_ids
        if self.start_time:
            d["start_time"] = self.start_time
        if self.end_time:
            d["end_time"] = self.end_time
        if self.min_severity:
            d["min_severity"] = self.min_severity.value
        return d


@dataclass
class CollapseQueryService:
    """
    Query service for collapse events.
    
    Provides filtering, aggregation, and retrieval operations on collapse
    event collections. Can operate on in-memory lists or delegate to
    persistent stores.
    """
    
    events: list[CollapseEvent] = field(default_factory=list)
    
    def add_event(self, event: CollapseEvent) -> None:
        """Add an event to the collection."""
        self.events.append(event)
    
    def add_events(self, events: list[CollapseEvent]) -> None:
        """Add multiple events to the collection."""
        self.events.extend(events)
    
    def clear(self) -> None:
        """Clear all events from the collection."""
        self.events.clear()
    
    def query(
        self,
        filter_: CollapseFilter | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[CollapseEvent]:
        """
        Query events matching filter criteria.
        
        Args:
            filter_: Filter criteria (all events if None)
            limit: Maximum number of events to return
            offset: Number of events to skip
        
        Returns:
            List of matching events
        """
        if filter_ is None:
            matching = list(self.events)
        else:
            matching = [e for e in self.events if filter_.matches(e)]
        
        matching.sort(key=lambda e: e.timestamp_utc, reverse=True)
        
        if offset:
            matching = matching[offset:]
        if limit:
            matching = matching[:limit]
        
        return matching
    
    def count(self, filter_: CollapseFilter | None = None) -> int:
        """Count events matching filter criteria."""
        if filter_ is None:
            return len(self.events)
        return sum(1 for e in self.events if filter_.matches(e))
    
    def get_by_event_id(self, event_id: str) -> CollapseEvent | None:
        """Get a single event by event_id."""
        for e in self.events:
            if e.event_id == event_id:
                return e
        return None
    
    def get_by_request_id(self, request_id: str) -> list[CollapseEvent]:
        """Get all events for a request_id."""
        return [e for e in self.events if e.request_id == request_id]
    
    def get_by_plan_hash(self, plan_hash: str) -> list[CollapseEvent]:
        """Get all events for a plan_hash."""
        return [e for e in self.events if e.plan_hash == plan_hash]
    
    def get_by_canonical_hash(self, canonical_hash: str) -> list[CollapseEvent]:
        """Get all events for a canonical_hash."""
        return [e for e in self.events if e.canonical_hash == canonical_hash]
    
    def get_by_session_id(self, session_id: str) -> list[CollapseEvent]:
        """Get all events for a session_id."""
        return [e for e in self.events if e.session_id == session_id]
    
    def get_critical(self) -> list[CollapseEvent]:
        """Get all critical severity events."""
        return [e for e in self.events if e.severity == CollapseSeverity.CRITICAL]
    
    def get_high_or_above(self) -> list[CollapseEvent]:
        """Get all high or critical severity events."""
        return [
            e for e in self.events
            if e.severity in (CollapseSeverity.HIGH, CollapseSeverity.CRITICAL)
        ]
    
    def summarize(
        self,
        filter_: CollapseFilter | None = None,
    ) -> CollapseSummary:
        """
        Generate a summary of events matching filter criteria.
        
        Args:
            filter_: Filter criteria (all events if None)
        
        Returns:
            CollapseSummary with aggregated counts
        """
        matching = self.query(filter_)
        return CollapseSummary.from_events(matching)
    
    def group_by_class(
        self,
        filter_: CollapseFilter | None = None,
    ) -> dict[CollapseClass, list[CollapseEvent]]:
        """
        Group events by collapse class.
        
        Args:
            filter_: Filter criteria (all events if None)
        
        Returns:
            Dictionary mapping collapse class to events
        """
        matching = self.query(filter_)
        groups: dict[CollapseClass, list[CollapseEvent]] = {}
        for e in matching:
            if e.collapse_class not in groups:
                groups[e.collapse_class] = []
            groups[e.collapse_class].append(e)
        return groups
    
    def group_by_severity(
        self,
        filter_: CollapseFilter | None = None,
    ) -> dict[CollapseSeverity, list[CollapseEvent]]:
        """
        Group events by severity.
        
        Args:
            filter_: Filter criteria (all events if None)
        
        Returns:
            Dictionary mapping severity to events
        """
        matching = self.query(filter_)
        groups: dict[CollapseSeverity, list[CollapseEvent]] = {}
        for e in matching:
            if e.severity not in groups:
                groups[e.severity] = []
            groups[e.severity].append(e)
        return groups
    
    def get_unique_request_ids(
        self,
        filter_: CollapseFilter | None = None,
    ) -> set[str]:
        """Get unique request_ids from matching events."""
        matching = self.query(filter_)
        return {e.request_id for e in matching if e.request_id}
    
    def get_unique_plan_hashes(
        self,
        filter_: CollapseFilter | None = None,
    ) -> set[str]:
        """Get unique plan_hashes from matching events."""
        matching = self.query(filter_)
        return {e.plan_hash for e in matching if e.plan_hash}
    
    def get_time_range(self) -> tuple[str | None, str | None]:
        """Get the time range of all events (earliest, latest)."""
        if not self.events:
            return None, None
        timestamps = [e.timestamp_utc for e in self.events if e.timestamp_utc]
        if not timestamps:
            return None, None
        return min(timestamps), max(timestamps)
    
    def has_collapses(self) -> bool:
        """Check if any collapse events exist."""
        return len(self.events) > 0
    
    def has_critical(self) -> bool:
        """Check if any critical severity events exist."""
        return any(e.severity == CollapseSeverity.CRITICAL for e in self.events)
    
    def has_high_or_above(self) -> bool:
        """Check if any high or critical severity events exist."""
        return any(
            e.severity in (CollapseSeverity.HIGH, CollapseSeverity.CRITICAL)
            for e in self.events
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert service state to dictionary for serialization."""
        return {
            "events": [e.to_dict() for e in self.events],
            "total_count": len(self.events),
            "time_range": self.get_time_range(),
        }
    
    @classmethod
    def from_events(cls, events: list[CollapseEvent]) -> "CollapseQueryService":
        """Create service from list of events."""
        service = cls()
        service.events = list(events)
        return service


def find_related_collapses(
    service: CollapseQueryService,
    event: CollapseEvent,
) -> list[CollapseEvent]:
    """
    Find collapse events related to a given event.
    
    Related events share request_id, plan_hash, canonical_hash, or session_id.
    
    Args:
        service: Query service to search
        event: Reference event
    
    Returns:
        List of related events (excluding the reference event)
    """
    related: list[CollapseEvent] = []
    seen_ids: set[str] = {event.event_id}
    
    if event.request_id:
        for e in service.get_by_request_id(event.request_id):
            if e.event_id not in seen_ids:
                related.append(e)
                seen_ids.add(e.event_id)
    
    if event.plan_hash:
        for e in service.get_by_plan_hash(event.plan_hash):
            if e.event_id not in seen_ids:
                related.append(e)
                seen_ids.add(e.event_id)
    
    if event.canonical_hash:
        for e in service.get_by_canonical_hash(event.canonical_hash):
            if e.event_id not in seen_ids:
                related.append(e)
                seen_ids.add(e.event_id)
    
    if event.session_id:
        for e in service.get_by_session_id(event.session_id):
            if e.event_id not in seen_ids:
                related.append(e)
                seen_ids.add(e.event_id)
    
    return related


def build_collapse_chain(
    service: CollapseQueryService,
    request_id: str,
) -> list[CollapseEvent]:
    """
    Build a chronological chain of collapse events for a request.
    
    Args:
        service: Query service to search
        request_id: Request ID to trace
    
    Returns:
        List of events sorted by timestamp (oldest first)
    """
    events = service.get_by_request_id(request_id)
    events.sort(key=lambda e: e.timestamp_utc)
    return events
