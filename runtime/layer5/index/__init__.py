"""
A4 — Deterministic file-level workspace index (MVP).

Indexes only paths under ``WorkspaceIdentity.canonical_root`` from A2.
See package docstring in ``builder`` for lifecycle and determinism guarantees.
"""

from runtime.layer5.index.builder import build_file_index, index_matches_workspace
from runtime.layer5.index.config import FileIndexConfig
from runtime.layer5.index.models import FileIndexEntry, WorkspaceFileIndex
from runtime.layer5.index.symbol_inventory import (
    SymbolInventory,
    SymbolInventoryEntry,
    build_symbol_inventory,
    index_fingerprint,
    inventory_token_lookup,
    normalize_identifier_tokens,
    resolve_symbol_lookup_for_index,
)

__all__ = [
    "FileIndexConfig",
    "FileIndexEntry",
    "WorkspaceFileIndex",
    "SymbolInventory",
    "SymbolInventoryEntry",
    "normalize_identifier_tokens",
    "build_symbol_inventory",
    "inventory_token_lookup",
    "index_fingerprint",
    "resolve_symbol_lookup_for_index",
    "build_file_index",
    "index_matches_workspace",
]
