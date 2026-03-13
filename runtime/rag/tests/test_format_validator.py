"""
Test Format Validator Agent - Priority 2

Tests validation accuracy with valid and invalid formats
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.agents.format_validator import FormatValidatorAgent

async def test_format_validator():
    """Test the Format Validator agent"""
    
    print("=" * 80)
    print("Testing Format Validator Agent (Priority 2)")
    print("=" * 80)
    
    validator = FormatValidatorAgent()
    
    test_cases = [
        {
            "name": "Valid Search/Replace Block",
            "code": """<<<< SEARCH
public void oldMethod() {
    return;
}
>>>>

>>>> REPLACE
public void newMethod() {
    System.out.println("Updated");
    return;
}
>>>>""",
            "expected_status": "VALID",
            "expected_errors": 0
        },
        {
            "name": "Mismatched Blocks",
            "code": """<<<< SEARCH
old code
>>>>

<<<< SEARCH
another old
>>>>

>>>> REPLACE
new code
>>>>""",
            "expected_status": "INVALID",
            "expected_errors": 1
        },
        {
            "name": "Unclosed Search Block",
            "code": """<<<< SEARCH
old code

>>>> REPLACE
new code""",
            "expected_status": "INVALID",
            "expected_errors": 2  # Unclosed blocks + mismatched
        },
        {
            "name": "Identical Search/Replace",
            "code": """<<<< SEARCH
same code
>>>>

>>>> REPLACE
same code
>>>>""",
            "expected_status": "INVALID",
            "expected_errors": 1
        },
        {
            "name": "Unbalanced Code Fences",
            "code": """```java
public class Test {
    // Missing closing fence""",
            "expected_status": "INVALID",
            "expected_errors": 1
        }
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        print(f"\n📝 Test: {test_case['name']}")
        
        state = {
            "generated_code": test_case['code'],
            "file_path": "src/main/java/Test.java",
            "file_type": "NEW"
        }
        
        result = await validator.run(state)
        
        status_match = result['status'] == test_case['expected_status']
        error_count_match = result['error_count'] == test_case['expected_errors']
        
        if status_match and error_count_match:
            print(f"   ✅ PASS")
            passed += 1
        else:
            print(f"   ❌ FAIL")
            if not status_match:
                print(f"      Expected status: {test_case['expected_status']}, Got: {result['status']}")
            if not error_count_match:
                print(f"      Expected {test_case['expected_errors']} errors, Got: {result['error_count']}")
            failed += 1
        
        results.append({
            "test": test_case['name'],
            "status": result['status'],
            "error_count": result['error_count'],
            "warning_count": result['warning_count'],
            "passed": status_match and error_count_match
        })
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {passed}/{len(test_cases)}")
    print(f"❌ Failed: {failed}/{len(test_cases)}")
    print(f"\nDetailed Results:")
    print(json.dumps(results, indent=2))
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(test_format_validator())
    sys.exit(0 if success else 1)

