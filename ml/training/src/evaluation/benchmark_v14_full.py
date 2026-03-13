#!/usr/bin/env python3
"""
Full benchmarking suite for V14 model - 10 diverse multi-file tasks.
"""

import json
import requests
import time
from pathlib import Path
from datetime import datetime

# API endpoint
V14_API = "http://localhost:8001/v1/chat/completions"

# 10 diverse test cases covering different scenarios
BENCHMARK_TASKS = [
    {
        "id": 1,
        "name": "2-file API endpoint addition",
        "task": "Add new REST endpoint for user profile updates",
        "files": [
            "src/api/UserController.java",
            "src/service/UserService.java"
        ]
    },
    {
        "id": 2,
        "name": "3-file authentication refactor",
        "task": "Refactor JWT token validation logic",
        "files": [
            "src/auth/AuthManager.java",
            "src/auth/TokenValidator.java",
            "src/api/AuthController.java"
        ]
    },
    {
        "id": 3,
        "name": "4-file logging framework",
        "task": "Add structured logging across service layer",
        "files": [
            "src/service/DataService.java",
            "src/service/MetricService.java",
            "src/util/Logger.java",
            "src/config/LogConfig.java"
        ]
    },
    {
        "id": 4,
        "name": "5-file error handling",
        "task": "Implement comprehensive error handling in data pipeline",
        "files": [
            "src/processor/DataProcessor.java",
            "src/processor/Validator.java",
            "src/exception/ProcessingException.java",
            "src/exception/ValidationException.java",
            "src/util/ErrorHandler.java"
        ]
    },
    {
        "id": 5,
        "name": "3-file database migration",
        "task": "Add database connection pooling support",
        "files": [
            "src/db/DatabaseManager.java",
            "src/db/ConnectionPool.java",
            "src/config/DatabaseConfig.java"
        ]
    },
    {
        "id": 6,
        "name": "4-file caching layer",
        "task": "Implement Redis caching for API responses",
        "files": [
            "src/cache/CacheManager.java",
            "src/cache/RedisClient.java",
            "src/api/APIController.java",
            "src/config/CacheConfig.java"
        ]
    },
    {
        "id": 7,
        "name": "6-file monitoring system",
        "task": "Add metrics collection and monitoring",
        "files": [
            "src/monitor/MetricCollector.java",
            "src/monitor/MetricAggregator.java",
            "src/monitor/MetricPublisher.java",
            "src/service/MonitorService.java",
            "src/config/MonitorConfig.java",
            "src/util/MetricUtil.java"
        ]
    },
    {
        "id": 8,
        "name": "3-file security enhancement",
        "task": "Add rate limiting and request throttling",
        "files": [
            "src/security/RateLimiter.java",
            "src/security/ThrottleManager.java",
            "src/api/SecurityFilter.java"
        ]
    },
    {
        "id": 9,
        "name": "5-file notification system",
        "task": "Implement multi-channel notification delivery",
        "files": [
            "src/notification/NotificationManager.java",
            "src/notification/EmailNotifier.java",
            "src/notification/SlackNotifier.java",
            "src/notification/NotificationQueue.java",
            "src/config/NotificationConfig.java"
        ]
    },
    {
        "id": 10,
        "name": "7-file data export pipeline",
        "task": "Build data export system with multiple format support",
        "files": [
            "src/export/ExportManager.java",
            "src/export/CSVExporter.java",
            "src/export/JSONExporter.java",
            "src/export/XMLExporter.java",
            "src/export/ExportQueue.java",
            "src/service/ExportService.java",
            "src/config/ExportConfig.java"
        ]
    }
]

SYSTEM_PROMPT = """You are a senior Motadata engineer. Given a task and multiple files to modify, generate precise unified diffs for each file.

CRITICAL REQUIREMENTS:
- Generate diffs for ALL files listed in the task
- Use proper unified diff format with --- a/ and +++ b/ headers
- Include File: prefix for each file
- Wrap each diff in ```diff blocks
- Ensure changes are consistent across all files"""


def test_task(task):
    """Test a single task."""
    files_list = "\n".join([f"{i+1}. {f}" for i, f in enumerate(task['files'])])
    user_message = f"""Task: {task['task']}

Files to modify ({len(task['files'])} files):
{files_list}

Generate unified diffs for all files to implement this change."""

    payload = {
        "model": "motadata-coder-v14",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.1,
        "max_tokens": 8192
    }
    
    try:
        start_time = time.time()
        response = requests.post(V14_API, json=payload, timeout=180)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Analyze response
            file_mentions = content.count('File:')
            diff_blocks = content.count('```diff')
            has_thinking = '<thinking>' in content
            has_code = '<code>' in content
            
            # Check if all files are covered
            expected_files = len(task['files'])
            all_files_covered = file_mentions >= expected_files
            
            return {
                "success": True,
                "content": content,
                "elapsed": elapsed,
                "file_mentions": file_mentions,
                "diff_blocks": diff_blocks,
                "expected_files": expected_files,
                "all_files_covered": all_files_covered,
                "has_thinking": has_thinking,
                "has_code": has_code,
                "length": len(content),
                "tokens": result['usage']['total_tokens'] if 'usage' in result else 0
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "error_detail": response.text[:500]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    print("=" * 100)
    print("V14 FULL BENCHMARK - 10 MULTI-FILE TASKS")
    print("=" * 100)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tasks: {len(BENCHMARK_TASKS)}")
    print()
    
    # Check service
    print("🔍 Checking V14 service...")
    try:
        check = requests.get("http://localhost:8001/v1/models", timeout=5)
        print("✅ V14 service running (port 8001)\n")
    except:
        print("❌ V14 service not running!")
        return 1
    
    # Run benchmark
    results = []
    total_start = time.time()
    
    for task in BENCHMARK_TASKS:
        print(f"\n{'='*100}")
        print(f"TASK {task['id']}/10: {task['name']}")
        print(f"{'='*100}")
        print(f"Description: {task['task']}")
        print(f"Files: {len(task['files'])}")
        print()
        
        print("🧪 Testing...")
        result = test_task(task)
        
        if result['success']:
            status = "✅" if result['all_files_covered'] else "⚠️"
            print(f"{status} Success ({result['elapsed']:.1f}s)")
            print(f"   📊 Files mentioned: {result['file_mentions']}/{result['expected_files']}")
            print(f"   📊 Diff blocks: {result['diff_blocks']}")
            print(f"   📊 All files covered: {result['all_files_covered']}")
            print(f"   📊 Has <thinking>: {result['has_thinking']}")
            print(f"   📊 Has <code>: {result['has_code']}")
            print(f"   📊 Response length: {result['length']:,} chars")
            if result['tokens'] > 0:
                print(f"   📊 Tokens used: {result['tokens']:,}")
        else:
            print(f"   ❌ Failed: {result['error']}")
        
        results.append({
            "task": task,
            "result": result
        })
    
    total_elapsed = time.time() - total_start
    
    # Summary
    print("\n" + "=" * 100)
    print("BENCHMARK SUMMARY")
    print("=" * 100)
    print()
    
    success_count = sum(1 for r in results if r['result']['success'])
    full_coverage = sum(1 for r in results if r['result'].get('all_files_covered', False))
    
    print(f"✅ Success Rate: {success_count}/{len(BENCHMARK_TASKS)} ({success_count/len(BENCHMARK_TASKS)*100:.0f}%)")
    print(f"✅ Full Coverage: {full_coverage}/{len(BENCHMARK_TASKS)} ({full_coverage/len(BENCHMARK_TASKS)*100:.0f}%)")
    print(f"⏱️  Total Time: {total_elapsed:.1f}s")
    print(f"⏱️  Avg Time: {total_elapsed/len(BENCHMARK_TASKS):.1f}s per task")
    print()
    
    # Detailed stats
    if success_count > 0:
        successful = [r['result'] for r in results if r['result']['success']]
        avg_time = sum(r['elapsed'] for r in successful) / len(successful)
        avg_length = sum(r['length'] for r in successful) / len(successful)
        avg_files = sum(r['file_mentions'] for r in successful) / len(successful)
        
        print("📊 Performance Metrics:")
        print(f"   Avg response time: {avg_time:.1f}s")
        print(f"   Avg response length: {avg_length:,.0f} chars")
        print(f"   Avg files per response: {avg_files:.1f}")
        print()
    
    # Save results
    output_file = "evaluation/finetuning/v14_benchmark_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tasks": len(BENCHMARK_TASKS),
            "success_count": success_count,
            "full_coverage_count": full_coverage,
            "total_time": total_elapsed,
            "results": results
        }, f, indent=2)
    
    print(f"📁 Detailed results saved to: {output_file}")
    print()
    print("=" * 100)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    return 0


if __name__ == '__main__':
    exit(main())

