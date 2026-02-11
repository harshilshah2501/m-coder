#!/usr/bin/env python3
"""
Test semantic context integration with a sample evaluation task.

This tests that:
1. When a task mentions method names, semantic context is extracted
2. When no method names, full file is used
3. The model generates proper diffs
"""

import requests
import json
import sys

RAG_API_URL = "http://localhost:5000"
WORKSPACE_ROOT = "/home/harshil/TestMotadataProject/Motadata/motadata"

def test_semantic_context_extraction():
    """Test 1: Verify semantic context extraction works"""
    print("=" * 60)
    print("Test 1: Semantic Context Extraction")
    print("=" * 60)
    
    # Test with a method name that exists
    payload = {
        "messages": [
            {"role": "user", "content": "Add logging to runRetention method in DatastoreConstants.java"}
        ],
        "model": "motadata-coder",
        "temperature": 0.1,
        "max_tokens": 2048,
        "stream": False,
        "use_rag": True,
        "workspace_root": WORKSPACE_ROOT,
        "expected_files": [
            "src/main/java/com/mindarray/datastore/DatastoreConstants.java"
        ]
    }
    
    response = requests.post(f"{RAG_API_URL}/v1/chat/completions", json=payload, timeout=60)
    
    if response.status_code != 200:
        print(f"✗ FAIL: API returned {response.status_code}")
        print(response.text)
        return False
    
    result = response.json()
    
    # Check if semantic context was used
    if "rag_context_info" in result:
        info = result["rag_context_info"]
        print(f"  Index type: {info.get('index_type')}")
        print(f"  Sources: {info.get('sources', [])}")
        
        if info.get("index_type") == "semantic_context":
            print("✓ PASS: Semantic context was used")
            return True
        else:
            print(f"✗ FAIL: Expected semantic_context, got {info.get('index_type')}")
            return False
    else:
        print("✗ FAIL: No rag_context_info in response")
        return False


def test_full_file_fallback():
    """Test 2: Verify full file fallback when no method name"""
    print("\n" + "=" * 60)
    print("Test 2: Full File Fallback")
    print("=" * 60)
    
    payload = {
        "messages": [
            {"role": "user", "content": "Add change logs to DatastoreConstants.java"}
        ],
        "model": "motadata-coder",
        "temperature": 0.1,
        "max_tokens": 2048,
        "stream": False,
        "use_rag": True,
        "workspace_root": WORKSPACE_ROOT,
        "expected_files": [
            "src/main/java/com/mindarray/datastore/DatastoreConstants.java"
        ]
    }
    
    response = requests.post(f"{RAG_API_URL}/v1/chat/completions", json=payload, timeout=60)
    
    if response.status_code != 200:
        print(f"✗ FAIL: API returned {response.status_code}")
        return False
    
    result = response.json()
    
    if "rag_context_info" in result:
        info = result["rag_context_info"]
        print(f"  Index type: {info.get('index_type')}")
        
        if info.get("index_type") == "workspace_files":
            print("✓ PASS: Full file fallback was used")
            return True
        else:
            print(f"✗ FAIL: Expected workspace_files, got {info.get('index_type')}")
            return False
    else:
        print("✗ FAIL: No rag_context_info in response")
        return False


def test_model_response_format():
    """Test 3: Verify model generates proper diff format"""
    print("\n" + "=" * 60)
    print("Test 3: Model Response Format")
    print("=" * 60)
    
    payload = {
        "messages": [
            {"role": "user", "content": "Add a debug log statement at the start of runRetention method"}
        ],
        "model": "motadata-coder",
        "temperature": 0.1,
        "max_tokens": 2048,
        "stream": False,
        "use_rag": True,
        "workspace_root": WORKSPACE_ROOT,
        "expected_files": [
            "src/main/java/com/mindarray/datastore/DatastoreConstants.java"
        ]
    }
    
    response = requests.post(f"{RAG_API_URL}/v1/chat/completions", json=payload, timeout=60)
    
    if response.status_code != 200:
        print(f"✗ FAIL: API returned {response.status_code}")
        return False
    
    result = response.json()
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    print(f"  Response length: {len(content)} chars")
    print(f"  First 200 chars: {content[:200]}")
    
    # Check for diff markers
    has_file_marker = "File:" in content
    has_diff_block = "```diff" in content or "```" in content
    
    if has_file_marker and has_diff_block:
        print("✓ PASS: Response contains proper diff format")
        return True
    else:
        print(f"✗ FAIL: Missing diff format (file_marker={has_file_marker}, diff_block={has_diff_block})")
        return False


def main():
    print("Testing Semantic Context Integration with Evaluation Tasks\n")
    
    # Check if RAG API is running
    try:
        response = requests.get(f"{RAG_API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ RAG API is running\n")
        else:
            print("✗ RAG API health check failed")
            return 1
    except Exception as e:
        print(f"✗ Cannot connect to RAG API: {e}")
        return 1
    
    # Run tests
    results = []
    results.append(("Semantic Context Extraction", test_semantic_context_extraction()))
    results.append(("Full File Fallback", test_full_file_fallback()))
    results.append(("Model Response Format", test_model_response_format()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

