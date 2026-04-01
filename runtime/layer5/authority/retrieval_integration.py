"""
Authority-Aware Retrieval Integration.

Provides a post-retrieval reranking layer that applies authority-aware
scoring to lexical retrieval results.

Phase 3: Minimal integration behind feature flag. No Plan-Gate changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, TYPE_CHECKING

from runtime.layer5.authority.code_index_adapter import CodeIndexProtocol, create_adapter
from runtime.layer5.authority.code_index_builder import build_index
from runtime.layer5.authority.code_index_models import CodeIndex
from runtime.layer5.authority.ranking import (
    AuthorityRanker,
    RankedHit,
    RankingContext,
    get_ranking_diagnostics,
)
from runtime.layer5.authority.ranking_config import RankingConfig, get_config
from runtime.layer5.authority.registry_loader import AuthorityRegistry, load_registry

if TYPE_CHECKING:
    from runtime.layer5.retrieval.models import RetrievalHit, RetrievalResult


@dataclass
class AuthorityRetrievalConfig:
    """Configuration for authority-aware retrieval."""

    enable_authority_reranking: bool = True
    registry_path: Optional[Path] = None
    workspace_root: Optional[Path] = None
    ranking_config: Optional[RankingConfig] = None


class AuthorityRetrievalEnhancer:
    """
    Enhances retrieval results with authority-aware reranking.

    Usage:
        enhancer = AuthorityRetrievalEnhancer(registry, code_index)
        reranked = enhancer.enhance(retrieval_result)
    """

    def __init__(
        self,
        registry: AuthorityRegistry,
        code_index: Optional[CodeIndexProtocol] = None,
        config: Optional[RankingConfig] = None,
    ) -> None:
        self.registry = registry
        self.code_index = code_index
        self.ranker = AuthorityRanker(registry, code_index, config)
        self.config = config or get_config()

    def enhance(
        self,
        retrieval_result: "RetrievalResult",
        *,
        return_diagnostics: bool = False,
    ) -> Tuple[List[RankedHit], Optional[RankingContext]]:
        """
        Enhance retrieval result with authority-aware reranking.

        Args:
            retrieval_result: Original lexical retrieval result.
            return_diagnostics: Whether to include full context.

        Returns:
            Tuple of (reranked_hits, context if return_diagnostics else None)
        """
        if not self.config.enable_authority_reranking:
            # Feature flag OFF: convert to RankedHit without reranking
            hits = [
                RankedHit(
                    file_path=h.relative_path,
                    original_score=float(h.score),
                    final_score=float(h.score),
                    rank=i + 1,
                    diagnostics=None,
                )
                for i, h in enumerate(retrieval_result.hits)
            ]
            return hits, None

        # Build ranking context from query
        context = self.ranker.build_context(retrieval_result.query_raw)

        # Convert retrieval hits to (path, score) tuples
        lexical_hits = [
            (h.relative_path, float(h.score))
            for h in retrieval_result.hits
        ]

        # Rerank
        ranked_hits = self.ranker.rank_hits(lexical_hits, context)

        return ranked_hits, context if return_diagnostics else None

    def enhance_hits(
        self,
        hits: List[Tuple[str, float]],
        query: str,
    ) -> List[RankedHit]:
        """
        Enhance raw (path, score) hits with authority-aware reranking.

        Args:
            hits: List of (file_path, base_score) tuples.
            query: Query string for concept matching.

        Returns:
            List of RankedHit sorted by final_score descending.
        """
        context = self.ranker.build_context(query)
        return self.ranker.rank_hits(hits, context)


def create_enhancer(
    registry_path: Optional[Path] = None,
    workspace_root: Optional[Path] = None,
    code_index: Optional[CodeIndex] = None,
    config: Optional[RankingConfig] = None,
) -> AuthorityRetrievalEnhancer:
    """
    Create an authority retrieval enhancer.

    Args:
        registry_path: Path to authority registry YAML.
        workspace_root: Workspace root for code index building.
        code_index: Pre-built code index (optional).
        config: Ranking configuration.

    Returns:
        Configured AuthorityRetrievalEnhancer.

    Raises:
        FileNotFoundError: If registry_path doesn't exist.
    """
    # Load registry
    if registry_path is None:
        registry_path = Path(__file__).parent / "product_authority_registry.yaml"

    registry = load_registry(registry_path)

    # Build or use provided code index
    adapter: Optional[CodeIndexProtocol] = None
    if code_index is not None:
        adapter = create_adapter(code_index=code_index)
    elif workspace_root is not None:
        built_index = build_index(workspace_root)
        adapter = create_adapter(code_index=built_index)

    return AuthorityRetrievalEnhancer(registry, adapter, config)


def rerank_retrieval_result(
    retrieval_result: "RetrievalResult",
    registry: AuthorityRegistry,
    code_index: Optional[CodeIndexProtocol] = None,
    config: Optional[RankingConfig] = None,
) -> List[RankedHit]:
    """
    Convenience function to rerank a retrieval result.

    Args:
        retrieval_result: Lexical retrieval result.
        registry: Authority registry.
        code_index: Optional code index adapter.
        config: Optional ranking configuration.

    Returns:
        List of RankedHit sorted by final_score descending.
    """
    enhancer = AuthorityRetrievalEnhancer(registry, code_index, config)
    ranked_hits, _ = enhancer.enhance(retrieval_result)
    return ranked_hits
