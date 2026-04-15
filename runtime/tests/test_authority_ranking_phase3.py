"""
Authority Ranking Tests (Phase 3).

Tests for:
- Authority-aware ranking with guarded boosts
- Distractor demotion
- Entry-point supportive boosts
- Feature flag behavior
- Generic-token overmatch prevention
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

import pytest

from runtime.layer5.authority.code_index_adapter import CodeIndexProtocol
from runtime.layer5.authority.code_index_models import (
    CallConfidence,
    CallEdge,
    ClassRecord,
    CodeIndex,
    EntryPointRecord,
    EntryPointType,
    FileRecord,
)
from runtime.layer5.authority.freshness import AuthorityState
from runtime.layer5.authority.ranking import (
    AuthorityRanker,
    RankedHit,
    RankingContext,
    RankingDiagnostics,
    get_ranking_diagnostics,
    rerank_hits,
)
from runtime.layer5.authority.ranking_config import RankingConfig
from runtime.layer5.authority.registry_loader import (
    AuthorityRegistry,
    Concept,
    Collaborator,
    Distractor,
    PrimaryOwner,
    Verification,
    load_registry,
)
from runtime.layer5.authority.validation import validate_concept


# Sample registry path
SAMPLE_REGISTRY_PATH = Path(__file__).parent.parent / "layer5" / "authority" / "product_authority_registry.yaml"


class MockCodeIndex:
    """Mock code index for testing."""

    def __init__(
        self,
        existing_files: Optional[set] = None,
        existing_classes: Optional[dict] = None,
        existing_methods: Optional[dict] = None,
        entry_points: Optional[dict] = None,
        callers: Optional[dict] = None,
        callees: Optional[dict] = None,
    ):
        self._files = existing_files or set()
        self._classes = existing_classes or {}
        self._methods = existing_methods or {}
        self._entry_points = entry_points or {}
        self._callers = callers or {}
        self._callees = callees or {}

    def file_exists(self, relative_path: str) -> bool:
        return relative_path in self._files

    def class_exists(self, relative_path: str, class_name: str) -> bool:
        return class_name in self._classes.get(relative_path, set())

    def method_exists(
        self, relative_path: str, class_name: str, method_name: str
    ) -> bool:
        key = (relative_path, class_name)
        return method_name in self._methods.get(key, set())

    def is_referenced(self, relative_path: str) -> Optional[bool]:
        return True if relative_path in self._files else None

    def get_entry_points_for_file(self, relative_path: str) -> List[EntryPointRecord]:
        return list(self._entry_points.get(relative_path, []))

    def get_direct_callers(self, class_name: str, method_name: str) -> List[CallEdge]:
        key = f"{class_name}.{method_name}"
        return list(self._callers.get(key, []))

    def get_direct_callees(self, class_name: str, method_name: str) -> List[CallEdge]:
        key = f"{class_name}.{method_name}"
        return list(self._callees.get(key, []))


def create_mock_registry() -> AuthorityRegistry:
    """Create a mock registry for testing."""
    return load_registry(SAMPLE_REGISTRY_PATH)


def create_validated_index(registry: AuthorityRegistry) -> MockCodeIndex:
    """Create an index where owner files exist."""
    concept = registry.get_concept("alert_correlation")
    owner_file = concept.primary_owner.file
    owner_class = concept.primary_owner.class_name
    
    return MockCodeIndex(
        existing_files={owner_file},
        existing_classes={owner_file: {owner_class}},
    )


def create_entry_point_index() -> MockCodeIndex:
    """Create an index with entry points."""
    handler_file = "motadata/src/main/java/com/mindarray/handlers/AlertEventHandler.java"
    owner_file = "src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java"
    
    ep = EntryPointRecord(
        entry_type=EntryPointType.EVENT_HANDLER,
        relative_path=handler_file,
        class_name="AlertEventHandler",
        method_name="handle",
        invokes=("correlationEngine.correlateDuplicateIncidents",),
    )
    
    return MockCodeIndex(
        existing_files={handler_file, owner_file},
        existing_classes={
            handler_file: {"AlertEventHandler"},
            owner_file: {"AvailabilityCorrelationEngine"},
        },
        entry_points={handler_file: [ep]},
    )


class TestRankingConfig:
    """Tests for ranking configuration."""

    def test_default_config(self):
        """Default config has reasonable values."""
        config = RankingConfig()
        
        assert config.enable_authority_reranking is True
        assert config.owner_boost_validated == 100.0
        assert config.owner_boost_stale_candidate == 40.0
        assert config.owner_boost_stale == 0.0
        assert config.distractor_penalty == -80.0

    def test_get_owner_boost(self):
        """Owner boost varies by authority status."""
        config = RankingConfig()
        
        assert config.get_owner_boost("validated") == 100.0
        assert config.get_owner_boost("stale_candidate") == 40.0
        assert config.get_owner_boost("unverified") == 30.0
        assert config.get_owner_boost("stale") == 0.0
        assert config.get_owner_boost("unknown") == 0.0


class TestAuthorityRanker:
    """Tests for AuthorityRanker."""

    def test_build_context_matches_concept(self):
        """build_context matches concept from query."""
        registry = create_mock_registry()
        ranker = AuthorityRanker(registry)
        
        context = ranker.build_context("alert correlation")
        
        assert context.matched_concept is not None
        assert context.matched_concept.name == "alert_correlation"
        assert context.owner_file is not None
        assert "AvailabilityCorrelationEngine" in context.owner_file

    def test_build_context_collects_collaborators(self):
        """build_context collects collaborator files."""
        registry = create_mock_registry()
        ranker = AuthorityRanker(registry)
        
        context = ranker.build_context("alert correlation")
        
        assert len(context.collaborator_files) > 0

    def test_build_context_collects_distractors(self):
        """build_context collects distractor files."""
        registry = create_mock_registry()
        ranker = AuthorityRanker(registry)
        
        context = ranker.build_context("incident deduplication")
        
        assert len(context.distractor_files) > 0


class TestValidatedAuthorityBoost:
    """Tests for validated authority getting full boost."""

    def test_validated_authority_full_boost(self):
        """Validated authority gets full owner boost."""
        registry = create_mock_registry()
        index = create_validated_index(registry)
        config = RankingConfig(owner_boost_validated=100.0)
        ranker = AuthorityRanker(registry, index, config)
        
        context = ranker.build_context("alert correlation")
        
        # Owner should be validated since file exists
        assert context.authority_status == "validated"
        
        hits = [
            ("src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java", 50.0),
            ("motadata/src/main/java/com/mindarray/other/OtherFile.java", 80.0),
        ]
        
        ranked = ranker.rank_hits(hits, context)
        
        # Owner should rank first due to boost
        assert ranked[0].file_path.endswith("AvailabilityCorrelationEngine.java")
        assert ranked[0].diagnostics.owner_boost == 100.0
        assert ranked[0].final_score == 150.0


class TestStaleCandidatePartialBoost:
    """Tests for stale_candidate getting partial boost only."""

    def test_stale_candidate_partial_boost(self):
        """Stale_candidate authority gets partial boost."""
        registry = create_mock_registry()
        # No index = unverified status
        config = RankingConfig(
            owner_boost_validated=100.0,
            owner_boost_unverified=30.0,
        )
        ranker = AuthorityRanker(registry, None, config)
        
        context = ranker.build_context("alert correlation")
        # Without index, status should be unverified
        assert context.authority_status == "unverified"
        
        hits = [
            ("src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java", 50.0),
            ("motadata/src/main/java/com/mindarray/other/OtherFile.java", 80.0),
        ]
        
        ranked = ranker.rank_hits(hits, context)
        
        owner = next(h for h in ranked if "AvailabilityCorrelationEngine" in h.file_path)
        # Should get unverified boost, not validated
        assert owner.diagnostics.owner_boost == 30.0


class TestStaleNoBoost:
    """Tests for stale authority getting no boost."""

    def test_stale_no_boost(self):
        """Stale authority gets no owner boost."""
        registry = create_mock_registry()
        # Create index where file doesn't exist (causes stale)
        index = MockCodeIndex(existing_files=set())
        config = RankingConfig(owner_boost_stale=0.0)
        ranker = AuthorityRanker(registry, index, config)
        
        context = ranker.build_context("alert correlation")
        # File doesn't exist = stale
        assert context.authority_status == "stale"
        
        hits = [
            ("src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java", 50.0),
        ]
        
        ranked = ranker.rank_hits(hits, context)
        
        assert ranked[0].diagnostics.owner_boost == 0.0


class TestDistractorDemotion:
    """Tests for distractor demotion."""

    def test_distractor_gets_demoted(self):
        """Distractor files receive penalty and get demoted."""
        registry = create_mock_registry()
        index = create_validated_index(registry)
        config = RankingConfig(
            distractor_penalty=-80.0,
            owner_boost_validated=100.0,
            same_package_boost=0.0,
        )
        ranker = AuthorityRanker(registry, index, config)
        
        context = ranker.build_context("incident deduplication")
        
        hits = [
            # Distractor with high lexical score (registry forbidden for incident_deduplication)
            ("src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java", 90.0),
            # Regular file
            ("motadata/src/main/java/com/mindarray/other/Other.java", 50.0),
        ]
        
        ranked = ranker.rank_hits(hits, context)
        
        distractor = next(h for h in ranked if "AvailabilityCorrelationEngine" in h.file_path)
        assert distractor.diagnostics.distractor_penalty == -80.0
        assert distractor.final_score == 10.0  # 90 - 80

    def test_generic_distractor_penalty(self):
        """Generic distractors (util, config) get mild penalty."""
        registry = create_mock_registry()
        config = RankingConfig(generic_distractor_penalty=-20.0)
        ranker = AuthorityRanker(registry, None, config)
        
        context = ranker.build_context("alert correlation")
        
        hits = [
            ("motadata/src/main/java/com/mindarray/util/SomeUtil.java", 60.0),
            ("motadata/src/main/java/com/mindarray/config/SomeConfig.java", 60.0),
            ("motadata/src/main/java/com/mindarray/service/RealService.java", 60.0),
        ]
        
        ranked = ranker.rank_hits(hits, context)
        
        util = next(h for h in ranked if "Util" in h.file_path)
        config_file = next(h for h in ranked if "Config" in h.file_path)
        service = next(h for h in ranked if "Service" in h.file_path)
        
        assert util.diagnostics.generic_distractor_penalty == -20.0
        assert config_file.diagnostics.generic_distractor_penalty == -20.0
        assert service.diagnostics.generic_distractor_penalty == 0.0


class TestEntryPointSupportiveBoost:
    """Tests for entry-point supportive (not overriding) boost."""

    def test_entry_point_does_not_override_owner(self):
        """Entry point boost is supportive, doesn't override owner."""
        registry = create_mock_registry()
        index = create_entry_point_index()
        config = RankingConfig(
            owner_boost_validated=100.0,
            entry_point_boost=20.0,
        )
        ranker = AuthorityRanker(registry, index, config)
        
        context = ranker.build_context("alert correlation")
        
        hits = [
            # Entry point with high lexical score
            ("motadata/src/main/java/com/mindarray/handlers/AlertEventHandler.java", 85.0),
            # Owner with lower lexical score
            ("src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java", 70.0),
        ]
        
        ranked = ranker.rank_hits(hits, context)
        
        # Owner should still rank first
        assert ranked[0].file_path.endswith("AvailabilityCorrelationEngine.java")
        assert ranked[0].rank == 1
        
        # Entry point should rank second
        assert ranked[1].file_path.endswith("AlertEventHandler.java")
        assert ranked[1].rank == 2


class TestMissingStructuralData:
    """Tests for graceful degradation with missing structural data."""

    def test_missing_code_index_no_crash(self):
        """Missing code index doesn't crash ranking."""
        registry = create_mock_registry()
        ranker = AuthorityRanker(registry, None)  # No index
        
        context = ranker.build_context("alert correlation")
        
        hits = [
            ("motadata/src/main/java/com/mindarray/SomeFile.java", 60.0),
        ]
        
        # Should not raise
        ranked = ranker.rank_hits(hits, context)
        assert len(ranked) == 1

    def test_empty_hits_no_crash(self):
        """Empty hits list doesn't crash."""
        registry = create_mock_registry()
        ranker = AuthorityRanker(registry)
        
        context = ranker.build_context("alert correlation")
        
        ranked = ranker.rank_hits([], context)
        assert ranked == []


class TestFeatureFlag:
    """Tests for feature flag behavior."""

    def test_feature_flag_off_preserves_order(self):
        """Feature flag OFF preserves original order."""
        registry = create_mock_registry()
        index = create_validated_index(registry)
        config = RankingConfig(enable_authority_reranking=False)
        ranker = AuthorityRanker(registry, index, config)
        
        context = ranker.build_context("alert correlation")
        
        hits = [
            ("motadata/src/main/java/com/mindarray/other/FileA.java", 100.0),
            ("src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java", 50.0),
            ("motadata/src/main/java/com/mindarray/other/FileB.java", 75.0),
        ]
        
        ranked = ranker.rank_hits(hits, context)
        
        # Original order preserved (by original score)
        assert ranked[0].file_path.endswith("FileA.java")
        assert ranked[1].file_path.endswith("AvailabilityCorrelationEngine.java")
        assert ranked[2].file_path.endswith("FileB.java")
        
        # Scores unchanged
        assert ranked[0].final_score == 100.0
        assert ranked[1].final_score == 50.0
        assert ranked[2].final_score == 75.0

    def test_feature_flag_on_reranks(self):
        """Feature flag ON applies authority reranking."""
        registry = create_mock_registry()
        index = create_validated_index(registry)
        config = RankingConfig(
            enable_authority_reranking=True,
            owner_boost_validated=100.0,
        )
        ranker = AuthorityRanker(registry, index, config)
        
        context = ranker.build_context("alert correlation")
        
        hits = [
            ("motadata/src/main/java/com/mindarray/other/FileA.java", 100.0),
            ("src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java", 50.0),
        ]
        
        ranked = ranker.rank_hits(hits, context)
        
        # Owner should now rank first due to boost
        assert ranked[0].file_path.endswith("AvailabilityCorrelationEngine.java")


class TestGenericTokenOvermatch:
    """Tests to prevent generic-token overmatch regression."""

    def test_generic_tokens_dont_match_concept(self):
        """Generic tokens alone should not match concepts."""
        registry = create_mock_registry()
        ranker = AuthorityRanker(registry)
        
        # These should not match any concept
        for query in ["correlation", "incident", "alert"]:
            context = ranker.build_context(query)
            assert context.matched_concept is None, f"'{query}' should not match"

    def test_specific_query_matches_concept(self):
        """Specific queries should match concepts."""
        registry = create_mock_registry()
        ranker = AuthorityRanker(registry)
        
        context = ranker.build_context("alert correlation engine")
        assert context.matched_concept is not None
        assert context.matched_concept.name == "alert_correlation"


class TestDeterminism:
    """Tests for deterministic ranking."""

    def test_same_input_same_output(self):
        """Same input produces same ranking."""
        registry = create_mock_registry()
        index = create_validated_index(registry)
        ranker = AuthorityRanker(registry, index)
        
        context = ranker.build_context("alert correlation")
        
        hits = [
            ("motadata/src/main/java/com/mindarray/FileA.java", 60.0),
            ("src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java", 50.0),
            ("motadata/src/main/java/com/mindarray/FileB.java", 70.0),
        ]
        
        ranked1 = ranker.rank_hits(hits, context)
        ranked2 = ranker.rank_hits(hits, context)
        
        assert len(ranked1) == len(ranked2)
        for r1, r2 in zip(ranked1, ranked2):
            assert r1.file_path == r2.file_path
            assert r1.final_score == r2.final_score
            assert r1.rank == r2.rank


class TestRankingDiagnostics:
    """Tests for ranking diagnostics."""

    def test_diagnostics_to_dict(self):
        """Diagnostics can be serialized."""
        diag = RankingDiagnostics(
            file_path="test.java",
            base_score=50.0,
            owner_boost=100.0,
            final_score=150.0,
            authority_status="validated",
            boost_reasons=["owner_boost(validated): +100.0"],
        )
        
        d = diag.to_dict()
        
        assert d["file_path"] == "test.java"
        assert d["base_score"] == 50.0
        assert d["owner_boost"] == 100.0
        assert d["final_score"] == 150.0
        assert d["authority_status"] == "validated"

    def test_get_ranking_diagnostics(self):
        """get_ranking_diagnostics extracts from ranked hits."""
        registry = create_mock_registry()
        ranker = AuthorityRanker(registry)
        
        context = ranker.build_context("alert correlation")
        hits = [("test.java", 50.0)]
        ranked = ranker.rank_hits(hits, context)
        
        diagnostics = get_ranking_diagnostics(ranked)
        
        assert len(diagnostics) == 1
        assert diagnostics[0]["file_path"] == "test.java"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_rerank_hits(self):
        """rerank_hits convenience function works."""
        registry = create_mock_registry()
        index = create_validated_index(registry)
        
        hits = [
            ("src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java", 50.0),
            ("motadata/src/main/java/com/mindarray/other/Other.java", 80.0),
        ]
        
        ranked = rerank_hits(hits, "alert correlation", registry, index)
        
        # Owner should rank first
        assert ranked[0].file_path.endswith("AvailabilityCorrelationEngine.java")


class TestCollaboratorBoost:
    """Tests for collaborator boost."""

    def test_collaborator_gets_boost(self):
        """Collaborator files get boost."""
        registry = create_mock_registry()
        index = create_validated_index(registry)
        config = RankingConfig(collaborator_boost=25.0)
        ranker = AuthorityRanker(registry, index, config)
        
        context = ranker.build_context("alert correlation")
        
        # Get a collaborator from the concept
        concept = context.matched_concept
        collaborator_file = list(context.collaborator_files)[0] if context.collaborator_files else None
        
        if collaborator_file:
            hits = [
                (collaborator_file, 60.0),
                ("motadata/src/main/java/com/mindarray/random/Random.java", 60.0),
            ]
            
            ranked = ranker.rank_hits(hits, context)
            
            collab = next((h for h in ranked if h.file_path == collaborator_file), None)
            if collab:
                assert collab.diagnostics.collaborator_boost == 25.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
