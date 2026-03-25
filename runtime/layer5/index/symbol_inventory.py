"""
Deterministic Java symbol inventory for PR-6 retrieval grounding.

Scope is intentionally narrow:
- only Java files under src/main/java/com/mindarray/aiops/
- class/interface/enum/record and method symbols
- deterministic ordering and canonical JSON export
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Tuple

from runtime.layer5.index.models import WorkspaceFileIndex

_JAVA_ROOT_PREFIX = "src/main/java/com/mindarray/aiops/"
_PACKAGE_RE = re.compile(r"^\s*package\s+([a-zA-Z0-9_.]+)\s*;", re.MULTILINE)
_TYPE_RE = re.compile(r"\b(class|interface|enum|record)\s+([A-Za-z_][A-Za-z0-9_]*)\b")
# Line-scoped method-like pattern (reduces cross-line / chained-call false positives vs whole-file scan).
_METHOD_LINE_RE = re.compile(
    r"(?:public|protected|private)\s+"
    r"(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?"
    r"(?:abstract\s+)?(?:native\s+)?"
    r"(?:<[A-Za-z0-9_,\s]+>\s+)?"
    r"(?:[A-Za-z_][A-Za-z0-9_<>\[\]]*\s+)+"
    r"([a-zA-Z_][A-Za-z0-9_]*)\s*\("
)
# Package-private / default-access methods: no access modifier; same return-type + name + "(" shape.
_PACKAGE_PRIVATE_METHOD_LINE_RE = re.compile(
    r"(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?"
    r"(?:abstract\s+)?(?:native\s+)?"
    r"(?:<[A-Za-z0-9_,\s]+>\s+)?"
    r"(?:[A-Za-z_][A-Za-z0-9_<>\[\]]*\s+)+"
    r"([a-zA-Z_][A-Za-z0-9_]*)\s*\("
)

_MAX_SYMBOL_LOOKUP_CACHE_ENTRIES = 32
_SYMBOL_LOOKUP_CACHE: "OrderedDict[str, Mapping[str, Tuple[str, ...]]]" = OrderedDict()


def normalize_identifier_tokens(value: str) -> Tuple[str, ...]:
    """Split identifiers to deterministic lowercase tokens."""
    if not value:
        return ()
    # Split CamelCase boundaries and non-alnum delimiters.
    camel_split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    raw = re.split(r"[^A-Za-z0-9]+", camel_split)
    out: List[str] = []
    for t in raw:
        tok = t.strip().lower()
        if len(tok) < 2:
            continue
        out.append(tok)
    # Deduplicate and sort to keep canonical payload stable.
    return tuple(sorted(set(out)))


@dataclass(frozen=True)
class SymbolInventoryEntry:
    symbol_name: str
    relative_path: str
    package: str
    module: str
    normalized_tokens: Tuple[str, ...]

    def to_canonical_dict(self) -> Dict[str, object]:
        return {
            "symbol_name": self.symbol_name,
            "relative_path": self.relative_path,
            "package": self.package,
            "module": self.module,
            "normalized_tokens": list(self.normalized_tokens),
        }


@dataclass(frozen=True)
class SymbolInventory:
    schema_version: str
    canonical_root: str
    entries: Tuple[SymbolInventoryEntry, ...]

    def to_canonical_dict(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "canonical_root": self.canonical_root,
            "entries": [e.to_canonical_dict() for e in self.entries],
        }

    def canonical_json(self) -> str:
        return json.dumps(self.to_canonical_dict(), sort_keys=True, separators=(",", ":"))


def _module_from_path(relative_path: str) -> str:
    """
    Stable-ish module label: path under ``.../aiops/`` excluding the file name.

    Examples:
    - ``.../aiops/correlation/Foo.java`` -> ``correlation``
    - ``.../aiops/correlation/engine/Bar.java`` -> ``correlation/engine``
    """
    parts = relative_path.split("/")
    if "aiops" not in parts:
        return "unknown"
    idx = parts.index("aiops")
    rest = parts[idx + 1 : -1]
    if not rest:
        return "unknown"
    return "/".join(rest)


def _line_may_contain_package_private_method(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith("//") or s.startswith("*"):
        return False
    if re.search(r"\b(public|protected|private)\b", line):
        return False
    if re.search(r"\b(class|interface|enum|record)\s+\w+", line):
        return False
    if "(" not in line:
        return False
    if re.match(r"\s*(?:if|for|while|switch|catch|return|try|else|new)\b", line):
        return False
    # Skip obvious assignments / lambdas before '('
    head = line.split("(", 1)[0]
    if "=" in head and "==" not in head:
        return False
    return True


def _line_may_contain_method_definition(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith("//") or s.startswith("*"):
        return False
    if re.search(r"\b(class|interface|enum|record)\s+\w+", line):
        return False
    if not re.search(r"\b(public|protected|private)\b", line):
        return False
    if "(" not in line:
        return False
    if re.search(r"\b(if|for|while|switch|catch)\s*\(", line):
        return False
    return True


def _method_names_from_java_lines(text: str) -> List[str]:
    """Collect method names from public/protected/private and package-private definitions."""
    seen: set[str] = set()
    ordered: List[str] = []

    def _push(name: str) -> None:
        if name in {"if", "for", "while", "switch", "catch", "return", "new", "super", "this"}:
            return
        if name not in seen:
            seen.add(name)
            ordered.append(name)

    for line in text.splitlines():
        if _line_may_contain_method_definition(line):
            m = _METHOD_LINE_RE.search(line)
            if m:
                _push(m.group(1))
            continue
        if _line_may_contain_package_private_method(line):
            m = _PACKAGE_PRIVATE_METHOD_LINE_RE.search(line)
            if m:
                _push(m.group(1))
    return ordered


def _extract_symbols_from_java(relative_path: str, text: str) -> List[SymbolInventoryEntry]:
    package_match = _PACKAGE_RE.search(text)
    package_name = package_match.group(1) if package_match else ""
    module = _module_from_path(relative_path)

    symbols: Dict[str, SymbolInventoryEntry] = {}

    for _, name in _TYPE_RE.findall(text):
        tokens = normalize_identifier_tokens(name)
        symbols[name] = SymbolInventoryEntry(
            symbol_name=name,
            relative_path=relative_path,
            package=package_name,
            module=module,
            normalized_tokens=tokens,
        )

    for method_name in _method_names_from_java_lines(text):
        tokens = normalize_identifier_tokens(method_name)
        symbols[method_name] = SymbolInventoryEntry(
            symbol_name=method_name,
            relative_path=relative_path,
            package=package_name,
            module=module,
            normalized_tokens=tokens,
        )

    out = list(symbols.values())
    out.sort(key=lambda e: (e.relative_path, e.symbol_name))
    return out


def build_symbol_inventory(index: WorkspaceFileIndex) -> SymbolInventory:
    """
    Build deterministic symbol inventory for indexed AIOps Java sources.
    """
    root = Path(index.canonical_root)
    entries: List[SymbolInventoryEntry] = []
    for f in index.files:
        rel = f.relative_path
        if not rel.lower().endswith(".java"):
            continue
        if not rel.startswith(_JAVA_ROOT_PREFIX):
            continue
        p = root / rel
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        entries.extend(_extract_symbols_from_java(rel, text))
    entries.sort(key=lambda e: (e.relative_path, e.symbol_name))
    return SymbolInventory(
        schema_version="layer5.symbol_inventory.v1",
        canonical_root=index.canonical_root,
        entries=tuple(entries),
    )


def inventory_token_lookup(inventory: SymbolInventory) -> Mapping[str, Tuple[str, ...]]:
    """
    Map file path -> sorted symbol tokens for retrieval-time deterministic boosts.

    **Important:** Only symbol-derived tokens are included. Package/module strings are
    intentionally excluded — injecting package shards (``com``, ``mindarray``, …) would
    uniformly boost every file in the same package and flatten rankings.
    """
    by_path: Dict[str, set[str]] = {}
    for e in inventory.entries:
        cur = by_path.setdefault(e.relative_path, set())
        cur.update(e.normalized_tokens)
    return {k: tuple(sorted(v)) for k, v in by_path.items()}


def index_fingerprint(index: WorkspaceFileIndex) -> str:
    """
    Deterministic fingerprint for index content (invalidates cache when files change).
    """
    h = hashlib.sha256()
    h.update(index.workspace_identity_hash.encode("utf-8"))
    h.update(b"\0")
    for f in index.files:
        h.update(f.relative_path.encode("utf-8"))
        h.update(b"\0")
        h.update(str(f.size_bytes).encode("ascii"))
        h.update(b"\0")
        h.update(str(f.mtime_ns).encode("ascii"))
        h.update(b"\0")
    return h.hexdigest()


def resolve_symbol_lookup_for_index(index: WorkspaceFileIndex) -> Mapping[str, Tuple[str, ...]]:
    """
    Cached ``inventory_token_lookup(build_symbol_inventory(index))``.

    Avoids reparsing Java sources on every ``retrieve_lexical`` call for the same index.
    """
    fp = index_fingerprint(index)
    if fp in _SYMBOL_LOOKUP_CACHE:
        _SYMBOL_LOOKUP_CACHE.move_to_end(fp)
        return _SYMBOL_LOOKUP_CACHE[fp]

    inv = build_symbol_inventory(index)
    mapping: Mapping[str, Tuple[str, ...]] = dict(inventory_token_lookup(inv))
    _SYMBOL_LOOKUP_CACHE[fp] = mapping
    if len(_SYMBOL_LOOKUP_CACHE) > _MAX_SYMBOL_LOOKUP_CACHE_ENTRIES:
        _SYMBOL_LOOKUP_CACHE.popitem(last=False)
    return mapping
