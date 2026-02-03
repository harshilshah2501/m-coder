"""
Test Coder Agent - Priority 1

Tests code generation quality and performance
"""

import asyncio
import json
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.agents.coder_agent import CoderAgent

async def test_coder_agent():
    """Test the Coder Agent with sample requests"""
    
    print("=" * 80)
    print("Testing Coder Agent (Priority 1)")
    print("=" * 80)
    
    agent = CoderAgent()
    
    test_cases = [
        {
            "name": "Simple REST Endpoint",
            "file_path": "src/main/java/com/motadata/api/UserAPI.java",
            "file_type": "NEW",
            "requirements": {
                "functional": [
                    "Create REST endpoint for user registration",
                    "Validate email format",
                    "Return user ID on success"
                ],
                "non_functional": [
                    "Response time < 100ms",
                    "Support 1000 concurrent requests"
                ]
            },
            "context": {
                "retrieved_patterns": [
                    {
                        "pattern_name": "REST API Pattern",
                        "snippet": "@RestController\npublic class UserController { ... }"
                    }
                ],
                "retrieved_examples": [],
                "architectural_guidelines": "Follow Vert.x async patterns"
            }
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n📝 Test: {test_case['name']}")
        print(f"   File: {test_case['file_path']}")
        
        start_time = time.time()
        
        try:
            result = await agent.run(test_case)
            elapsed = time.time() - start_time
            
            print(f"   Status: {result['status']}")
            print(f"   Latency: {elapsed:.2f}s")
            print(f"   Code Length: {len(result.get('generated_code', ''))} chars")
            print(f"   Confidence: {result.get('confidence_score', 0):.2f}")
            
            results.append({
                "test": test_case['name'],
                "status": result['status'],
                "latency": elapsed,
                "code_length": len(result.get('generated_code', '')),
                "confidence": result.get('confidence_score', 0)
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                "test": test_case['name'],
                "status": "FAILED",
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(json.dumps(results, indent=2))
    
    await agent.close()
    return all(r.get('status') == 'SUCCESS' for r in results)

if __name__ == "__main__":
    success = asyncio.run(test_coder_agent())
    sys.exit(0 if success else 1)

