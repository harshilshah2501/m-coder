"""
Authority Foundation Tests (Phase 1).

Tests for:
- Registry loading and validation
- Concept matching
- Freshness/drift classification
- Pre-boost structural validation
"""

from __future__ import annotations

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pytest

from runtime.layer5.authority.code_index_adapter import CodeIndexProtocol
from runtime.layer5.authority.freshness import (
    AuthorityState,
    compute_authority_state,
    compute_freshness_result,
    days_since_verification,
    is_stale,
)
from runtime.layer5.authority.registry_loader import (
    AuthorityRegistry,
    AuthorityRegistryError,
    Concept,
    PrimaryOwner,
    Verification,
    load_registry,
)
from runtime.layer5.authority.validation import (
    ValidationResult,
    validate_authority,
    validate_concept,
)


class MockCodeIndex:
    """Mock code index for testing validation."""

    def __init__(
        self,
        existing_files: Optional[set] = None,
        existing_classes: Optional[dict] = None,
        existing_methods: Optional[dict] = None,
        referenced_files: Optional[set] = None,
    ):
        self._files = existing_files or set()
        self._classes = existing_classes or {}
        self._methods = existing_methods or {}
        self._referenced = referenced_files

    def file_exists(self, relative_path: str) -> bool:
        return relative_path in self._files

    def class_exists(self, relative_path: str, class_name: str) -> bool:
        return self._classes.get(relative_path, set()).__contains__(class_name)

    def method_exists(
        self, relative_path: str, class_name: str, method_name: str
    ) -> bool:
        key = (relative_path, class_name)
        return method_name in self._methods.get(key, set())

    def is_referenced(self, relative_path: str) -> Optional[bool]:
        if self._referenced is None:
            return None
        return relative_path in self._referenced


SAMPLE_REGISTRY_PATH = Path(__file__).parent.parent / "layer5" / "authority" / "product_authority_registry.yaml"


class TestRegistryLoader:
    """Tests for registry loading and validation."""

    def test_load_sample_registry(self):
        """Sample registry loads correctly."""
        registry = load_registry(SAMPLE_REGISTRY_PATH)
        
        assert registry.schema_version == "product_authority_registry.v1.1"
        assert len(registry.concepts) == 3
        assert "incident_deduplication" in registry.concepts
        assert "alert_correlation" in registry.concepts
        assert "alert_escalation" in registry.concepts

    def test_concept_structure(self):
        """Concept has all required fields."""
        registry = load_registry(SAMPLE_REGISTRY_PATH)
        concept = registry.get_concept("incident_deduplication")
        
        assert concept is not None
        assert concept.name == "incident_deduplication"
        assert concept.primary_owner.file.endswith("IncidentDeduplicationProcessor.java")
        assert concept.primary_owner.class_name == "IncidentDeduplicationProcessor"
        assert concept.primary_owner.method == "processDeduplication"
        assert concept.primary_owner.confidence == "high"
        assert len(concept.aliases) > 0
        assert "dedup" in concept.aliases
        assert len(concept.collaborators) > 0
        assert len(concept.forbidden_distractors) > 0

    def test_verification_metadata(self):
        """Verification metadata is parsed correctly."""
        registry = load_registry(SAMPLE_REGISTRY_PATH)
        concept = registry.get_concept("incident_deduplication")
        
        assert concept is not None
        assert concept.verification.verification_source == "code_trace"
        assert concept.verification.staleness_threshold_days == 90
        assert isinstance(concept.verification.last_verified_at, datetime)

    def test_invalid_schema_missing_concepts(self):
        """Invalid schema fails fast - missing concepts."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("schema_version: test\n")
            f.flush()
            
            with pytest.raises(AuthorityRegistryError) as exc:
                load_registry(f.name)
            
            assert "concepts" in str(exc.value)

    def test_invalid_schema_missing_primary_owner(self):
        """Invalid schema fails fast - missing primary_owner."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
schema_version: test
concepts:
  bad_concept:
    aliases: []
""")
            f.flush()
            
            with pytest.raises(AuthorityRegistryError) as exc:
                load_registry(f.name)
            
            assert "primary_owner" in str(exc.value)

    def test_invalid_confidence_value(self):
        """Invalid confidence value fails fast."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
schema_version: test
concepts:
  bad_concept:
    primary_owner:
      file: test.java
      class: Test
      confidence: invalid
    aliases: []
""")
            f.flush()
            
            with pytest.raises(AuthorityRegistryError) as exc:
                load_registry(f.name)
            
            assert "confidence" in str(exc.value).lower()

    def test_file_not_found(self):
        """Non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_registry("/nonexistent/path/registry.yaml")


class TestConceptMatching:
    """Tests for concept matching."""

    def test_exact_match(self):
        """Exact concept name matches."""
        registry = load_registry(SAMPLE_REGISTRY_PATH)
        result = registry.match_concept("incident_deduplication")
        
        assert result is not None
        concept, match_type, confidence = result
        assert concept.name == "incident_deduplication"
        assert match_type == "exact"
        assert confidence == 1.0

    def test_alias_match(self):
        """Alias matches."""
        registry = load_registry(SAMPLE_REGISTRY_PATH)
        result = registry.match_concept("dedup")
        
        assert result is not None
        concept, match_type, confidence = result
        assert concept.name == "incident_deduplication"
        assert match_type == "alias"
        assert confidence == 1.0

    def test_alias_in_query(self):
        """Alias found in longer query text."""
        registry = load_registry(SAMPLE_REGISTRY_PATH)
        result = registry.match_concept("where is duplicate incident handled")
        
        assert result is not None
        concept, match_type, confidence = result
        assert concept.name == "incident_deduplication"
        assert match_type == "alias"

    def test_partial_match(self):
        """Partial token match."""
        registry = load_registry(SAMPLE_REGISTRY_PATH)
        result = registry.match_concept("incident processing")
        
        # Should match incident_deduplication via token overlap
        assert result is not None
        concept, match_type, confidence = result
        assert match_type == "partial"
        assert confidence >= 0.5

    def test_no_match(self):
        """No match returns None."""
        registry = load_registry(SAMPLE_REGISTRY_PATH)
        result = registry.match_concept("completely unrelated query")
        
        assert result is None

    def test_list_concepts(self):
        """List all concept names."""
        registry = load_registry(SAMPLE_REGISTRY_PATH)
        concepts = registry.list_concepts()
        
        assert len(concepts) == 3
        assert "incident_deduplication" in concepts
        assert "alert_correlation" in concepts


class TestFreshnessClassification:
    """Tests for freshness/drift classification."""

    def test_is_stale_false(self):
        """Recent verification is not stale."""
        now = datetime.now()
        recent = now - timedelta(days=30)
        
        assert is_stale(recent, threshold_days=90, reference_time=now) is False

    def test_is_stale_true(self):
        """Old verification is stale."""
        now = datetime.now()
        old = now - timedelta(days=100)
        
        assert is_stale(old, threshold_days=90, reference_time=now) is True

    def test_days_since_verification(self):
        """Days calculation is correct."""
        now = datetime.now()
        past = now - timedelta(days=45)
        
        days = days_since_verification(past, reference_time=now)
        assert days == 45

    def test_compute_state_validated(self):
        """High confidence, not stale → VALIDATED."""
        state = compute_authority_state(
            confidence="high",
            stale=False,
            structural_validation_passed=True,
        )
        assert state == AuthorityState.VALIDATED

    def test_compute_state_stale_candidate_from_stale(self):
        """High confidence, stale, structural pass → STALE_CANDIDATE."""
        state = compute_authority_state(
            confidence="high",
            stale=True,
            structural_validation_passed=True,
        )
        assert state == AuthorityState.STALE_CANDIDATE

    def test_compute_state_stale_candidate_from_medium(self):
        """Medium confidence, not stale → STALE_CANDIDATE."""
        state = compute_authority_state(
            confidence="medium",
            stale=False,
            structural_validation_passed=True,
        )
        assert state == AuthorityState.STALE_CANDIDATE

    def test_compute_state_unverified(self):
        """Medium confidence, stale → UNVERIFIED."""
        state = compute_authority_state(
            confidence="medium",
            stale=True,
            structural_validation_passed=None,
        )
        assert state == AuthorityState.UNVERIFIED

    def test_compute_state_stale_from_structural_fail(self):
        """Structural validation fails → STALE."""
        state = compute_authority_state(
            confidence="high",
            stale=False,
            structural_validation_passed=False,
        )
        assert state == AuthorityState.STALE

    def test_compute_state_low_confidence(self):
        """Low confidence → always STALE."""
        state = compute_authority_state(
            confidence="low",
            stale=False,
            structural_validation_passed=True,
        )
        assert state == AuthorityState.STALE

    def test_freshness_result(self):
        """Complete freshness result."""
        now = datetime.now()
        recent = now - timedelta(days=30)
        
        result = compute_freshness_result(
            confidence="high",
            last_verified_at=recent,
            threshold_days=90,
            structural_validation_passed=True,
            reference_time=now,
        )
        
        assert result.state == AuthorityState.VALIDATED
        assert result.is_stale is False
        assert result.days_since_verification == 30
        assert result.confidence == "high"


class TestStructuralValidation:
    """Tests for pre-boost structural validation."""

    def test_validation_validated(self):
        """Valid owner returns VALIDATED."""
        index = MockCodeIndex(
            existing_files={"src/Test.java"},
            existing_classes={"src/Test.java": {"TestClass"}},
            existing_methods={("src/Test.java", "TestClass"): {"testMethod"}},
        )
        
        owner = PrimaryOwner(
            file="src/Test.java",
            class_name="TestClass",
            method="testMethod",
            confidence="high",
        )
        verification = Verification(
            last_verified_at=datetime.now() - timedelta(days=10),
            verification_source="test",
            staleness_threshold_days=90,
        )
        
        result = validate_authority(owner, verification, index)
        
        assert result.status == AuthorityState.VALIDATED
        assert result.checks.file_exists is True
        assert result.checks.class_exists is True
        assert result.checks.method_exists is True
        assert result.all_critical_passed is True
        assert result.requires_verification is False

    def test_validation_missing_file(self):
        """Missing file returns STALE."""
        index = MockCodeIndex(existing_files=set())
        
        owner = PrimaryOwner(
            file="src/Missing.java",
            class_name="Missing",
            confidence="high",
        )
        verification = Verification(
            last_verified_at=datetime.now() - timedelta(days=10),
            verification_source="test",
            staleness_threshold_days=90,
        )
        
        result = validate_authority(owner, verification, index)
        
        assert result.status == AuthorityState.STALE
        assert result.checks.file_exists is False
        assert result.all_critical_passed is False
        assert result.requires_verification is True

    def test_validation_missing_class(self):
        """Missing class returns STALE."""
        index = MockCodeIndex(
            existing_files={"src/Test.java"},
            existing_classes={"src/Test.java": {"OtherClass"}},
        )
        
        owner = PrimaryOwner(
            file="src/Test.java",
            class_name="MissingClass",
            confidence="high",
        )
        verification = Verification(
            last_verified_at=datetime.now() - timedelta(days=10),
            verification_source="test",
            staleness_threshold_days=90,
        )
        
        result = validate_authority(owner, verification, index)
        
        assert result.status == AuthorityState.STALE
        assert result.checks.file_exists is True
        assert result.checks.class_exists is False
        assert result.all_critical_passed is False

    def test_validation_stale_authority(self):
        """Stale authority with structural pass returns STALE_CANDIDATE."""
        index = MockCodeIndex(
            existing_files={"src/Test.java"},
            existing_classes={"src/Test.java": {"TestClass"}},
        )
        
        owner = PrimaryOwner(
            file="src/Test.java",
            class_name="TestClass",
            confidence="high",
        )
        verification = Verification(
            last_verified_at=datetime.now() - timedelta(days=100),
            verification_source="test",
            staleness_threshold_days=90,
        )
        
        result = validate_authority(owner, verification, index)
        
        assert result.status == AuthorityState.STALE_CANDIDATE
        assert result.checks.freshness_ok is False
        assert result.checks.days_since_verification >= 100
        assert result.requires_verification is True

    def test_validation_to_dict(self):
        """ValidationResult serializes to dict."""
        index = MockCodeIndex(
            existing_files={"src/Test.java"},
            existing_classes={"src/Test.java": {"TestClass"}},
        )
        
        owner = PrimaryOwner(
            file="src/Test.java",
            class_name="TestClass",
            confidence="high",
        )
        verification = Verification(
            last_verified_at=datetime.now() - timedelta(days=10),
            verification_source="test",
            staleness_threshold_days=90,
        )
        
        result = validate_authority(owner, verification, index)
        data = result.to_dict()
        
        assert data["status"] == "validated"
        assert data["checks"]["file_exists"] is True
        assert data["all_critical_passed"] is True

    def test_validate_concept(self):
        """validate_concept convenience wrapper works."""
        registry = load_registry(SAMPLE_REGISTRY_PATH)
        concept = registry.get_concept("incident_deduplication")
        
        index = MockCodeIndex(
            existing_files={concept.primary_owner.file},
            existing_classes={concept.primary_owner.file: {concept.primary_owner.class_name}},
            existing_methods={
                (concept.primary_owner.file, concept.primary_owner.class_name): {concept.primary_owner.method}
            },
        )
        
        result = validate_concept(concept, index)
        
        assert result.status == AuthorityState.VALIDATED
        assert result.all_critical_passed is True


class TestIntegration:
    """Integration tests combining all components."""

    def test_full_flow_validated(self):
        """Full flow: load registry → match concept → validate → VALIDATED."""
        registry = load_registry(SAMPLE_REGISTRY_PATH)
        
        match = registry.match_concept("incident deduplication")
        assert match is not None
        
        concept, match_type, confidence = match
        assert concept.name == "incident_deduplication"
        
        index = MockCodeIndex(
            existing_files={concept.primary_owner.file},
            existing_classes={concept.primary_owner.file: {concept.primary_owner.class_name}},
            existing_methods={
                (concept.primary_owner.file, concept.primary_owner.class_name): {concept.primary_owner.method}
            },
        )
        
        result = validate_concept(concept, index)
        
        assert result.status == AuthorityState.VALIDATED
        print(f"\n[VALIDATED] Concept: {concept.name}")
        print(f"  Primary owner: {concept.primary_owner.class_name}")
        print(f"  Status: {result.status.value}")
        print(f"  Checks: {result.to_dict()['checks']}")

    def test_full_flow_stale(self):
        """Full flow: load registry → match concept → validate → STALE."""
        registry = load_registry(SAMPLE_REGISTRY_PATH)
        
        concept = registry.get_concept("alert_correlation")
        assert concept is not None
        
        index = MockCodeIndex(existing_files=set())
        
        result = validate_concept(concept, index)
        
        assert result.status == AuthorityState.STALE
        print(f"\n[STALE] Concept: {concept.name}")
        print(f"  Primary owner file: {concept.primary_owner.file}")
        print(f"  Status: {result.status.value}")
        print(f"  Reason: file does not exist")

    def test_full_flow_stale_candidate(self):
        """Full flow: high confidence + stale verification + structural pass → STALE_CANDIDATE."""
        registry = load_registry(SAMPLE_REGISTRY_PATH)
        
        # Use incident_deduplication but simulate stale verification
        concept = registry.get_concept("incident_deduplication")
        assert concept is not None
        assert concept.primary_owner.confidence == "high"  # Must be high for STALE_CANDIDATE
        
        index = MockCodeIndex(
            existing_files={concept.primary_owner.file},
            existing_classes={concept.primary_owner.file: {concept.primary_owner.class_name}},
            existing_methods={
                (concept.primary_owner.file, concept.primary_owner.class_name): {concept.primary_owner.method}
            },
        )
        
        # Use a reference time that makes the verification stale
        from datetime import datetime, timedelta
        stale_reference = concept.verification.last_verified_at + timedelta(days=100)
        
        result = validate_concept(concept, index, reference_time=stale_reference)
        
        # High confidence + stale + structural pass = STALE_CANDIDATE
        assert result.status == AuthorityState.STALE_CANDIDATE
        assert result.checks.freshness_ok is False
        print(f"\n[STALE_CANDIDATE] Concept: {concept.name}")
        print(f"  Confidence: {concept.primary_owner.confidence}")
        print(f"  Days since verification: {result.checks.days_since_verification}")
        print(f"  Status: {result.status.value}")

    def test_full_flow_unverified(self):
        """Full flow: medium confidence + stale → UNVERIFIED."""
        registry = load_registry(SAMPLE_REGISTRY_PATH)
        
        # alert_escalation has medium confidence and stale verification
        concept = registry.get_concept("alert_escalation")
        assert concept is not None
        assert concept.primary_owner.confidence == "medium"
        
        index = MockCodeIndex(
            existing_files={concept.primary_owner.file},
            existing_classes={concept.primary_owner.file: {concept.primary_owner.class_name}},
        )
        
        result = validate_concept(concept, index)
        
        # Medium confidence + stale = UNVERIFIED
        assert result.status == AuthorityState.UNVERIFIED
        print(f"\n[UNVERIFIED] Concept: {concept.name}")
        print(f"  Confidence: {concept.primary_owner.confidence}")
        print(f"  Days since verification: {result.checks.days_since_verification}")
        print(f"  Status: {result.status.value}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
