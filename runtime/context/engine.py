"""
Context engine — M3.0 Repository Context Engine.

Builds deterministic, revision-tied, auditable context bundles for the runtime
orchestrator. Selection and materialization are separated:

- Selectors produce SelectedContextRef objects (paths + reasons, no content).
- ContextEngine materializes file contents only after final selection, ordering,
  and cap enforcement.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from runtime.context.contracts import (
    ContextBundle,
    ContextBundleLimits,
    ContextBundleProvenance,
    ContextItem,
    ContextRequest,
    SelectedContextRef,
)
from runtime.context import selectors as sel


class ContextEngineError(Exception):
    """Base error for context engine failures."""


class MissingExplicitFilesError(ContextEngineError):
    """Raised when explicitly requested files are missing."""


class ContextEngine:
    """
    Deterministic repository context engine.

    Responsibilities:
    - validate request
    - run selectors in fixed order
    - collect SelectedContextRef objects
    - deduplicate by normalized path
    - apply stable ordering
    - enforce max_files and max_bytes
    - materialize file contents only after final selection
    - populate provenance and limits
    """

    SELECTOR_ORDER = ["direct", "siblings", "imports", "symbols"]

    def build_context_bundle(self, request: ContextRequest) -> ContextBundle:
        """Build a deterministic ContextBundle for the given request."""
        self._validate_request(request)
        root = Path(request.root_path).resolve()

        refs: List[SelectedContextRef] = []

        try:
            for name in self.SELECTOR_ORDER:
                if name not in request.selectors:
                    continue
                if name == "direct":
                    refs.extend(sel.select_direct(str(root), request))
                elif name == "siblings":
                    refs.extend(sel.select_siblings(str(root), refs))
                elif name == "imports":
                    refs.extend(sel.select_import_neighbors(str(root), refs))
                elif name == "symbols":
                    refs.extend(sel.select_symbol_hints(str(root), request.symbol_hints))
        except FileNotFoundError as e:
            # Wrap missing explicit files as a typed error.
            raise MissingExplicitFilesError(str(e)) from e

        deduped = self._deduplicate(refs)
        items, limits = self._materialize(root, deduped, request.max_files, request.max_bytes)

        provenance = ContextBundleProvenance(
            root_path=str(root),
            selectors=list(request.selectors),
            requested_files=list(request.files),
            symbol_hints=list(request.symbol_hints),
        )

        bundle = ContextBundle(
            task_id=request.task_id,
            revision=request.revision,
            created_at_utc=ContextBundle.now_utc(),
            items=items,
            limits=limits,
            provenance=provenance,
        )
        return bundle

    def _validate_request(self, request: ContextRequest) -> None:
        root = Path(request.root_path)
        if not root.exists() or not root.is_dir():
            raise ContextEngineError(f"root_path does not exist or is not a directory: {request.root_path}")
        if request.max_files <= 0:
            raise ContextEngineError(f"max_files must be positive, got {request.max_files}")
        if request.max_bytes <= 0:
            raise ContextEngineError(f"max_bytes must be positive, got {request.max_bytes}")

    def _deduplicate(self, refs: List[SelectedContextRef]) -> List[SelectedContextRef]:
        """
        Deduplicate by normalized path.

        Precedence: first occurrence wins, which is controlled by selector priority
        and SELECTOR_ORDER.
        """
        by_path: Dict[str, SelectedContextRef] = {}
        for r in refs:
            if r.path in by_path:
                continue
            by_path[r.path] = r
        # Stable, lexicographically sorted ordering by path.
        return [by_path[p] for p in sorted(by_path.keys())]

    def _materialize(
        self,
        root: Path,
        refs: List[SelectedContextRef],
        max_files: int,
        max_bytes: int,
    ) -> tuple[List[ContextItem], ContextBundleLimits]:
        """
        Materialize file contents for selected refs, enforcing caps.
        """
        items: List[ContextItem] = []
        total_bytes = 0
        truncated = False

        for r in refs:
            if len(items) >= max_files:
                truncated = True
                break
            file_path = (root / r.path).resolve()
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                # If a selected file goes missing between selection and materialization,
                # fail-closed rather than silently continue.
                raise ContextEngineError(f"Selected file missing or unreadable during materialization: {r.path}")
            byte_size = len(content.encode("utf-8"))
            if total_bytes + byte_size > max_bytes:
                truncated = True
                break

            items.append(
                ContextItem(
                    path=r.path,
                    content=content,
                    byte_size=byte_size,
                    selection_reason=r.selection_reason,
                )
            )
            total_bytes += byte_size

        limits = ContextBundleLimits(
            max_files=max_files,
            max_bytes=max_bytes,
            truncated=truncated,
        )
        return items, limits

