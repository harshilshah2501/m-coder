from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .assist_contracts import (
    ASSIST_VERSION,
    CANONICALIZATION_VERSION_V1,
    INPUT_HASH_SCOPE_V1,
    AssistInput,
    AssistOutput,
)


def canonicalize_original_query(query: str) -> str:
    # Canonicalization v1: UTF-8 encodable string, NFC, CRLF->LF, trim trailing ws per line.
    import unicodedata

    nfc = unicodedata.normalize("NFC", query)
    lf = nfc.replace("\r\n", "\n")
    lines = [line.rstrip() for line in lf.split("\n")]
    return "\n".join(lines)


def input_hash_sha256(query: str) -> str:
    canonical = canonicalize_original_query(query)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_assist_event(
    assist_input: AssistInput,
    assist_output: AssistOutput,
    reason_code: str,
    latency_ms: float,
    error_class: str | None = None,
) -> Dict[str, Any]:
    return {
        "event_name": "assist_layer_event",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "request_id": assist_input.request_id,
        "trace_id": assist_input.trace_id,
        "session_id": assist_input.session_id,
        "assist_version": ASSIST_VERSION,
        "assist_status": assist_output.assist_status.value,
        "confidence_enum": assist_output.confidence_enum.value,
        "reason_code": reason_code,
        "transform_codes_applied": list(assist_output.transform_codes_applied),
        "suggestions_source_tags": list(assist_output.suggestion_sources),
        "latency_ms": round(float(latency_ms), 3),
        "input_hash": input_hash_sha256(assist_input.original_query),
        "input_hash_scope": INPUT_HASH_SCOPE_V1,
        "canonicalization_version": CANONICALIZATION_VERSION_V1,
        "error_class": error_class,
    }


def emit_assist_event(log: logging.Logger, event: Dict[str, Any]) -> None:
    log.info("ASSIST_LAYER %s", json.dumps(event, sort_keys=True))
