"""
Test script for Agentic Orchestrator

Tests the state machine with a sample request
"""

import asyncio
import json
import sys
import os

# Add orchestrator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.langgraph_orchestrator import Orchestrator

async def test_orchestrator():
    """Test the orchestrator with a sample request"""
    
    print("=" * 80)
    print("Testing Motadata Agentic Orchestrator")
    print("=" * 80)
    
    orchestrator = Orchestrator()
    
    # Test request
    user_request = "Create a new UserAPI endpoint in Motadata that handles user registration"
    
    codebase_context = {
        "primary_language": "Java",
        "frameworks": ["Vert.x"],
        "architectural_style": "Event-Driven",
        "existing_patterns": ["REST API", "Event Bus", "Async Processing"]
    }
    
    print(f"\n📝 User Request: {user_request}")
    print(f"📦 Codebase Context: {json.dumps(codebase_context, indent=2)}")
    
    print("\n⏳ Processing request through orchestrator...")
    print("-" * 80)
    
    try:
        result = await orchestrator.process_request(
            user_request=user_request,
            conversation_history=[],
            codebase_context=codebase_context
        )
        
        print("\n✅ Orchestrator completed successfully!")
        print("-" * 80)
        print("\n📊 Result:")
        print(json.dumps(result, indent=2))
        
        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Status: {result.get('status')}")
        print(f"Phase: {result.get('phase', 'N/A')}")
        if result.get('error'):
            print(f"Error: {result.get('error')}")
        if result.get('generated_code'):
            print(f"Generated Code Length: {len(result.get('generated_code', ''))} chars")
        if result.get('quality_score'):
            print(f"Quality Score: {result.get('quality_score')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_orchestrator())
    sys.exit(0 if success else 1)

