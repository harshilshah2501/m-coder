#!/usr/bin/env python3
"""
Surgical Data Generation for V15 Enhancement
Generate exactly 421 new examples to fill gaps
"""

import json
import random
from pathlib import Path
from typing import List, Dict

# SURGICAL TARGETS (from analysis)
TARGETS = {
    'multi_file': 154,      # Highest priority
    'refactoring': 144,     # Second highest
    'diff_generation': 54,  # Medium priority
    'file_creation': 44,    # Medium priority
    'code_review': 25       # Lower priority (already decent)
}

# Template patterns for each category
MULTI_FILE_PATTERNS = [
    "refactor_service_layer",
    "update_api_contract",
    "dependency_injection",
    "configuration_propagation",
    "interface_implementation",
    "shared_utility_update",
    "cross_module_refactor",
    "package_restructure"
]

REFACTORING_PATTERNS = [
    "extract_method",
    "extract_class",
    "inline_method",
    "move_method",
    "rename_variable",
    "introduce_parameter_object",
    "replace_conditional_with_polymorphism",
    "decompose_conditional",
    "consolidate_duplicate_code",
    "simplify_complex_logic"
]

CODE_REVIEW_PATTERNS = [
    "performance_review",
    "security_review",
    "best_practices_review",
    "design_pattern_review",
    "error_handling_review",
    "concurrency_review",
    "memory_leak_review",
    "api_design_review"
]

DIFF_GENERATION_PATTERNS = [
    "bug_fix_diff",
    "feature_addition_diff",
    "refactor_diff",
    "optimization_diff",
    "cleanup_diff"
]

FILE_CREATION_PATTERNS = [
    "new_service_class",
    "new_utility_class",
    "new_test_class",
    "new_configuration_file",
    "new_interface",
    "new_dto_class"
]


class TargetedExampleGenerator:
    """Generate examples with surgical precision"""
    
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.generated = []
    
    def generate_multi_file_example(self, pattern: str) -> Dict:
        """Generate multi-file coordination example"""
        # This would use templates or LLM to generate realistic examples
        # For now, return structure
        return {
            "messages": [
                {
                    "role": "user",
                    "content": f"Multi-file task: {pattern}"
                },
                {
                    "role": "assistant",
                    "content": f"Generated multi-file solution for {pattern}"
                }
            ],
            "metadata": {
                "category": "multi_file",
                "pattern": pattern,
                "complexity": "high",
                "files_affected": random.randint(2, 5)
            }
        }
    
    def generate_refactoring_example(self, pattern: str) -> Dict:
        """Generate refactoring example"""
        return {
            "messages": [
                {
                    "role": "user",
                    "content": f"Refactor using: {pattern}"
                },
                {
                    "role": "assistant",
                    "content": f"Generated refactoring for {pattern}"
                }
            ],
            "metadata": {
                "category": "refactoring",
                "pattern": pattern,
                "complexity": "medium"
            }
        }
    
    def generate_code_review_example(self, pattern: str) -> Dict:
        """Generate code review example"""
        return {
            "messages": [
                {
                    "role": "user",
                    "content": f"Review code for: {pattern}"
                },
                {
                    "role": "assistant",
                    "content": f"Generated review for {pattern}"
                }
            ],
            "metadata": {
                "category": "code_review",
                "pattern": pattern,
                "complexity": "medium"
            }
        }
    
    def generate_diff_example(self, pattern: str) -> Dict:
        """Generate diff generation example"""
        return {
            "messages": [
                {
                    "role": "user",
                    "content": f"Generate diff for: {pattern}"
                },
                {
                    "role": "assistant",
                    "content": f"Generated diff for {pattern}"
                }
            ],
            "metadata": {
                "category": "diff_generation",
                "pattern": pattern,
                "complexity": "low"
            }
        }
    
    def generate_file_creation_example(self, pattern: str) -> Dict:
        """Generate file creation example"""
        return {
            "messages": [
                {
                    "role": "user",
                    "content": f"Create new file: {pattern}"
                },
                {
                    "role": "assistant",
                    "content": f"Generated file for {pattern}"
                }
            ],
            "metadata": {
                "category": "file_creation",
                "pattern": pattern,
                "complexity": "medium"
            }
        }
    
    def generate_all(self):
        """Generate all targeted examples"""
        print("="*80)
        print("SURGICAL DATA GENERATION")
        print("="*80)
        print()
        
        total = sum(TARGETS.values())
        print(f"Target: {total} new examples")
        print()
        
        # Generate multi-file examples
        print(f"Generating {TARGETS['multi_file']} multi-file examples...")
        for i in range(TARGETS['multi_file']):
            pattern = random.choice(MULTI_FILE_PATTERNS)
            self.generated.append(self.generate_multi_file_example(pattern))
        
        # Generate refactoring examples
        print(f"Generating {TARGETS['refactoring']} refactoring examples...")
        for i in range(TARGETS['refactoring']):
            pattern = random.choice(REFACTORING_PATTERNS)
            self.generated.append(self.generate_refactoring_example(pattern))
        
        # Generate diff examples
        print(f"Generating {TARGETS['diff_generation']} diff examples...")
        for i in range(TARGETS['diff_generation']):
            pattern = random.choice(DIFF_GENERATION_PATTERNS)
            self.generated.append(self.generate_diff_example(pattern))
        
        # Generate file creation examples
        print(f"Generating {TARGETS['file_creation']} file creation examples...")
        for i in range(TARGETS['file_creation']):
            pattern = random.choice(FILE_CREATION_PATTERNS)
            self.generated.append(self.generate_file_creation_example(pattern))
        
        # Generate code review examples
        print(f"Generating {TARGETS['code_review']} code review examples...")
        for i in range(TARGETS['code_review']):
            pattern = random.choice(CODE_REVIEW_PATTERNS)
            self.generated.append(self.generate_code_review_example(pattern))
        
        print()
        print(f"✅ Generated {len(self.generated)} examples")
        print()
        
        # Save
        print(f"Saving to {self.output_path}...")
        with open(self.output_path, 'w') as f:
            for example in self.generated:
                f.write(json.dumps(example) + '\n')
        
        print("✅ Saved")
        print()
        print("="*80)
        print("NEXT STEPS:")
        print("="*80)
        print("1. Review generated examples for quality")
        print("2. Enhance with real code snippets")
        print("3. Merge with existing v15_gold.jsonl")
        print("4. Create new train/val/test splits")
        print("5. Re-train model")


if __name__ == "__main__":
    generator = TargetedExampleGenerator("datasets/v15_enhancement.jsonl")
    generator.generate_all()

