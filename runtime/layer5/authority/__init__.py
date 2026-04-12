"""
Product Authority Layer — Foundation + Code Understanding + Ranking Module.

Provides:
- Authority registry loading and validation (Phase 1)
- Drift/freshness classification (Phase 1)
- Pre-boost structural validation (Phase 1)
- Code index building and extraction (Phase 2)
- Entry point detection (Phase 2)
- Call edge extraction (Phase 2)
- Authority-aware ranking fusion (Phase 3)
- Retrieval integration with feature flag (Phase 3)

Phase 1–3: Data + validation + structure + ranking. Phase 4: evidence bundle authority
payloads + Plan-Gate synthesis (see ``authority_evidence``, ``ask_service.authority_synthesis``).
"""

from runtime.layer5.authority.registry_loader import (
    AuthorityRegistry,
    load_registry,
    AuthorityRegistryError,
)
from runtime.layer5.authority.freshness import (
    is_stale,
    compute_authority_state,
    AuthorityState,
)
from runtime.layer5.authority.validation import (
    validate_authority,
    ValidationResult,
)
from runtime.layer5.authority.code_index_models import (
    CodeIndex,
    FileRecord,
    ClassRecord,
    MethodRecord,
    CallEdge,
    EntryPointRecord,
    EntryPointType,
)
from runtime.layer5.authority.code_index_builder import (
    build_index,
    CodeIndexBuilder,
)
from runtime.layer5.authority.code_index_adapter import (
    create_adapter,
    StructuredIndexAdapter,
    CodeIndexProtocol,
)
from runtime.layer5.authority.ranking_config import (
    RankingConfig,
    get_config,
)
from runtime.layer5.authority.ranking import (
    AuthorityRanker,
    RankedHit,
    RankingContext,
    RankingDiagnostics,
    rerank_hits,
    get_ranking_diagnostics,
)
from runtime.layer5.authority.retrieval_integration import (
    AuthorityRetrievalEnhancer,
    create_enhancer,
)

__all__ = [
    # Phase 1
    "AuthorityRegistry",
    "load_registry",
    "AuthorityRegistryError",
    "is_stale",
    "compute_authority_state",
    "AuthorityState",
    "validate_authority",
    "ValidationResult",
    # Phase 2
    "CodeIndex",
    "FileRecord",
    "ClassRecord",
    "MethodRecord",
    "CallEdge",
    "EntryPointRecord",
    "EntryPointType",
    "build_index",
    "CodeIndexBuilder",
    "create_adapter",
    "StructuredIndexAdapter",
    "CodeIndexProtocol",
    # Phase 3
    "RankingConfig",
    "get_config",
    "AuthorityRanker",
    "RankedHit",
    "RankingContext",
    "RankingDiagnostics",
    "rerank_hits",
    "get_ranking_diagnostics",
    "AuthorityRetrievalEnhancer",
    "create_enhancer",
]
