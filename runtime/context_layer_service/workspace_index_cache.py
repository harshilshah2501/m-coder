"""
In-process cache for WorkspaceFileIndex + authority CodeIndex keyed by workspace snapshot.

Service-latency only: does not change retrieval semantics. Bypass when git working tree is dirty.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple

from runtime.layer5.authority.code_index_models import CodeIndex
from runtime.layer5.index.models import WorkspaceFileIndex
from runtime.layer5.workspace.identity import WorkspaceIdentity


@dataclass(frozen=True)
class IndexCacheKey:
    """Snapshot key: root path + snapshot identity hash (not path alone)."""

    canonical_root: str
    snapshot_hash: str


@dataclass
class _CachedPair:
    file_index: WorkspaceFileIndex
    code_index: CodeIndex


class WorkspaceIndexCache:
    """
    LRU + optional TTL. Single-flight per key: concurrent misses wait on one builder.

    Only stores entries where authority ``CodeIndex`` build succeeded (same as uncached path).
    """

    def __init__(self, *, max_keys: int = 4, ttl_sec: float = 0.0) -> None:
        self._max_keys = max(1, int(max_keys))
        self._ttl_sec = float(ttl_sec)
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        # key_str -> _CachedPair
        self._lru: OrderedDict[str, Tuple[_CachedPair, float]] = OrderedDict()
        # key_str currently being built (single-flight)
        self._building: set[str] = set()

    def entry_count(self) -> int:
        with self._lock:
            return len(self._lru)

    @staticmethod
    def key_from_identity(identity: WorkspaceIdentity) -> IndexCacheKey:
        return IndexCacheKey(
            canonical_root=identity.canonical_root,
            snapshot_hash=(identity.snapshot_hash or identity.identity_hash),
        )

    @staticmethod
    def is_cacheable(identity: WorkspaceIdentity) -> bool:
        """False when git reports dirty — safest default."""
        rev = identity.revision
        if rev is None:
            return True
        if rev.is_dirty:
            return False
        return True

    def _key_str(self, key: IndexCacheKey) -> str:
        return f"{key.snapshot_hash}\n{key.canonical_root}"

    def _expired(self, stored_at: float) -> bool:
        if self._ttl_sec <= 0.0:
            return False
        return (time.monotonic() - stored_at) > self._ttl_sec

    def get_or_build(
        self,
        key: IndexCacheKey,
        build_fn: Callable[
            [],
            Tuple[WorkspaceFileIndex, Optional[CodeIndex], Dict[str, Any]],
        ],
    ) -> Tuple[WorkspaceFileIndex, Optional[CodeIndex], Dict[str, Any]]:
        """
        Returns ``(file_index, code_index, metrics)``.

        ``metrics`` includes ``index_cache_hit``, ``file_index_build_ms``, ``code_index_build_ms``.
        On cache hit, build ms values are ``0.0``.
        """
        ks = self._key_str(key)
        with self._cond:
            # LRU hit
            if ks in self._lru:
                pair_stored, stored_at = self._lru[ks]
                if not self._expired(stored_at):
                    self._lru.move_to_end(ks)
                    return (
                        pair_stored.file_index,
                        pair_stored.code_index,
                        {
                            "index_cache_hit": True,
                            "file_index_build_ms": 0.0,
                            "code_index_build_ms": 0.0,
                        },
                    )
                del self._lru[ks]

            while ks in self._building:
                self._cond.wait()
            # Another thread may have populated while we waited
            if ks in self._lru:
                pair_stored, stored_at = self._lru[ks]
                if not self._expired(stored_at):
                    self._lru.move_to_end(ks)
                    return (
                        pair_stored.file_index,
                        pair_stored.code_index,
                        {
                            "index_cache_hit": True,
                            "file_index_build_ms": 0.0,
                            "code_index_build_ms": 0.0,
                        },
                    )
                del self._lru[ks]

            self._building.add(ks)

        fi: Optional[WorkspaceFileIndex] = None
        ci: Optional[CodeIndex] = None
        partial: Dict[str, Any] = {}
        try:
            fi, ci, partial = build_fn()
        finally:
            with self._cond:
                self._building.discard(ks)
                if fi is not None and ci is not None:
                    self._lru[ks] = (_CachedPair(file_index=fi, code_index=ci), time.monotonic())
                    self._lru.move_to_end(ks)
                    while len(self._lru) > self._max_keys:
                        self._lru.popitem(last=False)
                self._cond.notify_all()

        if fi is None:
            raise RuntimeError("index cache build_fn did not return a file index")
        out = {
            "index_cache_hit": False,
            "file_index_build_ms": float(partial.get("file_index_build_ms", 0.0)),
            "code_index_build_ms": float(partial.get("code_index_build_ms", 0.0)),
        }
        return fi, ci, out
