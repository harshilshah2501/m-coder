"""Stage 3 observability ledger."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class LedgerEvent:
    request_id: str
    iteration_index: int
    event_type: str
    state_from: str | None = None
    state_to: str | None = None
    proposal_ref: str | None = None
    decision_ref: str | None = None
    tool_result_ref: str | None = None
    reason_code: str | None = None
    payload: dict[str, Any] | None = None
    timestamp_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if not self.timestamp_utc:
            data["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        return data


class Stage3Ledger:
    """Append-only JSONL ledger with in-memory query helpers."""

    def __init__(self, path: Path | str | None = None) -> None:
        self._events: list[dict[str, Any]] = []
        self._path = Path(path) if path else None

    def emit(self, event: LedgerEvent) -> None:
        row = event.to_dict()
        self._events.append(row)
        if self._path:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def list_by_request_id(self, request_id: str) -> list[dict[str, Any]]:
        return [e for e in self._events if e["request_id"] == request_id]

    def reason_code_chain(self, request_id: str) -> list[str]:
        return [e["reason_code"] for e in self.list_by_request_id(request_id) if e.get("reason_code")]

    def reconstruct_trace(self, request_id: str) -> dict[str, Any]:
        events = self.list_by_request_id(request_id)
        iteration_links: dict[int, dict[str, Any]] = {}
        terminal_event = None
        for e in events:
            idx = int(e.get("iteration_index", -1))
            if idx >= 0:
                row = iteration_links.setdefault(
                    idx,
                    {"proposal_ref": None, "decision_ref": None, "tool_result_ref": None, "events": []},
                )
                row["events"].append(e["event_type"])
                if e.get("proposal_ref"):
                    row["proposal_ref"] = e["proposal_ref"]
                if e.get("decision_ref"):
                    row["decision_ref"] = e["decision_ref"]
                if e.get("tool_result_ref"):
                    row["tool_result_ref"] = e["tool_result_ref"]
            if e.get("event_type") == "terminal_decision":
                terminal_event = e

        return {
            "request_id": request_id,
            "events": events,
            "reason_code_chain": self.reason_code_chain(request_id),
            "proposal_refs": [e["proposal_ref"] for e in events if e.get("proposal_ref")],
            "decision_refs": [e["decision_ref"] for e in events if e.get("decision_ref")],
            "tool_result_refs": [e["tool_result_ref"] for e in events if e.get("tool_result_ref")],
            "iteration_linkage": iteration_links,
            "terminal_decision_summary": {
                "state": (terminal_event or {}).get("state_to"),
                "reason_code": (terminal_event or {}).get("reason_code"),
                "outcome": ((terminal_event or {}).get("payload") or {}).get("outcome"),
            },
            "execution_truth_summary": ((terminal_event or {}).get("payload") or {}).get("execution_status"),
        }
