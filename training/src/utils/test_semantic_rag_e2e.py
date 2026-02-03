#!/usr/bin/env python3
"""
End-to-end test for semantic context integration in RAG API.

This test simulates the evaluation benchmark workflow:
1. Starts RAG API server (if not running)
2. Sends a chat completion request with expected_files
3. Verifies semantic context is used when method names are detected
4. Verifies full file fallback works when no method names
"""

import sys
import os
import requests
import time

# Test configuration
RAG_API_URL = "http://localhost:8081"
TEST_WORKSPACE = "/home/harshil/TestMotadataProject/Motadata/motadata"


def check_rag_api_health():
    """Check if RAG API is running"""
    try:
        response = requests.get(f"{RAG_API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def test_semantic_context_with_method_name():
    """Test that semantic context is used when method name is in query"""

    # Task with explicit method name (using a real file and method that exists)
    # Note: The method name must be in camelCase to be detected
    payload = {
        "messages": [
            {"role": "user", "content": "Add logging to runRetention method"}
        ],
        "model": "motadata-coder",
        "temperature": 0.1,
        "max_tokens": 2048,
        "stream": False,
        "use_rag": True,
        "workspace_root": TEST_WORKSPACE,
        "expected_files": [
            "src/main/java/com/mindarray/datastore/DatastoreConstants.java"
        ]
    }
    
    print("Test 1: Sending request with method name in query...")
    response = requests.post(
        f"{RAG_API_URL}/v1/chat/completions",
        json=payload,
        timeout=120
    )
    
    if response.status_code != 200:
        print(f"✗ FAIL: API returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    
    # Check if semantic context was used (indicated by '#' in sources)
    rag_context = data.get('rag_context', {})
    sources = rag_context.get('sources', [])
    index_type = rag_context.get('index_type', '')
    
    print(f"  Sources: {sources}")
    print(f"  Index type: {index_type}")
    
    if index_type == 'semantic_context':
        print("✓ PASS: Semantic context was used")
        return True
    else:
        print(f"✗ FAIL: Expected semantic_context, got {index_type}")
        return False


def test_full_file_fallback():
    """Test that full file is used when no method name in query"""

    # Task without explicit method name (using a real file that exists)
    payload = {
        "messages": [
            {"role": "user", "content": "added change logs"}
        ],
        "model": "motadata-coder",
        "temperature": 0.1,
        "max_tokens": 2048,
        "stream": False,
        "use_rag": True,
        "workspace_root": TEST_WORKSPACE,
        "expected_files": [
            "src/main/java/com/mindarray/datastore/DatastoreConstants.java"
        ]
    }
    
    print("\nTest 2: Sending request without method name in query...")
    response = requests.post(
        f"{RAG_API_URL}/v1/chat/completions",
        json=payload,
        timeout=120
    )
    
    if response.status_code != 200:
        print(f"✗ FAIL: API returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    
    # Check if full file was used
    rag_context = data.get('rag_context', {})
    index_type = rag_context.get('index_type', '')
    
    print(f"  Index type: {index_type}")
    
    if index_type == 'workspace_files':
        print("✓ PASS: Full file fallback was used")
        return True
    else:
        print(f"✗ FAIL: Expected workspace_files, got {index_type}")
        return False


def main():
    print("=" * 60)
    print("End-to-End Semantic Context Integration Test")
    print("=" * 60)
    print()
    
    # Check if RAG API is running
    if not check_rag_api_health():
        print("✗ RAG API is not running at", RAG_API_URL)
        print("  Start it with: cd rag-system && source venv/bin/activate && python rag_api.py")
        return 1
    
    print("✓ RAG API is running")
    print()
    
    # Run tests
    test1_pass = test_semantic_context_with_method_name()
    test2_pass = test_full_file_fallback()
    
    print()
    if test1_pass and test2_pass:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

