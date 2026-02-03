#!/usr/bin/env python3
"""
Fine-tune Claude model on V15 dataset using Anthropic API

This script fine-tunes Claude Opus 4.1 on the V15 training dataset.
Uses Anthropic's fine-tuning API.
"""

import json
import argparse
from pathlib import Path
import anthropic
import time


def prepare_training_data(train_file: Path) -> list:
    """Load and prepare training data for fine-tuning."""
    examples = []
    
    print(f"Loading training data from: {train_file}")
    with open(train_file, 'r') as f:
        for line in f:
            example = json.loads(line)
            examples.append(example)
    
    print(f"✓ Loaded {len(examples)} training examples")
    return examples


def convert_to_finetuning_format(examples: list) -> list:
    """Convert examples to Anthropic fine-tuning format."""
    finetuning_data = []
    
    for example in examples:
        # Extract user prompt and assistant response
        user_content = example['messages'][0]['content']
        assistant_content = example['messages'][-1]['content']
        
        # Anthropic fine-tuning format
        ft_example = {
            "messages": [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_content}
            ]
        }
        finetuning_data.append(ft_example)
    
    return finetuning_data


def save_finetuning_jsonl(data: list, output_file: Path):
    """Save data in JSONL format for fine-tuning."""
    with open(output_file, 'w') as f:
        for example in data:
            f.write(json.dumps(example) + '\n')
    
    print(f"✓ Saved fine-tuning data to: {output_file}")
    print(f"  File size: {output_file.stat().st_size / (1024*1024):.1f} MB")


def upload_training_file(client: anthropic.Anthropic, file_path: Path) -> str:
    """Upload training file to Anthropic."""
    print(f"\nUploading training file: {file_path}")
    
    with open(file_path, 'rb') as f:
        response = client.beta.files.upload(
            file=(file_path.name, f, "application/jsonl"),
        )
    
    file_id = response.id
    print(f"✓ File uploaded successfully!")
    print(f"  File ID: {file_id}")
    
    return file_id


def create_finetuning_job(
    client: anthropic.Anthropic,
    file_id: str,
    model: str = "claude-opus-4-1-20250805",
    learning_rate: float = 1e-4,
    epochs: int = 3
) -> str:
    """Create a fine-tuning job."""
    print(f"\nCreating fine-tuning job...")
    print(f"  Model: {model}")
    print(f"  Learning Rate: {learning_rate}")
    print(f"  Epochs: {epochs}")

    try:
        response = client.beta.fine_tuning.jobs.create(
            model=model,
            training_file=file_id,
            hyperparameters={
                "learning_rate_multiplier": learning_rate,
                "epochs": epochs
            }
        )

        job_id = response.id
        print(f"✓ Fine-tuning job created!")
        print(f"  Job ID: {job_id}")
        print(f"  Status: {response.status}")

        return job_id
    except AttributeError as e:
        print(f"\n⚠️  Fine-tuning API not available in current SDK version")
        print(f"Error: {str(e)}")
        print(f"\nNote: Anthropic fine-tuning may require a different approach.")
        print(f"File uploaded successfully: {file_id}")
        print(f"You can use this file ID to create a fine-tuning job via the API directly.")
        raise


def monitor_finetuning_job(client: anthropic.Anthropic, job_id: str, check_interval: int = 30):
    """Monitor fine-tuning job progress."""
    print(f"\nMonitoring fine-tuning job: {job_id}")
    print(f"Check interval: {check_interval} seconds")
    print("(Press Ctrl+C to stop monitoring)\n")
    
    try:
        while True:
            job = client.beta.fine_tuning.jobs.retrieve(job_id)
            
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Status: {job.status}")
            
            if hasattr(job, 'training_metrics') and job.training_metrics:
                metrics = job.training_metrics
                print(f"  Loss: {metrics.get('loss', 'N/A')}")
                print(f"  Accuracy: {metrics.get('accuracy', 'N/A')}")
            
            if job.status in ['succeeded', 'failed', 'cancelled']:
                print(f"\n✓ Job {job.status}!")
                if job.status == 'succeeded':
                    print(f"  Fine-tuned model: {job.fine_tuned_model}")
                return job
            
            time.sleep(check_interval)
    
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
        job = client.beta.fine_tuning.jobs.retrieve(job_id)
        print(f"Current status: {job.status}")
        return job


def main():
    parser = argparse.ArgumentParser(description='Fine-tune Claude on V15 dataset')
    parser.add_argument('--train-file', required=True, help='Path to training set JSONL file')
    parser.add_argument('--api-key', required=True, help='Anthropic API key')
    parser.add_argument('--model', default='claude-opus-4-1-20250805', help='Base model to fine-tune')
    parser.add_argument('--learning-rate', type=float, default=1e-4, help='Learning rate multiplier')
    parser.add_argument('--epochs', type=int, default=3, help='Number of training epochs')
    parser.add_argument('--output-dir', default='training/results', help='Output directory')
    parser.add_argument('--monitor', action='store_true', help='Monitor job until completion')
    
    args = parser.parse_args()
    
    # Setup
    train_file = Path(args.train_file)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    client = anthropic.Anthropic(api_key=args.api_key)
    
    print("="*80)
    print("V15 FINE-TUNING - CLAUDE OPUS 4.1")
    print("="*80)
    
    # Load and prepare data
    examples = prepare_training_data(train_file)
    finetuning_data = convert_to_finetuning_format(examples)
    
    # Save in fine-tuning format
    ft_file = output_dir / 'v15_finetuning_data.jsonl'
    save_finetuning_jsonl(finetuning_data, ft_file)
    
    # Upload file
    file_id = upload_training_file(client, ft_file)
    
    # Create fine-tuning job
    job_id = create_finetuning_job(
        client,
        file_id,
        model=args.model,
        learning_rate=args.learning_rate,
        epochs=args.epochs
    )
    
    # Save job info
    job_info = {
        'job_id': job_id,
        'file_id': file_id,
        'model': args.model,
        'learning_rate': args.learning_rate,
        'epochs': args.epochs,
        'training_examples': len(examples)
    }
    
    job_info_file = output_dir / 'v15_finetuning_job_info.json'
    with open(job_info_file, 'w') as f:
        json.dump(job_info, f, indent=2)
    
    print(f"\n✓ Job info saved to: {job_info_file}")
    
    # Monitor if requested
    if args.monitor:
        final_job = monitor_finetuning_job(client, job_id)
        print(f"\n{'='*80}")
        print(f"Final Status: {final_job.status}")
        if final_job.status == 'succeeded':
            print(f"Fine-tuned model: {final_job.fine_tuned_model}")
        print(f"{'='*80}")
    else:
        print(f"\n{'='*80}")
        print("Fine-tuning job created successfully!")
        print(f"Job ID: {job_id}")
        print(f"\nTo monitor progress, run:")
        print(f"  python3 training/src/finetuning/monitor_finetuning_job.py --job-id {job_id} --api-key <YOUR_API_KEY>")
        print(f"{'='*80}\n")


if __name__ == '__main__':
    main()

