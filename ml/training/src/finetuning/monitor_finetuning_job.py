#!/usr/bin/env python3
"""
Monitor Anthropic fine-tuning job progress
"""

import argparse
import anthropic
import time
import json
from pathlib import Path


def monitor_job(client: anthropic.Anthropic, job_id: str, check_interval: int = 30):
    """Monitor fine-tuning job progress."""
    print(f"Monitoring fine-tuning job: {job_id}")
    print(f"Check interval: {check_interval} seconds")
    print("(Press Ctrl+C to stop monitoring)\n")
    
    try:
        while True:
            job = client.beta.fine_tuning.jobs.retrieve(job_id)
            
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] Status: {job.status}")
            
            if hasattr(job, 'training_metrics') and job.training_metrics:
                metrics = job.training_metrics
                if hasattr(metrics, 'loss'):
                    print(f"  Loss: {metrics.loss}")
                if hasattr(metrics, 'accuracy'):
                    print(f"  Accuracy: {metrics.accuracy}")
            
            if job.status in ['succeeded', 'failed', 'cancelled']:
                print(f"\n✓ Job {job.status}!")
                if job.status == 'succeeded':
                    print(f"  Fine-tuned model: {job.fine_tuned_model}")
                    return job
                else:
                    print(f"  Error: {getattr(job, 'error', 'Unknown error')}")
                    return job
            
            time.sleep(check_interval)
    
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
        job = client.beta.fine_tuning.jobs.retrieve(job_id)
        print(f"Current status: {job.status}")
        return job


def main():
    parser = argparse.ArgumentParser(description='Monitor Anthropic fine-tuning job')
    parser.add_argument('--job-id', required=True, help='Fine-tuning job ID')
    parser.add_argument('--api-key', required=True, help='Anthropic API key')
    parser.add_argument('--check-interval', type=int, default=30, help='Check interval in seconds')
    
    args = parser.parse_args()
    
    client = anthropic.Anthropic(api_key=args.api_key)
    
    print("="*80)
    print("FINE-TUNING JOB MONITOR")
    print("="*80 + "\n")
    
    final_job = monitor_job(client, args.job_id, args.check_interval)
    
    print(f"\n{'='*80}")
    print(f"Final Status: {final_job.status}")
    if final_job.status == 'succeeded':
        print(f"Fine-tuned model: {final_job.fine_tuned_model}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()

