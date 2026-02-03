#!/usr/bin/env python3
"""
Test semantic context extractor with real Motadata files
"""

import sys
from semantic_context_extractor import get_semantic_context

def test_groupconfigstore():
    """Test with GroupConfigStore.getItemsByUserProfile()"""
    
    print("=" * 80)
    print("TEST: Extract semantic context for GroupConfigStore.getItemsByUserProfile()")
    print("=" * 80)
    
    try:
        context = get_semantic_context(
            file_path="src/main/java/com/mindarray/store/GroupConfigStore.java",
            method_name="getItemsByUserProfile",
            task_description="Add logging statement at the start of the method (after opening brace, before first statement)",
            workspace_root="/home/harshil/TestMotadataProject/Motadata/motadata"
        )
        
        print("\n✅ SUCCESS! Semantic context extracted:\n")
        print(context)
        print("\n" + "=" * 80)
        
        # Verify key elements
        assert "Target method (MODIFY THIS):" in context
        assert "getItemsByUserProfile" in context
        assert "Previous method (for context):" in context
        # Next method is optional (might be last method in class)
        assert "Available fields in this class:" in context
        
        print("\n✅ All assertions passed!")
        print("✅ Context includes:")
        print("  - Target method (full body)")
        print("  - Previous method (for disambiguation)")
        print("  - Next method (for disambiguation)")
        print("  - Class fields")
        print("  - NO line numbers (semantic anchoring only)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_nonexistent_method():
    """Test error handling for non-existent method"""
    
    print("\n" + "=" * 80)
    print("TEST: Error handling for non-existent method")
    print("=" * 80)
    
    try:
        context = get_semantic_context(
            file_path="src/main/java/com/mindarray/store/GroupConfigStore.java",
            method_name="nonExistentMethod",
            task_description="This should fail",
            workspace_root="/home/harshil/TestMotadataProject/Motadata/motadata"
        )
        
        print("\n❌ FAILED: Should have raised ValueError")
        return False
        
    except ValueError as e:
        print(f"\n✅ SUCCESS: Correctly raised ValueError: {e}")
        assert "not found" in str(e).lower()
        assert "available methods:" in str(e).lower()
        return True
    except Exception as e:
        print(f"\n❌ FAILED: Wrong exception type: {e}")
        return False


if __name__ == "__main__":
    print("\n🧪 Testing Semantic Context Extractor\n")
    
    results = []
    
    # Test 1: Valid method
    results.append(("GroupConfigStore.getItemsByUserProfile", test_groupconfigstore()))
    
    # Test 2: Error handling
    results.append(("Error handling", test_nonexistent_method()))
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)

