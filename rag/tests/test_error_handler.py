"""
Test Error Handler Agent - Priority 3

Tests error detection and fixing
"""

import asyncio
import json
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.agents.error_handler import ErrorHandlerAgent

async def test_error_handler():
    """Test the Error Handler agent"""
    
    print("=" * 80)
    print("Testing Error Handler Agent (Priority 3)")
    print("=" * 80)
    
    agent = ErrorHandlerAgent()
    
    test_cases = [
        {
            "name": "Code with Unmatched Braces",
            "code": """public class UserAPI {
    public void register(String email) {
        System.out.println("Registering: " + email);
    // Missing closing brace
}""",
            "should_have_errors": True
        },
        {
            "name": "Valid Code",
            "code": """public class UserAPI {
    public void register(String email) {
        System.out.println("Registering: " + email);
    }
}""",
            "should_have_errors": False
        },
        {
            "name": "Code with Extra Braces",
            "code": """public class UserAPI {
    public void register(String email) {
        System.out.println("Registering: " + email);
    }
}}""",
            "should_have_errors": True
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n📝 Test: {test_case['name']}")
        
        start_time = time.time()
        
        state = {
            "generated_code": test_case['code'],
            "file_path": "src/main/java/UserAPI.java"
        }
        
        result = await agent.run(state)
        elapsed = time.time() - start_time
        
        has_errors = result['status'] != 'NO_ERRORS'
        expected_errors = test_case['should_have_errors']
        
        if has_errors == expected_errors:
            print(f"   ✅ PASS")
        else:
            print(f"   ❌ FAIL")
        
        print(f"   Status: {result['status']}")
        print(f"   Latency: {elapsed:.2f}s")
        if result.get('fixes_applied'):
            print(f"   Fixes: {len(result['fixes_applied'])}")
        
        results.append({
            "test": test_case['name'],
            "status": result['status'],
            "has_errors": has_errors,
            "expected_errors": expected_errors,
            "latency": elapsed,
            "fixes_count": len(result.get('fixes_applied', []))
        })
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed = sum(1 for r in results if r['has_errors'] == r['expected_errors'])
    print(f"✅ Passed: {passed}/{len(test_cases)}")
    print(f"\nDetailed Results:")
    print(json.dumps(results, indent=2))
    
    await agent.close()
    return passed == len(test_cases)

if __name__ == "__main__":
    success = asyncio.run(test_error_handler())
    sys.exit(0 if success else 1)

