"""
Deterministic file/subsystem classification and policy helpers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet, Iterable, Tuple

# PR-6 Slice 4: broad support / constants-style Java basenames (case-insensitive suffix).
# Slice 5: single *Util.java (distinct from *Utils.java) — config/helper pools.
_SUPPORT_STYLE_JAVA_SUFFIXES: Tuple[str, ...] = (
    "constants.java",
    "utils.java",
    "util.java",
    "helpers.java",
    "helper.java",
    "common.java",
    "config.java",
    "facade.java",
)


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

# Query tokens that imply code / debug / engineering investigation (PR-6 Slice 3).
# Intersection with normalized query tokens enables content gating without ML.
_CODE_DEBUG_INTENT_TOKENS: FrozenSet[str] = frozenset(
    {
        "alert",
        "alerts",
        "anomaly",
        "collector",
        "correlation",
        "debug",
        "delegation",
        "detector",
        "duplicate",
        "engine",
        "facade",
        "fail",
        "failing",
        "false",
        "graph",
        "helper",
        "incident",
        "incidents",
        "ingest",
        "ingestion",
        "inconsistency",
        "intermittently",
        "investigate",
        "issue",
        "metric",
        "metrics",
        "orchestrate",
        "parser",
        "pipeline",
        "positive",
        "positives",
        "service",
        "timeout",
        "topology",
        "trace",
        "utilities",
        "utility",
    }
)


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
    if "db-files" in parts:
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


def infer_code_debug_intent(tokens: Tuple[str, ...]) -> bool:
    """
    Deterministic code/debug/engineering intent for lexical retrieval.

    When True, Slice-3 content gating may zero content scores on noise file classes
    so log/JSON dumps cannot outrank ``src/main/java`` implementation files.
    """
    if not tokens:
        return False
    return bool(set(tokens) & _CODE_DEBUG_INTENT_TOKENS)


def infer_query_subsystems(tokens: Iterable[str]) -> FrozenSet[str]:
    token_set = {t.lower() for t in tokens}
    matched = {
        subsystem
        for subsystem, keywords in _SUBSYSTEM_KEYWORDS.items()
        if token_set.intersection(keywords)
    }
    return frozenset(matched)


def query_topology_focus(tokens: Tuple[str, ...]) -> bool:
    """
    PR-6 Slice 5: query is strongly topology/anomaly/graph oriented (not merely ``correlation``).
    Used to gate generic eventbus-handler content caps without hurting correlation-only queries.
    """
    ts = set(tokens)
    if "topology" in ts or "topo" in ts:
        return True
    if "anomaly" in ts and ("graph" in ts or "node" in ts or "detector" in ts):
        return True
    return False


def query_ingestion_focus(tokens: Tuple[str, ...]) -> bool:
    """
    PR-6 Slice 5: query is strongly ingestion/pipeline/parser/collector oriented.
    """
    ts = set(tokens)
    if "ingestion" in ts or "ingest" in ts:
        return True
    if "pipeline" in ts and ("parser" in ts or "metric" in ts or "metrics" in ts or "collector" in ts):
        return True
    if "parser" in ts and ("timeout" in ts or "metric" in ts or "metrics" in ts or "collector" in ts):
        return True
    if "collector" in ts and ("metric" in ts or "metrics" in ts):
        return True
    return False


def query_duplicate_incident_focus(tokens: Tuple[str, ...]) -> bool:
    """True when the query is about duplicate incidents (incident or incidents token)."""
    ts = set(tokens)
    if "duplicate" not in ts:
        return False
    return "incident" in ts or "incidents" in ts


def is_generic_eventbus_java_handler(relative_path: str, basename: str) -> bool:
    """
    Deterministic structural slot: ``.../eventbus/...`` + ``*Handler.java`` with ``handler`` in name.
    Not a filename blacklist — path role + naming pattern.
    """
    rel = relative_path.lower()
    b = basename.lower()
    if "/eventbus/" not in rel or not b.endswith(".java"):
        return False
    return "handler" in b


def is_support_style_java_basename(basename: str) -> bool:
    """
    Deterministic support / constants / helper-style Java file names.

    Used under code/debug intent to demote broad owners that often win on raw
    content repetition (e.g. ``*Constants.java``) vs behavioral classes.
    """
    b = basename.lower().strip()
    if not b.endswith(".java"):
        return False
    return any(b.endswith(s) for s in _SUPPORT_STYLE_JAVA_SUFFIXES)


def looks_like_symbol_token(token: str) -> bool:
    t = token.strip()
    if not t:
        return False
    # Allow identifier-like and java/python-ish dotted names.
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_\.]*", t))


def is_noise_class(file_class: str) -> bool:
    return file_class in {"tests", "logs", "vendor_static", "generated_metrics_data"}

