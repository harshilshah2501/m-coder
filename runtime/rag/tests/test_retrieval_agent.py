"""
Test Retrieval Agent
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.agents.retrieval_agent import RetrievalAgent

async def test_retrieval_agent():
    """Test the Retrieval Agent"""
    
    print("=" * 80)
    print("Testing Retrieval Agent")
    print("=" * 80)
    
    agent = RetrievalAgent()
    
    test_state = {
        "request_analysis": {
            "extracted_requirements": {
                "programming_language": "Java",
                "frameworks": ["Vert.x"],
                "functional_requirements": [
                    "Create a new UserAPI endpoint",
                    "Handle user registration with email validation"
                ]
            }
        },
        "task_type": "NEW_FEATURE"
    }
    
    print(f"\n📝 Test State: {json.dumps(test_state, indent=2)}")
    print("\n⏳ Retrieving patterns and examples...")
    
    try:
        result = await agent.run(test_state)
        
        print("\n✅ Retrieval Agent completed!")
        print("-" * 80)
        print("\n📊 Result:")
        print(json.dumps(result, indent=2))
        
        # Validate result
        assert "status" in result, "Missing 'status' in result"
        assert "retrieved_patterns" in result, "Missing 'retrieved_patterns'"
        assert "retrieved_examples" in result, "Missing 'retrieved_examples'"
        assert "coverage_score" in result, "Missing 'coverage_score'"
        
        print("\n✅ All validations passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await agent.close()

if __name__ == "__main__":
    success = asyncio.run(test_retrieval_agent())
    sys.exit(0 if success else 1)

