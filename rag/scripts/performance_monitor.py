#!/usr/bin/env python3
"""
V16 Performance Monitoring Script
Monitors inference latency, GPU utilization, and error rates
"""

import requests
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

VLLM_URL = "http://localhost:8000/v1"
MODEL_NAME = "motadata-coder-v16"
LOG_DIR = Path("/home/harshil/Harshil-PoCs/rag/logs")
METRICS_FILE = LOG_DIR / "v16_performance_metrics.json"

def get_gpu_stats():
    """Get GPU memory and utilization stats"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            return {
                "memory_used_mb": int(parts[0]),
                "memory_total_mb": int(parts[1]),
                "gpu_utilization_percent": int(parts[2].rstrip("%"))
            }
    except Exception as e:
        print(f"Error getting GPU stats: {e}")
    return None

def test_inference_latency():
    """Test inference latency"""
    try:
        start_time = time.time()
        response = requests.post(
            f"{VLLM_URL}/completions",
            json={
                "model": MODEL_NAME,
                "prompt": "Generate a simple Java method",
                "max_tokens": 128,
                "temperature": 0.7
            },
            timeout=30
        )
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            return {"status": "success", "latency_ms": latency_ms}
        else:
            return {"status": "error", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def check_service_health():
    """Check if all services are running"""
    services = {
        "qdrant": "http://localhost:6333/health",
        "neo4j": "http://localhost:7474",
        "vllm": f"{VLLM_URL}/models",
        "rag_api": "http://localhost:8081/health"
    }
    
    health = {}
    for service, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            health[service] = response.status_code == 200
        except:
            health[service] = False
    
    return health

def collect_metrics():
    """Collect all performance metrics"""
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "gpu_stats": get_gpu_stats(),
        "inference_latency": test_inference_latency(),
        "service_health": check_service_health()
    }
    return metrics

def save_metrics(metrics):
    """Save metrics to file"""
    try:
        if METRICS_FILE.exists():
            with open(METRICS_FILE, "r") as f:
                history = json.load(f)
        else:
            history = []
        
        history.append(metrics)
        # Keep last 1000 entries
        history = history[-1000:]
        
        with open(METRICS_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving metrics: {e}")

def print_metrics(metrics):
    """Print metrics in readable format"""
    print(f"\n[{metrics['timestamp']}] Performance Metrics")
    print("-" * 60)
    
    if metrics["gpu_stats"]:
        gpu = metrics["gpu_stats"]
        mem_percent = (gpu["memory_used_mb"] / gpu["memory_total_mb"]) * 100
        print(f"GPU Memory: {gpu['memory_used_mb']}/{gpu['memory_total_mb']} MB ({mem_percent:.1f}%)")
        print(f"GPU Utilization: {gpu['gpu_utilization_percent']}%")
    
    if metrics["inference_latency"]["status"] == "success":
        latency = metrics["inference_latency"]["latency_ms"]
        status = "✅" if latency < 3000 else "⚠️" if latency < 4000 else "❌"
        print(f"Inference Latency: {latency:.0f}ms {status}")
    else:
        print(f"Inference Latency: ERROR - {metrics['inference_latency']['error']}")
    
    health = metrics["service_health"]
    print(f"Services: ", end="")
    for service, is_healthy in health.items():
        status = "✅" if is_healthy else "❌"
        print(f"{service}{status} ", end="")
    print()

def main():
    print("=" * 60)
    print("V16 Performance Monitoring")
    print("=" * 60)
    print(f"Monitoring {MODEL_NAME}")
    print(f"Metrics saved to: {METRICS_FILE}")
    print()
    
    try:
        while True:
            metrics = collect_metrics()
            save_metrics(metrics)
            print_metrics(metrics)
            
            # Wait 60 seconds before next check
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped")

if __name__ == "__main__":
    main()

