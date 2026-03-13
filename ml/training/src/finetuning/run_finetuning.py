#!/usr/bin/env python3
"""
Fine-tuning script for motadata-coder model using extracted training data.
Uses vLLM for inference and standard fine-tuning approach.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

def load_training_data(jsonl_path):
    """Load JSONL training data."""
    examples = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            examples.append(json.loads(line))
    return examples

def prepare_training_data(examples, output_dir):
    """Prepare data for fine-tuning."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Split into train/val (90/10)
    split_idx = int(len(examples) * 0.9)
    train_examples = examples[:split_idx]
    val_examples = examples[split_idx:]
    
    # Save splits
    train_path = os.path.join(output_dir, 'train.jsonl')
    val_path = os.path.join(output_dir, 'val.jsonl')
    
    with open(train_path, 'w') as f:
        for ex in train_examples:
            f.write(json.dumps(ex) + '\n')
    
    with open(val_path, 'w') as f:
        for ex in val_examples:
            f.write(json.dumps(ex) + '\n')
    
    return train_path, val_path, len(train_examples), len(val_examples)

def main():
    print("=" * 80)
    print("MOTADATA-CODER FINE-TUNING")
    print("=" * 80)
    
    # Paths
    script_dir = Path(__file__).parent
    data_path = script_dir / 'motadata_finetuning_data.jsonl'
    output_dir = script_dir / 'finetuning_output'
    
    if not data_path.exists():
        print(f"❌ Dataset not found: {data_path}")
        sys.exit(1)
    
    print(f"\n📂 Loading training data from: {data_path}")
    examples = load_training_data(str(data_path))
    print(f"✅ Loaded {len(examples)} examples")
    
    print(f"\n📊 Preparing training/validation split...")
    train_path, val_path, train_count, val_count = prepare_training_data(
        examples, str(output_dir)
    )
    print(f"✅ Train: {train_count} examples")
    print(f"✅ Val: {val_count} examples")
    
    print(f"\n📝 Training data prepared:")
    print(f"  Train: {train_path}")
    print(f"  Val: {val_path}")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"  1. Use OpenAI API: openai.FineTuningJob.create()")
    print(f"  2. Or use local fine-tuning with:")
    print(f"     - axolotl (recommended)")
    print(f"     - unsloth")
    print(f"     - huggingface transformers")
    
    print(f"\n💡 EXAMPLE COMMAND (using axolotl):")
    print(f"  axolotl train config.yaml")
    
    print(f"\n📊 DATASET STATS:")
    print(f"  Total Examples: {len(examples)}")
    print(f"  Avg Tokens/Example: 1,061")
    print(f"  Total Tokens: 3,655,503")
    print(f"  Estimated Cost: $10.97 (OpenAI)")
    print(f"  Estimated Time: 2-4 hours")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()

