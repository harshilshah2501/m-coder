#!/usr/bin/env python3
"""
Complete System Audit - Detailed Analysis of RAG Pipeline
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

print("\n" + "=" * 80)
print("COMPLETE RAG SYSTEM AUDIT")
print("=" * 80)

# 1. Check Qdrant
print("\n" + "=" * 80)
print("1. QDRANT STATUS")
print("=" * 80)

try:
    qdrant = QdrantClient(host="localhost", port=6333)
    collections = qdrant.get_collections()
    print(f"✅ Qdrant connected")
    print(f"   Collections: {len(collections.collections)}")
    
    for col in collections.collections:
        info = qdrant.get_collection(col.name)
        print(f"\n   📦 {col.name}:")
        print(f"      - Points: {info.points_count}")
        print(f"      - Indexed Vectors: {info.indexed_vectors_count}")
        print(f"      - Vector Size: {info.config.params.vectors.size}")
        
        # Check if vectors are actually stored
        if info.points_count > 0:
            points = qdrant.scroll(col.name, limit=1)
            if points[0]:
                point = points[0][0]
                vector_dim = len(point.vector) if point.vector else 0
                print(f"      - Sample Point Vector Dim: {vector_dim}")
                if vector_dim == 0:
                    print(f"      ⚠️  WARNING: Vectors are empty!")
except Exception as e:
    print(f"❌ Qdrant error: {e}")

# 2. Check Embedding Model
print("\n" + "=" * 80)
print("2. EMBEDDING MODEL")
print("=" * 80)

try:
    print("🔧 Loading embedding model...")
    model = SentenceTransformer("jinaai/jina-embeddings-v2-base-code", trust_remote_code=True)
    print(f"✅ Model loaded")
    
    # Test embedding
    test_text = "public void handleRequest(RoutingContext ctx)"
    embedding = model.encode(test_text)
    print(f"   - Test embedding dimension: {len(embedding)}")
    print(f"   - Sample values: {embedding[:5]}")
    
    if len(embedding) != 768:
        print(f"   ⚠️  WARNING: Expected 768 dims, got {len(embedding)}")
except Exception as e:
    print(f"❌ Embedding model error: {e}")

# 3. Check RAG API
print("\n" + "=" * 80)
print("3. RAG API STATUS")
print("=" * 80)

try:
    import httpx
    response = httpx.get("http://localhost:8081/health", timeout=5)
    if response.status_code == 200:
        print(f"✅ RAG API is running")
        health = response.json()
        print(f"   Status: {health.get('status', 'unknown')}")
    else:
        print(f"❌ RAG API returned {response.status_code}")
except Exception as e:
    print(f"❌ RAG API error: {e}")

# 4. Check vLLM
print("\n" + "=" * 80)
print("4. vLLM STATUS")
print("=" * 80)

try:
    import httpx
    response = httpx.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        print(f"✅ vLLM is running")
    else:
        print(f"❌ vLLM returned {response.status_code}")
except Exception as e:
    print(f"❌ vLLM error: {e}")

# 5. Test Search
print("\n" + "=" * 80)
print("5. SEARCH FUNCTIONALITY TEST")
print("=" * 80)

try:
    import httpx
    response = httpx.post(
        "http://localhost:8081/search/semantic",
        json={"query": "REST endpoint", "top_k": 3},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Semantic search works")
        print(f"   - Results: {data.get('total_found', 0)}")
        print(f"   - High confidence: {data.get('high_confidence_count', 0)}")
        if data.get('results'):
            print(f"   - Sample result: {data['results'][0].get('qualified_name', 'N/A')}")
    else:
        print(f"❌ Search returned {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Search error: {e}")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)

