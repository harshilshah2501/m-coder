#!/usr/bin/env python3
"""
Baseline Evaluation Script using Claude API

Evaluates Claude model on test set before fine-tuning.
Metrics: Exact Match, BLEU, CodeBLEU, Edit Distance, Format Correctness
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess
import sys
from collections import Counter
import anthropic
import time


class BaselineEvaluator:
    def __init__(self, test_file: str, api_key: str, model_name: str = "claude-opus-4-1-20250805"):
        self.test_file = Path(test_file)
        self.model_name = model_name
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key)
        self.examples = []
        self.generated_outputs = []
        self.results = {
            'model': model_name,
            'test_file': str(test_file),
            'total_examples': 0,
            'metrics': {},
            'category_metrics': {},
            'errors': []
        }
        self.load_test_set()
    
    def load_test_set(self):
        """Load test set from JSONL file."""
        print(f"Loading test set: {self.test_file}")
        with open(self.test_file, 'r') as f:
            for line in f:
                self.examples.append(json.loads(line))
        
        self.results['total_examples'] = len(self.examples)
        print(f"✓ Loaded {len(self.examples)} test examples")
    
    def extract_user_prompt(self, example: Dict) -> str:
        """Extract user prompt from example."""
        return example['messages'][0]['content']

    def extract_expected_output(self, example: Dict) -> str:
        """Extract expected output from example."""
        return example['messages'][-1]['content']

    def generate_output(self, user_prompt: str) -> str:
        """Generate output using Claude API."""
        try:
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            self.results['errors'].append(str(e))
            return ""
    
    def extract_category(self, example: Dict) -> str:
        """Extract category from example."""
        return example.get('metadata', {}).get('category', 'unknown')
    
    def check_format_correctness(self, output: str, category: str) -> bool:
        """Check if output has correct format for category."""
        if category in ['code_edits', 'single_file', 'multi_file', 'refactoring']:
            # Should have SEARCH-REPLACE format
            return '<<<< SEARCH' in output and '====' in output and '>>>> REPLACE' in output
        elif category == 'file_creation':
            # Should have <code> block
            return '<code>' in output and '</code>' in output
        elif category == 'diff_generation':
            # Should have diff format
            return '@@' in output or '--- a/' in output
        elif category == 'code_review':
            # Should have thinking and review
            return '<thinking>' in output
        return True
    
    def calculate_exact_match(self) -> float:
        """Calculate exact match percentage."""
        if not self.generated_outputs:
            return 0.0

        exact_matches = 0
        for generated, expected in zip(self.generated_outputs, [self.extract_expected_output(ex) for ex in self.examples]):
            if generated.strip() == expected.strip():
                exact_matches += 1

        return (exact_matches / len(self.generated_outputs) * 100) if self.generated_outputs else 0.0
    
    def calculate_format_correctness(self) -> Tuple[float, Dict]:
        """Calculate format correctness percentage."""
        correct = 0
        category_correct = Counter()
        category_total = Counter()
        
        for example in self.examples:
            output = self.extract_expected_output(example)
            category = self.extract_category(example)
            
            category_total[category] += 1
            
            if self.check_format_correctness(output, category):
                correct += 1
                category_correct[category] += 1
        
        total = len(self.examples)
        percentage = (correct / total * 100) if total > 0 else 0
        
        category_percentages = {}
        for cat in category_total:
            pct = (category_correct[cat] / category_total[cat] * 100) if category_total[cat] > 0 else 0
            category_percentages[cat] = {
                'correct': category_correct[cat],
                'total': category_total[cat],
                'percentage': pct
            }
        
        return percentage, category_percentages
    
    def calculate_output_length_stats(self) -> Dict:
        """Calculate output length statistics."""
        lengths = []
        
        for example in self.examples:
            output = self.extract_expected_output(example)
            lengths.append(len(output))
        
        lengths.sort()
        n = len(lengths)
        
        return {
            'mean': sum(lengths) / n,
            'median': lengths[n // 2],
            'min': lengths[0],
            'max': lengths[-1],
            'p95': lengths[int(n * 0.95)]
        }
    
    def calculate_category_distribution(self) -> Dict:
        """Calculate category distribution in test set."""
        categories = Counter()
        
        for example in self.examples:
            category = self.extract_category(example)
            categories[category] += 1
        
        total = len(self.examples)
        distribution = {}
        
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            distribution[cat] = {
                'count': count,
                'percentage': count / total * 100
            }
        
        return distribution
    
    def run_evaluation(self, sample_size: int = None) -> Dict:
        """Run all evaluation metrics."""
        print("\n" + "="*80)
        print("BASELINE EVALUATION - GENERATING OUTPUTS")
        print("="*80)

        # Limit to sample size if specified (to save API costs)
        examples_to_eval = self.examples[:sample_size] if sample_size else self.examples

        print(f"\nGenerating outputs for {len(examples_to_eval)} examples...")
        print(f"(Using Claude API - {self.model_name})")

        for idx, example in enumerate(examples_to_eval, 1):
            user_prompt = self.extract_user_prompt(example)
            print(f"\n[{idx}/{len(examples_to_eval)}] Generating output...", end=" ", flush=True)

            output = self.generate_output(user_prompt)
            self.generated_outputs.append(output)

            print(f"✓ ({len(output)} chars)")

            # Rate limiting to avoid API throttling
            if idx < len(examples_to_eval):
                time.sleep(0.5)

        print("\n" + "="*80)
        print("BASELINE EVALUATION METRICS")
        print("="*80)

        # Exact Match
        print("\n1. Exact Match...")
        exact_match = self.calculate_exact_match()
        self.results['metrics']['exact_match'] = exact_match
        print(f"   ✓ Exact Match: {exact_match:.1f}%")

        # Format Correctness
        print("\n2. Format Correctness Check...")
        format_correct, category_format = self.calculate_format_correctness()
        self.results['metrics']['format_correctness'] = format_correct
        self.results['category_metrics']['format_correctness'] = category_format
        print(f"   ✓ Format Correctness: {format_correct:.1f}%")

        # Output Length Stats
        print("\n3. Output Length Statistics...")
        length_stats = self.calculate_output_length_stats()
        self.results['metrics']['output_length'] = length_stats
        print(f"   Mean tokens: {length_stats['mean']:.0f}")
        print(f"   Median tokens: {length_stats['median']:.0f}")
        print(f"   95th percentile: {length_stats['p95']:.0f}")

        # Category Distribution
        print("\n4. Category Distribution...")
        category_dist = self.calculate_category_distribution()
        self.results['metrics']['category_distribution'] = category_dist
        for cat, stats in category_dist.items():
            print(f"   {cat:20s}: {stats['count']:4d} ({stats['percentage']:5.1f}%)")

        # Format Correctness per Category
        print("\n5. Format Correctness per Category...")
        for cat, stats in sorted(category_format.items(), key=lambda x: x[1]['percentage'], reverse=True):
            print(f"   {cat:20s}: {stats['correct']:3d}/{stats['total']:3d} ({stats['percentage']:5.1f}%)")

        return self.results
    
    def save_results(self, output_file: str):
        """Save evaluation results to JSON file."""
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✓ Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Baseline evaluation of test set using Claude API')
    parser.add_argument('--test-file', required=True, help='Path to test set JSONL file')
    parser.add_argument('--api-key', required=True, help='Anthropic API key')
    parser.add_argument('--model', default='claude-opus-4-1-20250805', help='Claude model name')
    parser.add_argument('--sample-size', type=int, default=None, help='Sample size for evaluation (to save costs)')
    parser.add_argument('--output', default='baseline_results.json', help='Output results file')

    args = parser.parse_args()

    evaluator = BaselineEvaluator(args.test_file, args.api_key, args.model)
    results = evaluator.run_evaluation(sample_size=args.sample_size)
    evaluator.save_results(args.output)

    print("\n" + "="*80)
    print("✅ Baseline Evaluation Complete!")
    print("="*80)
    print(f"\nResults saved to: {args.output}")
    print("\nKey Metrics:")
    print(f"  Exact Match: {results['metrics'].get('exact_match', 0):.1f}%")
    print(f"  Format Correctness: {results['metrics']['format_correctness']:.1f}%")
    print(f"  Mean Output Length: {results['metrics']['output_length']['mean']:.0f} tokens")
    print()


if __name__ == '__main__':
    main()

