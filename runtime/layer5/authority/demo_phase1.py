#!/usr/bin/env python3
"""
Phase 1 Foundation Demo.

Demonstrates:
1. Concept lookup from registry
2. Validation result (validated)
3. Stale case detection
"""

from datetime import datetime, timedelta
from pathlib import Path

from runtime.layer5.authority.registry_loader import load_registry
from runtime.layer5.authority.freshness import AuthorityState
from runtime.layer5.authority.validation import validate_concept


class MockCodeIndex:
    """Mock code index for demo."""

    def __init__(self, files_exist: bool = True, classes_exist: bool = True):
        self._files_exist = files_exist
        self._classes_exist = classes_exist

    def file_exists(self, path: str) -> bool:
        return self._files_exist

    def class_exists(self, path: str, class_name: str) -> bool:
        return self._classes_exist and self._files_exist

    def method_exists(self, path: str, class_name: str, method_name: str) -> bool:
        return self._classes_exist and self._files_exist

    def is_referenced(self, path: str):
        return None


def main():
    registry_path = Path(__file__).parent / "product_authority_registry.yaml"
    
    print("=" * 70)
    print("PHASE 1 FOUNDATION DEMO")
    print("=" * 70)
    
    # Load registry
    print("\n1. Loading Authority Registry...")
    registry = load_registry(registry_path)
    print(f"   Schema version: {registry.schema_version}")
    print(f"   Concepts loaded: {len(registry.concepts)}")
    print(f"   Concepts: {', '.join(registry.list_concepts())}")
    
    # Demo 1: Concept lookup
    print("\n" + "-" * 70)
    print("2. CONCEPT LOOKUP")
    print("-" * 70)
    
    query = "incident deduplication"
    print(f"\n   Query: \"{query}\"")
    
    match = registry.match_concept(query)
    if match:
        concept, match_type, confidence = match
        print(f"   Match type: {match_type}")
        print(f"   Confidence: {confidence}")
        print(f"   Concept: {concept.name}")
        print(f"   Primary owner: {concept.primary_owner.class_name}")
        print(f"   File: {concept.primary_owner.file}")
        print(f"   Aliases: {list(concept.aliases)[:3]}...")
    
    # Demo 2: Validation result (validated)
    print("\n" + "-" * 70)
    print("3. VALIDATION RESULT: VALIDATED")
    print("-" * 70)
    
    concept = registry.get_concept("incident_deduplication")
    index = MockCodeIndex(files_exist=True, classes_exist=True)
    
    result = validate_concept(concept, index)
    print(f"\n   Concept: {concept.name}")
    print(f"   Authority confidence: {concept.primary_owner.confidence}")
    print(f"   Verification source: {concept.verification.verification_source}")
    print(f"\n   Validation checks:")
    print(f"     file_exists: {result.checks.file_exists}")
    print(f"     class_exists: {result.checks.class_exists}")
    print(f"     method_exists: {result.checks.method_exists}")
    print(f"     freshness_ok: {result.checks.freshness_ok}")
    print(f"     days_since_verification: {result.checks.days_since_verification}")
    print(f"\n   → STATUS: {result.status.value.upper()}")
    print(f"   → All critical passed: {result.all_critical_passed}")
    print(f"   → Requires verification: {result.requires_verification}")
    
    # Demo 3: Stale case (missing file)
    print("\n" + "-" * 70)
    print("4. VALIDATION RESULT: STALE (missing file)")
    print("-" * 70)
    
    concept = registry.get_concept("alert_correlation")
    index = MockCodeIndex(files_exist=False, classes_exist=False)
    
    result = validate_concept(concept, index)
    print(f"\n   Concept: {concept.name}")
    print(f"   Primary owner file: {concept.primary_owner.file}")
    print(f"\n   Validation checks:")
    print(f"     file_exists: {result.checks.file_exists}")
    print(f"     class_exists: {result.checks.class_exists}")
    print(f"\n   → STATUS: {result.status.value.upper()}")
    print(f"   → All critical passed: {result.all_critical_passed}")
    print(f"   → Requires verification: {result.requires_verification}")
    
    # Demo 4: Stale candidate (stale verification)
    print("\n" + "-" * 70)
    print("5. VALIDATION RESULT: STALE_CANDIDATE (stale verification)")
    print("-" * 70)
    
    concept = registry.get_concept("incident_deduplication")
    index = MockCodeIndex(files_exist=True, classes_exist=True)
    
    # Simulate stale by using a reference time 100 days after verification
    stale_reference = concept.verification.last_verified_at + timedelta(days=100)
    
    result = validate_concept(concept, index, reference_time=stale_reference)
    print(f"\n   Concept: {concept.name}")
    print(f"   Authority confidence: {concept.primary_owner.confidence}")
    print(f"   Staleness threshold: {concept.verification.staleness_threshold_days} days")
    print(f"\n   Validation checks:")
    print(f"     file_exists: {result.checks.file_exists}")
    print(f"     class_exists: {result.checks.class_exists}")
    print(f"     freshness_ok: {result.checks.freshness_ok}")
    print(f"     days_since_verification: {result.checks.days_since_verification}")
    print(f"\n   → STATUS: {result.status.value.upper()}")
    print(f"   → Reason: verification is stale ({result.checks.days_since_verification} days > {concept.verification.staleness_threshold_days} threshold)")
    
    print("\n" + "=" * 70)
    print("PHASE 1 DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
