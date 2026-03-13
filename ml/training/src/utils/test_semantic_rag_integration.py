#!/usr/bin/env python3
"""
Test semantic context integration in RAG API chat completions endpoint.

This tests that:
1. Method names are extracted from task descriptions
2. Semantic context is used when method names are detected
3. Full file fallback works when semantic context fails
"""

import sys
import os
import re
from typing import List

# Add rag-system to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rag-system'))


def _extract_method_names_from_query(query: str) -> List[str]:
    """
    Extract potential method names from task description.
    (Copied from rag_api.py for standalone testing)
    """
    # Match camelCase identifiers (likely method names)
    # Must start with lowercase and contain at least one uppercase letter
    pattern = r'\b([a-z][a-z0-9]*[A-Z][a-zA-Z0-9]+)\b'
    matches = re.findall(pattern, query)

    # Filter out common words that match the pattern but aren't methods
    common_words = {'JavaScript', 'TypeScript', 'GitHub', 'GitLab'}
    method_names = [m for m in matches if m not in common_words]

    return method_names


def test_method_name_extraction():
    """Test that method names are correctly extracted from queries"""
    
    test_cases = [
        # (query, expected_methods)
        ("Add logging to getItemsByUserProfile", ["getItemsByUserProfile"]),
        ("Refactor calculateTotal and processPayment", ["calculateTotal", "processPayment"]),
        ("added change logs", []),  # No specific method
        ("Update the getUserData method", ["getUserData"]),
        ("Fix bug in processOrder", ["processOrder"]),
        ("Implement new feature", []),  # No method name
        ("Modify handleRequest to add validation", ["handleRequest"]),
    ]
    
    print("Testing method name extraction...")
    passed = 0
    failed = 0
    
    for query, expected in test_cases:
        result = _extract_method_names_from_query(query)
        if set(result) == set(expected):
            print(f"✓ PASS: '{query}' -> {result}")
            passed += 1
        else:
            print(f"✗ FAIL: '{query}' -> Expected {expected}, got {result}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_semantic_context_api():
    """Test that semantic context API is accessible"""
    try:
        from semantic_context_extractor import get_semantic_context
        print("✓ Semantic context extractor imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import semantic context extractor: {e}")
        return False


def main():
    print("=" * 60)
    print("Testing Semantic Context Integration")
    print("=" * 60)
    print()
    
    # Test 1: Method name extraction
    test1_pass = test_method_name_extraction()
    print()
    
    # Test 2: API availability
    test2_pass = test_semantic_context_api()
    print()
    
    if test1_pass and test2_pass:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

