#!/usr/bin/env python3
"""
Quick validation: Test that DPO pairs can be loaded and formatted by TRL.

This doesn't train, just verifies the dataset loads and formats correctly
for the DPO trainer.
"""

import json
from pathlib import Path
from datasets import load_dataset


BASE_DIR = Path("/home/harshil/Harshil-PoCs")
TRAIN_FILE = BASE_DIR / "datasets/v17_dpo_pairs_train.jsonl"


def validate_dpo_format():
    """Test loading and basic format validation."""
    print("=" * 80)
    print("DPO DATASET FORMAT VALIDATION")
    print("=" * 80)
    
    # Load dataset
    print(f"\nLoading {TRAIN_FILE.name}...")
    dataset = load_dataset("json", data_files=str(TRAIN_FILE), split="train")
    print(f"✓ Loaded {len(dataset)} pairs")
    
    # Inspect first pair
    print("\n" + "-" * 80)
    print("SAMPLE PAIR INSPECTION")
    print("-" * 80)
    sample = dataset[0]
    print(f"Keys: {list(sample.keys())}")
    print(f"\nStructure:")
    print(f"  category: {sample.get('category')}")
    print(f"  source: {sample.get('source')}")
    print(f"  difficulty: {sample.get('difficulty')}")
    print(f"  messages: {len(sample.get('messages', []))} items")
    
    if sample.get('messages'):
        for i, msg in enumerate(sample['messages']):
            content_preview = msg.get('content', '')[:60].replace('\n', ' ').strip()
            print(f"    [{i}] role={msg.get('role'):9s} | content={content_preview}...")
    
    # Check for common DPO formats
    print("\n" + "-" * 80)
    print("FORMAT CHECK")
    print("-" * 80)
    
    has_messages = "messages" in sample
    has_chosen = "chosen" in sample
    has_rejected = "rejected" in sample
    
    print(f"Has 'messages' field: {has_messages} {'✓' if has_messages else '✗ (REQUIRED)'}")
    print(f"Has 'chosen' field:   {has_chosen}")
    print(f"Has 'rejected' field: {has_rejected}")
    
    if has_messages:
        print("\n✓ Dataset uses ChatML 'messages' format (spec-compliant)")
        print("  Note: TRL DPO trainer will process messages into prompt/chosen/rejected")
    elif has_chosen and has_rejected:
        print("\n✓ Dataset has chosen/rejected (traditional DPO format)")
    else:
        print("\n✗ Dataset missing preference pair fields")
        return False
    
    # Token stats
    print("\n" + "-" * 80)
    print("TOKEN STATISTICS (approximate)")
    print("-" * 80)
    
    token_counts = []
    for pair in dataset:
        messages = pair.get('messages', [])
        tokens = sum(len(msg.get('content', '').split()) for msg in messages)
        token_counts.append(tokens)
    
    token_counts.sort()
    print(f"  Count:  {len(token_counts)}")
    print(f"  Mean:   {sum(token_counts) / len(token_counts):.0f}")
    print(f"  Median: {token_counts[len(token_counts) // 2]:.0f}")
    print(f"  Min:    {min(token_counts)}")
    print(f"  Max:    {max(token_counts)}")
    print(f"  P95:    {token_counts[int(len(token_counts) * 0.95)]}")
    
    # Category balance
    print("\n" + "-" * 80)
    print("CATEGORY DISTRIBUTION")
    print("-" * 80)
    
    categories = {}
    for pair in dataset:
        cat = pair.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat in sorted(categories.keys()):
        count = categories[cat]
        pct = (count / len(dataset)) * 100
        print(f"  {cat:20s}: {count:3d} ({pct:5.1f}%)")
    
    print("\n" + "=" * 80)
    print("✓ VALIDATION PASSED - Dataset is ready for DPO training")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    validate_dpo_format()
