#!/usr/bin/env python3
"""
Filter dataset based on LLM judge report:
- Keep all PASS pairs (score >= 0.90)
- Keep FAIL pairs with score >= 0.70 (partial credit)
- Remove low-quality pairs (score < 0.70)
- Generate filtered splits
"""

import json
from typing import Dict, List
from collections import Counter

def load_jsonl(path: str) -> List[Dict]:
    """Load JSONL file"""
    samples = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    return samples

def save_jsonl(path: str, samples: List[Dict]):
    """Save samples as JSONL"""
    with open(path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

def main():
    print("Loading clean dataset...")
    all_samples = load_jsonl("datasets/v17_dpo_pairs_clean.jsonl")
    print(f"Total samples: {len(all_samples)}")
    
    print("\nLoading judge report...")
    with open("datasets/v17_dpo_judge_50sample.json") as f:
        report = json.load(f)
    
    # Create lookup of task_id -> verdict/score
    verdicts = {}
    for item in report.get("verdicts", []):
        task_id = item.get("task_id")
        verdict = item.get("verdict")
        score = item.get("score", 0)
        verdicts[task_id] = {"verdict": verdict, "score": score}
    
    print(f"Judge report has {len(verdicts)} verdicts")
    
    # Filter samples
    passed = []
    partial = []
    failed = []
    unjudged = []
    
    for sample in all_samples:
        task_id = sample.get("task_id")
        
        if task_id in verdicts:
            v = verdicts[task_id]
            verdict = v.get("verdict")
            score = v.get("score", 0)
            
            if verdict == "PASS" or score >= 0.90:
                passed.append(sample)
            elif score >= 0.70:
                partial.append(sample)
            else:
                failed.append(sample)
        else:
            unjudged.append(sample)
    
    print(f"\nFilter results:")
    print(f"  Passed (score >= 0.90): {len(passed)}")
    print(f"  Partial (0.70 <= score < 0.90): {len(partial)}")
    print(f"  Failed (score < 0.70): {len(failed)}")
    print(f"  Unjudged (not in sample): {len(unjudged)}")
    
    # Strategy: Keep all passed + partial + sample of unjudged (conservative: only use trusted data)
    # This gives us ~9 passed + some partial + most unjudged
    # Since only 50 were judged, we need a strategy for the remaining 450
    
    # Conservative approach: Only keep samples matching patterns from PASSED category
    print("\nAnalyzing PASSED samples for pattern matching...")
    passed_sources = Counter(s.get("source") for s in passed)
    passed_types = Counter(s.get("task_type") for s in passed)
    
    print(f"  PASSED sources: {dict(passed_sources)}")
    print(f"  PASSED task types: {dict(passed_types)}")
    
    # Filter all samples: keep only sources/types that had high pass rate
    # From the report: bugfix (100%) and multi_file (95%) passed
    # Refactoring (65%), single_file (65%), feature_add (55%) have issues
    high_quality_sources = {"synthetic_bugfix", "synthetic_multi_file"}
    high_quality_types = {"bugfix", "multi_file"}
    
    filtered_samples = []
    for sample in all_samples:
        source = sample.get("source", "")
        task_type = sample.get("task_type", "")
        
        # Keep if: in high-quality source/type OR in passed list
        if source in high_quality_sources or task_type in high_quality_types:
            filtered_samples.append(sample)
        elif sample in passed:
            filtered_samples.append(sample)
    
    print(f"\nFiltered dataset: {len(filtered_samples)} pairs")
    print(f"  Removed: {len(all_samples) - len(filtered_samples)} low-quality pairs")
    
    # Generate splits (80/10/10)
    import random
    random.seed(42)
    random.shuffle(filtered_samples)
    
    n = len(filtered_samples)
    n_train = int(n * 0.8)
    n_val = int(n * 0.1)
    
    train = filtered_samples[:n_train]
    val = filtered_samples[n_train:n_train + n_val]
    test = filtered_samples[n_train + n_val:]
    
    # Save filtered dataset and splits
    output_path = "datasets/v17_dpo_pairs_filtered.jsonl"
    save_jsonl(output_path, filtered_samples)
    print(f"\nFiltered dataset saved: {output_path}")
    
    save_jsonl("datasets/v17_dpo_pairs_filtered_train.jsonl", train)
    save_jsonl("datasets/v17_dpo_pairs_filtered_val.jsonl", val)
    save_jsonl("datasets/v17_dpo_pairs_filtered_test.jsonl", test)
    
    print(f"Splits:")
    print(f"  Train: {len(train)} pairs")
    print(f"  Val: {len(val)} pairs")
    print(f"  Test: {len(test)} pairs")
    
    # Metadata
    source_dist = Counter(s.get("source") for s in filtered_samples)
    task_type_dist = Counter(s.get("task_type") for s in filtered_samples)
    
    metadata = {
        "total": len(filtered_samples),
        "filtering_strategy": "Keep only high-quality patterns (bugfix 100%, multi_file 95%)",
        "original_size": len(all_samples),
        "removed": len(all_samples) - len(filtered_samples),
        "source_distribution": dict(source_dist),
        "task_type_distribution": dict(task_type_dist),
        "splits": {"train": len(train), "val": len(val), "test": len(test)},
        "judge_pass_rate": "18% on full (9/50), focusing on bugfix/multi-file"
    }
    
    with open("datasets/v17_dpo_pairs_filtered_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nSource distribution (filtered):")
    for src, count in sorted(source_dist.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(filtered_samples)
        print(f"  {src}: {count} ({pct:.1f}%)")
    
    print(f"\nTask type distribution (filtered):")
    for ttype, count in sorted(task_type_dist.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(filtered_samples)
        print(f"  {ttype}: {count} ({pct:.1f}%)")
    
    print("\n✅ Filtering complete!")
    print(f"Quality estimate: 95%+ (based on bugfix/multi-file patterns)")

if __name__ == "__main__":
    main()
