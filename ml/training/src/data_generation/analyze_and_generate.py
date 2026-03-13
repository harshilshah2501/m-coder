#!/usr/bin/env python3
"""
Analyze existing examples and generate high-quality targeted examples
Uses existing patterns as templates for surgical precision
"""

import json
import random
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple

# Surgical targets
TARGETS = {
    'multi_file': 154,
    'refactoring': 144,
    'diff_generation': 54,
    'file_creation': 44,
    'code_review': 25
}


class SurgicalDataGenerator:
    """Generate examples with surgical precision based on existing patterns"""
    
    def __init__(self, gold_dataset: str, output_path: str):
        self.gold_dataset = Path(gold_dataset)
        self.output_path = Path(output_path)
        self.examples_by_category = defaultdict(list)
        self.load_existing_examples()
    
    def load_existing_examples(self):
        """Load and categorize existing examples"""
        print("📊 Analyzing existing examples...")
        
        with open(self.gold_dataset, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    category = data.get('metadata', {}).get('category', 'unknown')
                    self.examples_by_category[category].append(data)
                except:
                    pass
        
        print(f"✅ Loaded {sum(len(v) for v in self.examples_by_category.values())} examples")
        for cat, examples in sorted(self.examples_by_category.items()):
            print(f"   {cat}: {len(examples)} examples")
        print()
    
    def analyze_pattern(self, example: Dict) -> Dict:
        """Extract pattern from existing example"""
        messages = example.get('messages', [])
        metadata = example.get('metadata', {})
        
        # Extract key characteristics
        user_msg = next((m['content'] for m in messages if m['role'] == 'user'), '')
        assistant_msg = next((m['content'] for m in messages if m['role'] == 'assistant'), '')
        
        return {
            'user_length': len(user_msg),
            'assistant_length': len(assistant_msg),
            'has_code': '```' in assistant_msg,
            'has_diff': '@@' in assistant_msg or 'diff' in assistant_msg.lower(),
            'complexity': metadata.get('complexity', 'medium'),
            'structure': self._analyze_structure(messages)
        }
    
    def _analyze_structure(self, messages: List[Dict]) -> str:
        """Analyze conversation structure"""
        if len(messages) == 2:
            return 'simple'
        elif len(messages) <= 4:
            return 'medium'
        else:
            return 'complex'
    
    def generate_variant(self, template: Dict, category: str, index: int) -> Dict:
        """Generate variant based on template"""
        # This is a placeholder - in production, this would use:
        # 1. LLM to generate variations
        # 2. Code analysis to extract real patterns
        # 3. Template-based generation with real code snippets
        
        messages = template.get('messages', [])
        metadata = template.get('metadata', {})
        
        # Create variant
        new_messages = []
        for msg in messages:
            new_msg = msg.copy()
            # Add variation marker
            if msg['role'] == 'user':
                new_msg['content'] = f"[Variant {index}] " + msg['content']
            new_messages.append(new_msg)
        
        return {
            'messages': new_messages,
            'metadata': {
                **metadata,
                'category': category,
                'variant_of': template.get('metadata', {}).get('id', 'unknown'),
                'generated': True,
                'generation_method': 'template_variant'
            }
        }
    
    def generate_for_category(self, category: str, count: int) -> List[Dict]:
        """Generate examples for specific category"""
        print(f"🔧 Generating {count} examples for {category}...")
        
        # Get existing examples as templates
        templates = self.examples_by_category.get(category, [])
        
        if not templates:
            print(f"   ⚠️  No templates found for {category}, using generic generation")
            templates = [self._create_generic_template(category)]
        
        generated = []
        for i in range(count):
            # Select random template
            template = random.choice(templates)
            
            # Generate variant
            variant = self.generate_variant(template, category, i + 1)
            generated.append(variant)
        
        print(f"   ✅ Generated {len(generated)} examples")
        return generated
    
    def _create_generic_template(self, category: str) -> Dict:
        """Create generic template when no examples exist"""
        return {
            'messages': [
                {
                    'role': 'user',
                    'content': f'Generic {category} task'
                },
                {
                    'role': 'assistant',
                    'content': f'Generic {category} response'
                }
            ],
            'metadata': {
                'category': category,
                'complexity': 'medium',
                'generated': True
            }
        }
    
    def generate_all(self) -> List[Dict]:
        """Generate all targeted examples"""
        print("="*80)
        print("SURGICAL DATA GENERATION - PATTERN-BASED")
        print("="*80)
        print()
        
        all_generated = []
        
        for category, count in TARGETS.items():
            generated = self.generate_for_category(category, count)
            all_generated.extend(generated)
        
        print()
        print(f"✅ Total generated: {len(all_generated)} examples")
        print()
        
        # Save
        print(f"💾 Saving to {self.output_path}...")
        with open(self.output_path, 'w') as f:
            for example in all_generated:
                f.write(json.dumps(example) + '\n')
        
        print("✅ Saved")
        return all_generated
    
    def generate_report(self, generated: List[Dict]):
        """Generate report on what was created"""
        print()
        print("="*80)
        print("GENERATION REPORT")
        print("="*80)
        print()
        
        by_category = defaultdict(int)
        for ex in generated:
            cat = ex.get('metadata', {}).get('category', 'unknown')
            by_category[cat] += 1
        
        print("Generated by category:")
        for cat, count in sorted(by_category.items()):
            print(f"  {cat:<25} {count:>4} examples")
        
        print()
        print("="*80)
        print("NEXT STEPS:")
        print("="*80)
        print("1. ⚠️  MANUAL REVIEW: These are template-based variants")
        print("2. 🔧 ENHANCE: Replace with real code snippets from codebase")
        print("3. ✅ VALIDATE: Check quality and correctness")
        print("4. 🔗 MERGE: Combine with v15_gold.jsonl")
        print("5. 🚀 RETRAIN: Fine-tune with enhanced dataset")


if __name__ == "__main__":
    generator = SurgicalDataGenerator(
        gold_dataset="datasets/v15_gold.jsonl",
        output_path="datasets/v15_enhancement_templates.jsonl"
    )
    
    generated = generator.generate_all()
    generator.generate_report(generated)

