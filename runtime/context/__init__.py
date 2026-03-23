"""
Runtime context — M3.0 Repository Context Engine + M3.12 narrow repo-aware manifest.

M3.0: contracts, engine, selectors (deterministic context bundles).
M3.12: manifest_models, manifest_builder, doc_selector (deterministic doc ingestion and selection).
"""

from runtime.context.contracts import (
    ContextBundle,
    ContextBundleLimits,
    ContextBundleProvenance,
    ContextItem,
    ContextRequest,
    SelectedContextRef,
)
from runtime.context.doc_selector import select_from_manifest
from runtime.context.engine import ContextEngine, ContextEngineError, MissingExplicitFilesError
from runtime.context.manifest_builder import ManifestBuilder
from runtime.context.manifest_models import (
    IngestionConfig,
    ManifestEntry,
    RepoManifest,
    SectionRange,
)

__all__ = [
    "ContextBundle",
    "ContextBundleLimits",
    "ContextBundleProvenance",
    "ContextEngine",
    "ContextEngineError",
    "ContextItem",
    "ContextRequest",
    "IngestionConfig",
    "ManifestBuilder",
    "ManifestEntry",
    "MissingExplicitFilesError",
    "RepoManifest",
    "SectionRange",
    "SelectedContextRef",
    "select_from_manifest",
]
