"""
Deterministic file/subsystem classification and policy helpers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet, Iterable, Tuple


_NOISE_DIR_TOKENS: FrozenSet[str] = frozenset(
    {
        "test",
        "tests",
        "logs",
        "vendor",
        "node_modules",
        "test-plugin-metrics",
        "metrics_dump",
        "coverage",
    }
)

_CONFIG_EXTENSIONS: FrozenSet[str] = frozenset(
    {".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".conf", ".properties"}
)

_SUBSYSTEM_KEYWORDS = {
    "alerting": frozenset({"alert", "alerts", "dedup", "dedupe", "notification"}),
    "correlation": frozenset({"correlation", "correlate", "incident", "rca"}),
    "topology": frozenset({"topology", "topo", "graph", "node", "edge", "anomaly"}),
    "ingestion": frozenset({"ingest", "ingestion", "collector", "pipeline", "parser"}),
    "metrics": frozenset({"metric", "metrics", "telemetry", "timeseries", "prometheus"}),
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class FilePolicy:
    file_class: str
    subsystem: str


def _tokenize_path(rel_path: str) -> Tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(rel_path.lower()))


def classify_file(relative_path: str) -> FilePolicy:
    rel = relative_path.lower().strip("/")
    p = Path(rel)
    ext = p.suffix.lower()
    parts = tuple(part for part in p.parts if part)

    # Strong noise classes first.
    if any(part in {"test", "tests"} for part in parts) or p.name.endswith(("_test.py", "_spec.py")):
        return FilePolicy(file_class="tests", subsystem="unknown")
    if "logs" in parts or ext == ".log":
        return FilePolicy(file_class="logs", subsystem="unknown")
    if any(part in {"vendor", "node_modules"} for part in parts):
        return FilePolicy(file_class="vendor_static", subsystem="unknown")
    if any(part in {"test-plugin-metrics", "metrics_dump"} for part in parts):
        return FilePolicy(file_class="generated_metrics_data", subsystem="unknown")
    if ext == ".json" and any(tok in rel for tok in ("metrics", "snapshot", "report")):
        return FilePolicy(file_class="generated_metrics_data", subsystem="unknown")

    # Config class.
    if ext in _CONFIG_EXTENSIONS:
        return FilePolicy(file_class="config", subsystem="unknown")

    # Core AIOps implementation class.
    is_core_aiops = (
        "src/main/java/com/mindarray/aiops/" in rel
        or rel.startswith("runtime/")
        or "aiops" in parts
    )
    if is_core_aiops:
        return FilePolicy(file_class="core_aiops_code", subsystem=infer_file_subsystem(relative_path))

    # Default code/supporting bucket.
    return FilePolicy(file_class="supporting_prod_code", subsystem=infer_file_subsystem(relative_path))


def infer_file_subsystem(relative_path: str) -> str:
    toks = _tokenize_path(relative_path)
    for subsystem, keywords in _SUBSYSTEM_KEYWORDS.items():
        if any(t in keywords for t in toks):
            return subsystem
    return "unknown"


def infer_query_subsystems(tokens: Iterable[str]) -> FrozenSet[str]:
    token_set = {t.lower() for t in tokens}
    matched = {
        subsystem
        for subsystem, keywords in _SUBSYSTEM_KEYWORDS.items()
        if token_set.intersection(keywords)
    }
    return frozenset(matched)


def looks_like_symbol_token(token: str) -> bool:
    t = token.strip()
    if not t:
        return False
    # Allow identifier-like and java/python-ish dotted names.
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_\.]*", t))


def is_noise_class(file_class: str) -> bool:
    return file_class in {"tests", "logs", "vendor_static", "generated_metrics_data"}

