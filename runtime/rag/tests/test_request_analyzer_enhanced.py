"""
Enhanced Integration Tests for Request Analyzer Agent
Tests error handling, validation, and metrics
"""

import asyncio
import json
import sys
import os
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.agents.request_analyzer import RequestAnalyzerAgent


async def test_valid_request():
    """Test successful request analysis"""
    print("\n" + "=" * 80)
    print("TEST 1: Valid Request Analysis")
    print("=" * 80)
    
    agent = RequestAnalyzerAgent()
    
    state = {
        "user_request": "Create a REST endpoint for user authentication",
        "conversation_history": ["Previous context"],
        "codebase_context": {
            "primary_language": "Java",
            "frameworks": ["Vert.x"],
            "architectural_style": "Event-Driven"
        }
    }
    
    try:
        result = await agent.run(state)
        
        print(f"✅ Status: {result['status']}")
        print(f"✅ Confidence: {result.get('confidence_score', 'N/A')}")
        print(f"✅ Latency: {result.get('latency_ms', 'N/A'):.2f}ms")
        
        assert result["status"] in ["VALID", "NEEDS_CLARIFICATION", "INVALID"]
        assert "extracted_requirements" in result
        assert "latency_ms" in result
        
        print("✅ TEST PASSED")
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await agent.close()


async def test_invalid_request():
    """Test with empty request - should FAIL"""
    print("\n" + "=" * 80)
    print("TEST 2: Invalid Request (Empty) - Should FAIL")
    print("=" * 80)

    agent = RequestAnalyzerAgent()

    state = {
        "user_request": "",
        "conversation_history": [],
        "codebase_context": {}
    }

    try:
        result = await agent.run(state)

        print(f"✅ Status: {result['status']}")
        print(f"✅ Error: {result.get('error', 'N/A')}")

        # This test validates that INVALID input is properly rejected
        assert result["status"] == "FAILED", f"Expected FAILED status, got {result['status']}"
        assert "error" in result, "Expected error message in response"

        print("✅ TEST PASSED - Invalid input correctly rejected")
        return True

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        return False
    finally:
        await agent.close()


async def test_metrics():
    """Test metrics tracking"""
    print("\n" + "=" * 80)
    print("TEST 3: Metrics Tracking")
    print("=" * 80)
    
    agent = RequestAnalyzerAgent()
    
    state = {
        "user_request": "Create a REST endpoint",
        "conversation_history": [],
        "codebase_context": {
            "primary_language": "Java",
            "frameworks": ["Vert.x"],
            "architectural_style": "Event-Driven"
        }
    }
    
    try:
        # Run multiple times
        for i in range(3):
            await agent.run(state)
        
        metrics = agent.get_metrics()
        
        print(f"✅ Total Requests: {metrics['total_requests']}")
        print(f"✅ Successful: {metrics['successful_analyses']}")
        print(f"✅ Success Rate: {metrics['success_rate']:.2%}")
        print(f"✅ Avg Latency: {metrics['avg_latency_ms']:.2f}ms")
        
        assert metrics["total_requests"] == 3
        assert metrics["avg_latency_ms"] > 0
        
        print("✅ TEST PASSED")
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        return False
    finally:
        await agent.close()


async def test_framework_validation():
    """Test framework validation - should reject unknown frameworks"""
    print("\n" + "=" * 80)
    print("TEST 4: Framework Validation - Should REJECT Unknown Frameworks")
    print("=" * 80)

    agent = RequestAnalyzerAgent()

    # Test with invalid framework
    state = {
        "user_request": "Create a REST endpoint using UnknownFramework",
        "conversation_history": [],
        "codebase_context": {
            "primary_language": "Java",
            "frameworks": ["Vert.x"],
            "architectural_style": "Event-Driven"
        }
    }

    try:
        result = await agent.run(state)

        print(f"✅ Status: {result['status']}")
        print(f"✅ Confidence: {result.get('confidence_score', 'N/A')}")

        # The agent should detect the unknown framework and mark as INVALID
        # OR it should ask for clarification
        assert result["status"] in ["INVALID", "NEEDS_CLARIFICATION"], \
            f"Expected INVALID or NEEDS_CLARIFICATION, got {result['status']}"

        print("✅ TEST PASSED - Unknown framework properly validated")
        return True

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await agent.close()


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("REQUEST ANALYZER AGENT - ENHANCED INTEGRATION TESTS")
    print("=" * 80)
    
    results = []
    
    results.append(("Valid Request", await test_valid_request()))
    results.append(("Invalid Request", await test_invalid_request()))
    results.append(("Metrics Tracking", await test_metrics()))
    results.append(("Framework Validation", await test_framework_validation()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(p for _, p in results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

