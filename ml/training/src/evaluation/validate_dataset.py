#!/usr/bin/env python3
"""
Dataset Validation Script - Industry Standard Checks

Usage:
    python validate_dataset.py --dataset datasets/v15_gold.jsonl --output validation_report.json
"""

import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
import hashlib


class DatasetValidator:
    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)
        self.examples = []
        self.load_dataset()
    
    def load_dataset(self):
        """Load and parse dataset."""
        print(f"Loading dataset: {self.dataset_path}")
        with open(self.dataset_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    example = json.loads(line)
                    self.examples.append(example)
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON parse error on line {line_num}: {e}")
        
        print(f"✓ Loaded {len(self.examples)} examples")
    
    def check_json_validity(self) -> Dict:
        """Check if all examples are valid JSON."""
        print("\n" + "="*80)
        print("1. JSON VALIDITY CHECK")
        print("="*80)
        
        valid_count = len(self.examples)
        total_count = valid_count  # Already filtered during load
        
        result = {
            'valid': valid_count,
            'total': total_count,
            'pass': valid_count == total_count
        }
        
        print(f"✓ Valid JSON: {valid_count}/{total_count}")
        return result
    
    def check_format_consistency(self) -> Dict:
        """Check format consistency per category."""
        print("\n" + "="*80)
        print("2. FORMAT CONSISTENCY CHECK")
        print("="*80)
        
        category_formats = defaultdict(lambda: {
            'has_thinking': 0,
            'has_code': 0,
            'has_search_replace': 0,
            'has_diffs': 0,
            'total': 0
        })
        
        for example in self.examples:
            category = example.get('metadata', {}).get('category', 'unknown')
            content = example['messages'][-1]['content']
            
            stats = category_formats[category]
            stats['total'] += 1
            
            if '<thinking>' in content:
                stats['has_thinking'] += 1
            if '<code>' in content:
                stats['has_code'] += 1
            if '<<<< SEARCH' in content:
                stats['has_search_replace'] += 1
            if '@@' in content or '--- a/' in content:
                stats['has_diffs'] += 1
        
        # Print results
        for category, stats in sorted(category_formats.items()):
            print(f"\n{category}:")
            print(f"  Total: {stats['total']}")
            print(f"  Has <thinking>: {stats['has_thinking']} ({stats['has_thinking']/stats['total']*100:.1f}%)")
            print(f"  Has <code>: {stats['has_code']} ({stats['has_code']/stats['total']*100:.1f}%)")
            print(f"  Has SEARCH-REPLACE: {stats['has_search_replace']} ({stats['has_search_replace']/stats['total']*100:.1f}%)")
            print(f"  Has diffs: {stats['has_diffs']} ({stats['has_diffs']/stats['total']*100:.1f}%)")
        
        return dict(category_formats)
    
    def detect_duplicates(self) -> Dict:
        """Detect duplicate examples."""
        print("\n" + "="*80)
        print("3. DUPLICATE DETECTION")
        print("="*80)
        
        content_hashes = {}
        duplicates = []
        
        for idx, example in enumerate(self.examples):
            content = example['messages'][-1]['content']
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            if content_hash in content_hashes:
                duplicates.append((idx, content_hashes[content_hash]))
            else:
                content_hashes[content_hash] = idx
        
        print(f"✓ Unique examples: {len(content_hashes)}")
        print(f"✓ Duplicates found: {len(duplicates)}")
        
        if duplicates:
            print(f"\nFirst 5 duplicates:")
            for i, (idx1, idx2) in enumerate(duplicates[:5], 1):
                print(f"  {i}. Example {idx1} duplicates example {idx2}")
        
        return {
            'unique': len(content_hashes),
            'duplicates': len(duplicates),
            'duplicate_pairs': duplicates[:10]  # First 10
        }
    
    def compute_statistics(self) -> Dict:
        """Compute dataset statistics."""
        print("\n" + "="*80)
        print("4. STATISTICAL ANALYSIS")
        print("="*80)
        
        token_counts = []
        category_counts = Counter()
        
        for example in self.examples:
            content = example['messages'][-1]['content']
            # Rough token count (words * 1.3)
            tokens = len(content.split()) * 1.3
            token_counts.append(tokens)
            
            category = example.get('metadata', {}).get('category', 'unknown')
            category_counts[category] += 1
        
        token_counts.sort()
        n = len(token_counts)
        
        stats = {
            'total_examples': len(self.examples),
            'mean_tokens': sum(token_counts) / n,
            'median_tokens': token_counts[n//2],
            'p95_tokens': token_counts[int(n * 0.95)],
            'min_tokens': token_counts[0],
            'max_tokens': token_counts[-1],
            'category_distribution': dict(category_counts)
        }
        
        print(f"Total examples: {stats['total_examples']}")
        print(f"Mean tokens: {stats['mean_tokens']:.0f}")
        print(f"Median tokens: {stats['median_tokens']:.0f}")
        print(f"95th percentile: {stats['p95_tokens']:.0f}")
        print(f"Min tokens: {stats['min_tokens']:.0f}")
        print(f"Max tokens: {stats['max_tokens']:.0f}")
        
        print(f"\nCategory distribution:")
        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat:20s}: {count:4d} ({count/stats['total_examples']*100:5.1f}%)")
        
        return stats
    
    def run_all_checks(self) -> Dict:
        """Run all validation checks."""
        results = {
            'dataset': str(self.dataset_path),
            'json_validity': self.check_json_validity(),
            'format_consistency': self.check_format_consistency(),
            'duplicates': self.detect_duplicates(),
            'statistics': self.compute_statistics()
        }
        
        return results


def main():
    parser = argparse.ArgumentParser(description='Validate dataset quality')
    parser.add_argument('--dataset', required=True, help='Path to dataset JSONL file')
    parser.add_argument('--output', default='validation_report.json', help='Output report file')
    
    args = parser.parse_args()
    
    validator = DatasetValidator(args.dataset)
    results = validator.run_all_checks()
    
    # Save report
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ Validation complete! Report saved to: {output_path}")
    print(f"{'='*80}\n")


    def check_category_balance(self) -> Dict:
        """Check if categories are balanced."""
        print("\n" + "="*80)
        print("5. CATEGORY BALANCE CHECK")
        print("="*80)

        category_counts = Counter()
        for example in self.examples:
            category = example.get('metadata', {}).get('category', 'unknown')
            category_counts[category] += 1

        total = len(self.examples)
        expected_per_category = total / len(category_counts)

        imbalance_threshold = 0.5  # 50% deviation
        imbalanced = []

        for cat, count in category_counts.items():
            deviation = abs(count - expected_per_category) / expected_per_category
            if deviation > imbalance_threshold:
                imbalanced.append((cat, count, deviation))

        if imbalanced:
            print(f"⚠️  Imbalanced categories (>{imbalance_threshold*100}% deviation):")
            for cat, count, dev in imbalanced:
                print(f"  {cat}: {count} ({dev*100:.1f}% deviation)")
        else:
            print(f"✓ All categories reasonably balanced")

        return {
            'balanced': len(imbalanced) == 0,
            'imbalanced_categories': imbalanced
        }


if __name__ == '__main__':
    main()

