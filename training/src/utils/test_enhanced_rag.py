"""
Test script for Enhanced RAG Service
Demonstrates intent detection, context gathering, and prompt building
"""

import sys
import json
from pathlib import Path

# Add rag_api to path
sys.path.insert(0, str(Path(__file__).parent / "rag_api"))

from intent_detector import IntentDetector
from context_gatherer import ContextGatherer
from prompt_builder import PromptBuilder
from enhanced_rag_service import EnhancedRAGService


def test_intent_detection():
    """Test intent detection with various queries"""
    print("\n" + "="*80)
    print("TEST 1: Intent Detection")
    print("="*80)
    
    detector = IntentDetector()
    
    test_cases = [
        "Create CorrectionProfile API with all required classes",
        "Modify DeviceController to add pagination support",
        "Refactor the authentication logic in UserService",
        "Explain how the SLOProfile class works",
        "Fix the bug in CredentialProfile where authentication fails",
        "Find all usages of ConfigStore in the codebase",
        "Add a new endpoint to handle device metrics",
    ]
    
    for query in test_cases:
        result = detector.detect(query)
        print(f"\nQuery: {query}")
        print(f"  Intent: {result.intent.value} (confidence: {result.confidence:.2f})")
        print(f"  Entities: {result.entities}")
        print(f"  Task Type: {result.task_type}")
        print(f"  Keywords: {result.keywords[:5]}")


def test_context_gathering():
    """Test context gathering for CREATE intent"""
    print("\n" + "="*80)
    print("TEST 2: Context Gathering (Mock)")
    print("="*80)
    
    # Note: This requires actual codebase, so we'll just show the structure
    print("\nContext gathering would retrieve:")
    print("  1. Similar entity files (e.g., CredentialProfile.java)")
    print("  2. ConfigStore files (e.g., CredentialProfileConfigStore.java)")
    print("  3. Schema files (e.g., credential-profiles.json)")
    print("  4. Registration patterns from APIRouter.java")
    print("  5. File lists for creation and modification")
    
    print("\nExample context structure:")
    example_context = {
        'intent': 'CREATE',
        'entities': ['CorrectionProfile'],
        'task_type': 'api',
        'files_to_create': [
            'src/main/java/com/mindarray/api/CorrectionProfile.java',
            'src/main/java/com/mindarray/store/CorrectionProfileConfigStore.java',
            'src/main/resources/entity-schemas/correction-profiles.json',
        ],
        'files_to_modify': [
            'src/main/java/com/mindarray/api/APIRouter.java',
        ],
        'reference_files': {
            'api_class': '[CredentialProfile.java content]',
            'config_store': '[CredentialProfileConfigStore.java content]',
            'schema': '[credential-profiles.json content]',
        },
        'patterns': {
            'registration': 'new CredentialProfile().init(settingsAPIRouter);'
        }
    }
    print(json.dumps(example_context, indent=2))


def test_prompt_building():
    """Test prompt building for different intents"""
    print("\n" + "="*80)
    print("TEST 3: Prompt Building")
    print("="*80)
    
    from intent_detector import IntentResult, Intent
    
    builder = PromptBuilder()
    
    # Test CREATE intent
    print("\n--- CREATE Intent Prompt ---")
    intent_result = IntentResult(
        intent=Intent.CREATE,
        confidence=0.9,
        entities=['CorrectionProfile'],
        keywords=['create', 'api', 'correction', 'profile'],
        task_type='api'
    )
    
    context = {
        'intent': 'CREATE',
        'entities': ['CorrectionProfile'],
        'task_type': 'api',
        'files_to_create': [
            'src/main/java/com/mindarray/api/CorrectionProfile.java',
            'src/main/java/com/mindarray/store/CorrectionProfileConfigStore.java',
        ],
        'files_to_modify': [
            'src/main/java/com/mindarray/api/APIRouter.java',
        ],
        'reference_files': {
            'api_class': 'public class CredentialProfile { ... }',
        },
        'patterns': {
            'registration': 'new CredentialProfile().init(settingsAPIRouter);'
        }
    }
    
    prompt = builder.build(intent_result, context, "Create CorrectionProfile API")
    print(prompt[:1000])  # Show first 1000 chars
    print("\n... [truncated] ...")
    
    # Test MODIFY intent
    print("\n--- MODIFY Intent Prompt ---")
    intent_result = IntentResult(
        intent=Intent.MODIFY,
        confidence=0.85,
        entities=['DeviceController'],
        keywords=['modify', 'add', 'pagination'],
        task_type='api'
    )
    
    context = {
        'intent': 'MODIFY',
        'entities': ['DeviceController'],
        'files_to_modify': [
            'src/main/java/com/mindarray/api/DeviceController.java',
        ],
        'existing_code': {
            'DeviceController': 'public class DeviceController { ... }'
        }
    }
    
    prompt = builder.build(intent_result, context, "Add pagination to DeviceController")
    print(prompt[:800])
    print("\n... [truncated] ...")


def test_full_pipeline():
    """Test the full enhanced RAG pipeline"""
    print("\n" + "="*80)
    print("TEST 4: Full Pipeline (Diagnostics)")
    print("="*80)
    
    # Note: This would require actual Qdrant and codebase
    print("\nFull pipeline would:")
    print("  1. Detect intent from query")
    print("  2. Gather comprehensive context")
    print("  3. Build optimized prompt")
    print("  4. Return structured response")
    
    print("\nExample response structure:")
    example_response = {
        'prompt': '[Optimized prompt with all context]',
        'intent': 'CREATE',
        'confidence': 0.9,
        'entities': ['CorrectionProfile'],
        'context': {
            'files_to_create': ['...'],
            'files_to_modify': ['...'],
            'reference_files': {'...': '...'},
        },
        'metadata': {
            'intent_detection_enabled': True,
            'task_type': 'api',
            'files_to_create': ['...'],
            'files_to_modify': ['...'],
            'reference_entity': 'CredentialProfile',
        }
    }
    print(json.dumps(example_response, indent=2))


if __name__ == "__main__":
    print("\n" + "="*80)
    print("ENHANCED RAG SERVICE - TEST SUITE")
    print("="*80)
    
    test_intent_detection()
    test_context_gathering()
    test_prompt_building()
    test_full_pipeline()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)

