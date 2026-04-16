"""
Authority-Aware Ranking Module.

Implements deterministic ranking fusion that combines:
- Lexical base scores
- Authority owner boosts (guarded by validation status)
- Collaborator boosts
- Structural proximity boosts (caller/callee)
- Entry point supportive boosts
- Distractor penalties

Phase 3: Ranking logic. No Plan-Gate changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from runtime.layer5.authority.code_index_adapter import CodeIndexProtocol
from runtime.layer5.authority.freshness import AuthorityState
from runtime.layer5.authority.ranking_config import RankingConfig, get_config
from runtime.layer5.authority.registry_loader import AuthorityRegistry, Concept
from runtime.layer5.authority.validation import ValidationResult, validate_concept


@dataclass
class RankingDiagnostics:
    """Per-hit diagnostics for ranking transparency."""

    file_path: str
    base_score: float = 0.0
    owner_boost: float = 0.0
    collaborator_boost: float = 0.0
    caller_boost: float = 0.0
    callee_boost: float = 0.0
    entry_point_boost: float = 0.0
    same_package_boost: float = 0.0
    distractor_penalty: float = 0.0
    generic_distractor_penalty: float = 0.0
    final_score: float = 0.0
    authority_status: str = ""
    boost_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "file_path": self.file_path,
            "base_score": self.base_score,
            "owner_boost": self.owner_boost,
            "collaborator_boost": self.collaborator_boost,
            "caller_boost": self.caller_boost,
            "callee_boost": self.callee_boost,
            "entry_point_boost": self.entry_point_boost,
            "same_package_boost": self.same_package_boost,
            "distractor_penalty": self.distractor_penalty,
            "generic_distractor_penalty": self.generic_distractor_penalty,
            "final_score": self.final_score,
            "authority_status": self.authority_status,
            "boost_reasons": self.boost_reasons,
        }


@dataclass
class RankedHit:
    """A retrieval hit with authority-aware ranking."""

    file_path: str
    original_score: float
    final_score: float
    rank: int
    diagnostics: RankingDiagnostics


@dataclass
class RankingContext:
    """Context for ranking a set of hits."""

    matched_concept: Optional[Concept] = None
    authority_status: str = "unverified"
    validation_result: Optional[ValidationResult] = None
    owner_file: Optional[str] = None
    owner_class: Optional[str] = None
    owner_method: Optional[str] = None
    owner_package: Optional[str] = None
    collaborator_files: Set[str] = field(default_factory=set)
    distractor_files: Set[str] = field(default_factory=set)


class AuthorityRanker:
    """
    Authority-aware ranking engine.

    Consumes Phase 1 (registry + freshness) and Phase 2 (code index)
    to produce guarded ranking adjustments.
    """

    def __init__(
        self,
        registry: AuthorityRegistry,
        code_index: Optional[CodeIndexProtocol] = None,
        config: Optional[RankingConfig] = None,
    ) -> None:
        self.registry = registry
        self.code_index = code_index
        self.config = config or get_config()

    def build_context(
        self,
        query: str,
        *,
        concept: Optional[Concept] = None,
    ) -> RankingContext:
        """
        Build ranking context from query and optional concept.

        If concept not provided, attempts to match from query.
        """
        ctx = RankingContext()

        # Match concept if not provided
        if concept is None:
            match = self.registry.match_concept(query)
            if match:
                concept, match_type, confidence = match
                ctx.matched_concept = concept

        if concept:
            ctx.matched_concept = concept
            ctx.owner_file = concept.primary_owner.file
            ctx.owner_class = concept.primary_owner.class_name
            ctx.owner_method = concept.primary_owner.method

            # Extract package from owner file path
            ctx.owner_package = self._extract_package(concept.primary_owner.file)

            # Collect collaborator files
            ctx.collaborator_files = {c.file for c in concept.collaborators}

            # Collect distractor files
            ctx.distractor_files = {d.file for d in concept.forbidden_distractors}

            # Validate authority status
            if self.code_index:
                validation = validate_concept(concept, self.code_index)
                ctx.validation_result = validation
                ctx.authority_status = validation.status.value
            else:
                ctx.authority_status = "unverified"

        return ctx

    def compute_path_score(
        self,
        file_path: str,
        base_score: float,
        context: RankingContext,
    ) -> RankingDiagnostics:
        """
        Public wrapper for per-path authority-aware scoring (Stage B fusion).

        Applies the same rules as ``rank_hits`` without sorting.
        """
        return self._compute_score(file_path, base_score, context)

    def _extract_package(self, file_path: str) -> str:
        """Extract Java package from file path."""
        # motadata/src/main/java/com/mindarray/aiops/correlation/X.java
        # -> com.mindarray.aiops.correlation
        parts = file_path.replace("\\", "/").split("/")
        try:
            java_idx = parts.index("java")
            package_parts = parts[java_idx + 1 : -1]
            return ".".join(package_parts)
        except (ValueError, IndexError):
            return ""

    def rank_hits(
        self,
        hits: List[Tuple[str, float]],
        context: RankingContext,
    ) -> List[RankedHit]:
        """
        Rank hits using authority-aware scoring.

        Args:
            hits: List of (file_path, base_score) tuples.
            context: Ranking context with authority metadata.

        Returns:
            List of RankedHit sorted by final_score descending.
        """
        if not self.config.enable_authority_reranking:
            # Feature flag OFF: preserve original order
            return [
                RankedHit(
                    file_path=path,
                    original_score=score,
                    final_score=score,
                    rank=i + 1,
                    diagnostics=RankingDiagnostics(
                        file_path=path,
                        base_score=score,
                        final_score=score,
                        boost_reasons=["authority_reranking_disabled"],
                    ),
                )
                for i, (path, score) in enumerate(hits)
            ]

        # Compute scores for each hit
        scored_hits: List[Tuple[str, float, float, RankingDiagnostics]] = []

        for file_path, base_score in hits:
            diag = self._compute_score(file_path, base_score, context)
            scored_hits.append((file_path, base_score, diag.final_score, diag))

        # Sort by final_score descending
        scored_hits.sort(key=lambda x: x[2], reverse=True)

        # Assign ranks
        results: List[RankedHit] = []
        for rank, (file_path, orig_score, final_score, diag) in enumerate(
            scored_hits, start=1
        ):
            results.append(
                RankedHit(
                    file_path=file_path,
                    original_score=orig_score,
                    final_score=final_score,
                    rank=rank,
                    diagnostics=diag,
                )
            )

        return results

    def _compute_score(
        self,
        file_path: str,
        base_score: float,
        context: RankingContext,
    ) -> RankingDiagnostics:
        """Compute authority-aware score for a single hit."""
        diag = RankingDiagnostics(
            file_path=file_path,
            base_score=base_score,
            authority_status=context.authority_status,
        )

        score = base_score

        # 1. Owner boost (guarded by authority status)
        if context.owner_file and self._normalize_path(file_path) == self._normalize_path(
            context.owner_file
        ):
            owner_boost = self.config.get_owner_boost(context.authority_status)
            diag.owner_boost = owner_boost
            score += owner_boost
            diag.boost_reasons.append(
                f"owner_boost({context.authority_status}): +{owner_boost}"
            )

        # 2. Collaborator boost
        elif context.collaborator_files and self._normalize_path(file_path) in {
            self._normalize_path(f) for f in context.collaborator_files
        }:
            diag.collaborator_boost = self.config.collaborator_boost
            score += diag.collaborator_boost
            diag.boost_reasons.append(
                f"collaborator_boost: +{self.config.collaborator_boost}"
            )

        # 3. Distractor penalty (applies even if also matched elsewhere)
        if context.distractor_files and self._normalize_path(file_path) in {
            self._normalize_path(f) for f in context.distractor_files
        }:
            diag.distractor_penalty = self.config.distractor_penalty
            score += diag.distractor_penalty
            diag.boost_reasons.append(
                f"distractor_penalty: {self.config.distractor_penalty}"
            )

        # 4. Generic distractor penalty (conservative)
        elif self._is_generic_distractor(file_path):
            diag.generic_distractor_penalty = self.config.generic_distractor_penalty
            score += diag.generic_distractor_penalty
            diag.boost_reasons.append(
                f"generic_distractor_penalty: {self.config.generic_distractor_penalty}"
            )

        # 5. Structural proximity boosts (if code index available)
        if self.code_index and context.owner_class and context.owner_method:
            structural_boosts = self._compute_structural_boosts(
                file_path, context, diag
            )
            score += structural_boosts

        # 6. Same package boost
        if context.owner_package:
            file_package = self._extract_package(file_path)
            if file_package and file_package == context.owner_package:
                if diag.owner_boost == 0 and diag.collaborator_boost == 0:
                    diag.same_package_boost = self.config.same_package_boost
                    score += diag.same_package_boost
                    diag.boost_reasons.append(
                        f"same_package_boost: +{self.config.same_package_boost}"
                    )

        # Apply score floor
        score = max(score, self.config.min_score)
        diag.final_score = score

        return diag

    def _compute_structural_boosts(
        self,
        file_path: str,
        context: RankingContext,
        diag: RankingDiagnostics,
    ) -> float:
        """
        Compute structural proximity boosts.

        These are supportive only - never override owner truth.
        """
        total_boost = 0.0

        if not self.code_index or not context.owner_class:
            return total_boost

        # Get file record to extract classes
        file_rec = None
        if hasattr(self.code_index, "_index"):
            # StructuredIndexAdapter
            idx = getattr(self.code_index, "_index")
            get_file = getattr(idx, "get_file", None)
            if callable(get_file):
                file_rec = get_file(file_path)

        if not file_rec:
            return total_boost

        # Check caller/callee relationships
        for cls in getattr(file_rec, "classes", ()):
            for method in cls.methods:
                # Check if this method calls the owner
                callees = self.code_index.get_direct_callees(cls.name, method)
                for edge in callees:
                    if edge.target_class == context.owner_class:
                        if context.owner_method is None or edge.target_method == context.owner_method:
                            diag.caller_boost = self.config.caller_boost
                            total_boost += self.config.caller_boost
                            diag.boost_reasons.append(
                                f"caller_boost({cls.name}.{method} -> {context.owner_class}): +{self.config.caller_boost}"
                            )
                            break

                # Check if owner calls this method
                if context.owner_method:
                    callers = self.code_index.get_direct_callers(cls.name, method)
                    for edge in callers:
                        if edge.source_class == context.owner_class and edge.source_method == context.owner_method:
                            diag.callee_boost = self.config.callee_boost
                            total_boost += self.config.callee_boost
                            diag.boost_reasons.append(
                                f"callee_boost({context.owner_class}.{context.owner_method} calls {cls.name}.{method}): +{self.config.callee_boost}"
                            )
                            break

        # Check entry point boosts (supportive only)
        entry_points = self.code_index.get_entry_points_for_file(file_path)
        for ep in entry_points:
            # Check if entry point invokes owner
            owner_invoked = False
            for invoke in ep.invokes:
                if context.owner_class and context.owner_class.lower() in invoke.lower():
                    owner_invoked = True
                    break

            if owner_invoked:
                boost = self.config.entry_point_invokes_owner_boost
                diag.entry_point_boost += boost
                total_boost += boost
                diag.boost_reasons.append(
                    f"entry_point_invokes_owner({ep.class_name}.{ep.method_name}): +{boost}"
                )

        return total_boost

    def _is_generic_distractor(self, file_path: str) -> bool:
        """Check if file matches generic distractor patterns."""
        path_lower = file_path.lower()
        file_name = path_lower.split("/")[-1].replace(".java", "")

        for pattern in self.config.generic_distractor_patterns:
            if pattern in file_name:
                return True

        return False

    def _normalize_path(self, path: str) -> str:
        """Normalize file path for comparison."""
        return path.replace("\\", "/").lower()


def rerank_hits(
    hits: List[Tuple[str, float]],
    query: str,
    registry: AuthorityRegistry,
    code_index: Optional[CodeIndexProtocol] = None,
    config: Optional[RankingConfig] = None,
) -> List[RankedHit]:
    """
    Convenience function to rerank hits with authority awareness.

    Args:
        hits: List of (file_path, base_score) tuples.
        query: User query text.
        registry: Authority registry.
        code_index: Optional code index adapter.
        config: Optional ranking configuration.

    Returns:
        List of RankedHit sorted by final_score descending.
    """
    ranker = AuthorityRanker(registry, code_index, config)
    context = ranker.build_context(query)
    return ranker.rank_hits(hits, context)


def get_ranking_diagnostics(
    ranked_hits: List[RankedHit],
) -> List[Dict[str, Any]]:
    """Extract diagnostics from ranked hits."""
    return [hit.diagnostics.to_dict() for hit in ranked_hits]
