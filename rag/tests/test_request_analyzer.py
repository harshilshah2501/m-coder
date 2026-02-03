"""
Test Request Analyzer Agent
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.agents.request_analyzer import RequestAnalyzerAgent

async def test_request_analyzer():
    """Test the Request Analyzer agent"""
    
    print("=" * 80)
    print("Testing Request Analyzer Agent")
    print("=" * 80)
    
    agent = RequestAnalyzerAgent()
    
    test_state = {
        "user_request": "Create a new UserAPI endpoint that handles user registration with email validation",
        "conversation_history": [],
        "codebase_context": {
            "primary_language": "Java",
            "frameworks": ["Vert.x"],
            "architectural_style": "Event-Driven"
        }
    }
    
    print(f"\n📝 Test Request: {test_state['user_request']}")
    print("\n⏳ Calling vLLM for analysis...")
    
    try:
        result = await agent.run(test_state)
        
        print("\n✅ Request Analyzer completed!")
        print("-" * 80)
        print("\n📊 Result:")
        print(json.dumps(result, indent=2))
        
        # Validate result
        assert "status" in result, "Missing 'status' in result"
        assert "extracted_requirements" in result, "Missing 'extracted_requirements' in result"
        assert "confidence_score" in result, "Missing 'confidence_score' in result"
        
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
    success = asyncio.run(test_request_analyzer())
    sys.exit(0 if success else 1)

