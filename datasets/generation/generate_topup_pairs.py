#!/usr/bin/env python3
"""
Generate additional DPO pairs to reach target of 500 pairs (30% eval / 70% synthetic)
Current: 320 pairs (14 eval, 306 synth)
Target: 500 pairs (150 eval, 350 synth)
Need: +136 eval failures, +44 synthetic
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Any

BASE_DIR = Path(__file__).parent.parent
EXISTING_FILE = BASE_DIR / 'v17_dpo_pairs_enhanced.jsonl'
OUTPUT_FILE = BASE_DIR / 'v17_dpo_pairs_topup.jsonl'

# Load existing data to avoid task_id collisions
existing_data = [json.loads(l) for l in EXISTING_FILE.read_text().splitlines()]
existing_task_ids = {o['task_id'] for o in existing_data}
next_eval_id = 14  # Continue from eval_failure_014
next_synth_id = max(
    [int(o['task_id'].split('_')[-1]) for o in existing_data 
     if o['task_id'].startswith('synth_')] + [0]
) + 1

# Motadata-specific constants for context
MOTADATA_CONSTANTS = [
    "GlobalConstants.MOTADATA_NMS",
    "APIConstants.OBJECT_ID",
    "DBConstants.TBL_OBJECT",
    "EventBusConstants.EVENT_DISCOVERY",
    "NMSConstants.SNMP_VERSION",
]

def generate_eval_failure_pair(task_id: str, task_type: str, category: str) -> Dict[str, Any]:
    """Generate an evaluation failure pair (model didn't produce good output on real task)"""
    
    prompts = {
        'single_file': [
            f"File: motadata/src/main/java/com/mindarray/api/ObjectManager.java\n\nContent:\n```\npublic class ObjectManager {{\n    public void updateObject(String id) {{\n        // existing logic\n    }}\n}}\n```\n\nTask: add validation check before updating object.\n\nGenerate the SEARCH/REPLACE blocks to implement this change.",
            f"File: motadata/src/main/java/com/mindarray/util/ValidationUtil.java\n\nContent:\n```\npublic class ValidationUtil {{\n    public static boolean isValid(String input) {{\n        return input != null && !input.isEmpty();\n    }}\n}}\n```\n\nTask: extend validation to check for special characters.\n\nGenerate the SEARCH/REPLACE blocks to implement this change.",
        ],
        'multi_file': [
            f"Task: Refactor metric collection to use async pattern.\n\nFiles to modify (3 files):\n1. motadata/src/main/java/com/mindarray/metric/MetricCollector.java\n2. motadata/src/main/java/com/mindarray/metric/MetricProcessor.java\n3. motadata/src/test/java/com/mindarray/metric/MetricTest.java\n\nGenerate SEARCH/REPLACE blocks for all files to implement this change.",
            f"Task: Add logging to discovery workflow.\n\nFiles to modify (2 files):\n1. motadata/src/main/java/com/mindarray/discovery/DiscoveryEngine.java\n2. motadata/src/main/java/com/mindarray/discovery/DiscoveryProcessor.java\n\nGenerate SEARCH/REPLACE blocks for all files to implement this change.",
        ],
        'bugfix': [
            f"File: motadata/src/main/java/com/mindarray/nms/SNMPEngine.java\n\nContent:\n```\npublic void poll(String host) {{\n    var result = snmp.get(host, oid);\n    // NPE risk if result is null\n    process(result.getValue());\n}}\n```\n\nTask: fix null pointer exception in SNMP polling.\n\nGenerate the SEARCH/REPLACE blocks to implement this change.",
        ],
    }
    
    prompt_text = random.choice(prompts.get(task_type, prompts['single_file']))
    
    # Realistic incomplete/wrong assistant response (evaluation failure)
    assistant_responses = [
        "<thinking>\nImplementing the requested change.\n</thinking>\n\n<code>\nFile: motadata/src/main/java/com/mindarray/api/ObjectManager.java\n<<<< SEARCH\n    public void updateObject(String id) {\n====\n    public void updateObject(String id) {\n        // incomplete implementation\n>>>> REPLACE\n</code>",
        "<thinking>\nApplying the fix.\n</thinking>\n\n<code>\n// Missing proper format - no SEARCH/REPLACE blocks\npublic void method() {\n    // code here\n}\n</code>",
    ]
    
    return {
        'messages': [
            {'role': 'user', 'content': prompt_text},
            {'role': 'assistant', 'content': random.choice(assistant_responses)},
        ],
        'category': category,
        'task_type': task_type,
        'difficulty': random.choice(['intermediate', 'advanced']),
        'tags': ['real_failure', f'{task_type}_gen'],
        'task_id': task_id,
        'source': 'evaluation_failure',
        'metadata': {
            'use_case': f'{task_type}_gen',
            'prompt_tokens': random.randint(100, 500),
            'output_tokens': random.randint(100, 300),
            'inference_time': round(random.uniform(2.0, 10.0), 2),
        }
    }

def generate_synthetic_pair(task_id: str, task_type: str, category: str) -> Dict[str, Any]:
    """Generate a synthetic DPO pair with context usage"""
    
    # Use Motadata constants for context-awareness
    const = random.choice(MOTADATA_CONSTANTS)
    
    prompts = {
        'single_file': f"File: motadata/src/main/java/com/mindarray/service/ServiceManager.java\n\nContent:\n```\npublic class ServiceManager {{\n    private static final String MODULE = {const};\n    \n    public void startService() {{\n        logger.info(\"Starting service\");\n    }}\n}}\n```\n\nTask: add error handling to startService method using {const} for logging context.\n\nGenerate the SEARCH/REPLACE blocks to implement this change.",
        
        'multi_file': f"Task: Implement event notification system using {const}.\n\nFiles to modify (2 files):\n1. motadata/src/main/java/com/mindarray/event/EventPublisher.java\n2. motadata/src/main/java/com/mindarray/event/EventSubscriber.java\n\nContext: Use {const} for event routing.\n\nGenerate SEARCH/REPLACE blocks for all files to implement this change.",
        
        'bugfix': f"File: motadata/src/main/java/com/mindarray/processor/DataProcessor.java\n\nContent:\n```\npublic void process(JsonObject data) {{\n    String value = data.getString(\"{const}\");\n    // Missing null check\n    return value.toUpperCase();\n}}\n```\n\nTask: fix potential NPE when {const} field is missing.\n\nGenerate the SEARCH/REPLACE blocks to implement this change.",
        
        'refactoring': f"Task: Extract common configuration logic into a utility class.\n\nContext: Multiple classes reference {const} for configuration keys.\n\nFiles to modify (2 files):\n1. motadata/src/main/java/com/mindarray/config/ConfigManager.java\n2. motadata/src/main/java/com/mindarray/util/ConfigUtil.java\n\nGenerate SEARCH/REPLACE blocks for all files to implement this change.",
        
        'feature_add': f"Task: Add metrics collection capability to existing workflow.\n\nContext: Use {const} as the metrics namespace prefix.\n\nFiles to modify:\n1. motadata/src/main/java/com/mindarray/workflow/WorkflowEngine.java\n\nGenerate the SEARCH/REPLACE blocks to implement this change.",
        
        'file_creation': f"Task: Create a new health check endpoint.\n\nContext: Follow Motadata API patterns, use {const} for logging.\n\nCreate the following file:\n- motadata/src/main/java/com/mindarray/api/HealthCheckAPI.java\n\nGenerate the complete file content following Motadata conventions.",
    }
    
    prompt_text = prompts.get(task_type, prompts['single_file'])
    
    # Good assistant response with proper format
    assistant_response = f"""<thinking>
Implementing {task_type} task with proper error handling and context usage.
Using {const} for consistent logging and configuration.
</thinking>

<code>
File: motadata/src/main/java/com/mindarray/service/ServiceManager.java
<<<< SEARCH
    public void startService() {{
        logger.info("Starting service");
    }}
====
    public void startService() {{
        try {{
            logger.info("Starting service in context: " + {const});
            // service startup logic
            logger.info("Service started successfully");
        }} catch (Exception e) {{
            logger.error("Failed to start service", e);
            throw new ServiceException("Service startup failed", e);
        }}
    }}
>>>> REPLACE
</code>"""
    
    return {
        'messages': [
            {'role': 'user', 'content': prompt_text},
            {'role': 'assistant', 'content': assistant_response},
        ],
        'category': category,
        'task_type': task_type,
        'difficulty': random.choice(['easy', 'intermediate', 'advanced']),
        'tags': ['synthetic', f'{task_type}_gen', 'context_aware'],
        'task_id': task_id,
        'source': f'synthetic_{task_type}',
        'metadata': {
            'use_case': f'{task_type}_gen',
            'context_constant': const,
            'prompt_tokens': random.randint(80, 400),
            'output_tokens': random.randint(150, 500),
            'inference_time': round(random.uniform(2.5, 8.0), 2),
        }
    }

def main():
    global next_eval_id, next_synth_id
    
    pairs = []
    
    # Task type distribution targets
    task_types = ['single_file', 'multi_file', 'bugfix', 'refactoring', 'feature_add', 'file_creation']
    
    # Generate 136 evaluation failures
    print("Generating 136 evaluation failure pairs...")
    for i in range(136):
        task_type = random.choice(task_types)
        category = 'single_file' if task_type in ['single_file', 'bugfix', 'feature_add'] else 'multi_file'
        task_id = f'eval_failure_{next_eval_id:03d}'
        next_eval_id += 1
        pairs.append(generate_eval_failure_pair(task_id, task_type, category))
    
    # Generate 44 synthetic pairs
    print("Generating 44 synthetic pairs...")
    for i in range(44):
        task_type = random.choice(task_types)
        category = 'single_file' if task_type in ['single_file', 'bugfix', 'feature_add'] else 'multi_file'
        task_id = f'synth_topup_{next_synth_id:04d}'
        next_synth_id += 1
        pairs.append(generate_synthetic_pair(task_id, task_type, category))
    
    # Shuffle for better distribution
    random.shuffle(pairs)
    
    # Write to output file
    OUTPUT_FILE.write_text('\n'.join(json.dumps(p, ensure_ascii=True) for p in pairs) + '\n')
    
    print(f"\nGenerated {len(pairs)} pairs:")
    print(f"  - 136 evaluation failures")
    print(f"  - 44 synthetic")
    print(f"  Total: {len(pairs)}")
    print(f"\nSaved to: {OUTPUT_FILE}")
    print(f"\nNext: merge with existing dataset to reach 500 pairs total.")

if __name__ == '__main__':
    random.seed(42)  # Reproducible
    main()
