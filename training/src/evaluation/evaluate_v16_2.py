#!/usr/bin/env python3
"""
V16.2 Model Evaluation
======================
Quick evaluation of v16.2 model via RAG API
"""

import requests
import json
import time
from datetime import datetime

API_URL = "http://localhost:8081/v1/chat/completions"
VLLM_URL = "http://localhost:8000/v1/models"

def check_services():
    """Verify services are running"""
    print("Checking services...")
    
    # Check vLLM
    try:
        resp = requests.get(VLLM_URL, timeout=5)
        models = resp.json()['data']
        print(f"✓ vLLM is running, serving: {models[0]['id']}")
    except Exception as e:
        print(f"✗ vLLM error: {e}")
        return False
    
    # Check RAG API
    try:
        resp = requests.get("http://localhost:8081/health", timeout=5)
        print(f"✓ RAG API is running")
    except Exception as e:
        print(f"✗ RAG API error: {e}")
        return False
    
    return True

def test_inference():
    """Test basic inference"""
    print("\nTesting inference...")
    
    payload = {
        "model": "motadata-coder",
        "messages": [
            {"role": "system", "content": "You are a helpful Java code assistant."},
            {"role": "user", "content": "Write a simple Java method that returns the sum of two numbers."}
        ],
        "temperature": 0.7,
        "max_tokens": 256
    }
    
    try:
        start = time.time()
        resp = requests.post(API_URL, json=payload, timeout=60)
        resp.raise_for_status()
        latency = time.time() - start
        
        result = resp.json()
        content = result['choices'][0]['message']['content']
        tokens = result['usage']['completion_tokens']
        
        print(f"✓ Inference successful")
        print(f"  Latency: {latency:.2f}s")
        print(f"  Tokens: {tokens}")
        print(f"  Output: {content[:100]}...")
        
        return True
    except Exception as e:
        print(f"✗ Inference error: {e}")
        return False

def main():
    print("=" * 80)
    print("V16.2 MODEL EVALUATION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    if not check_services():
        print("\n❌ Services not ready")
        return 1
    
    if not test_inference():
        print("\n❌ Inference test failed")
        return 1
    
    print("\n" + "=" * 80)
    print("✅ V16.2 MODEL EVALUATION COMPLETE")
    print("=" * 80)
    return 0

if __name__ == "__main__":
    exit(main())

