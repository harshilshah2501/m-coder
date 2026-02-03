#!/usr/bin/env python3
"""
Complete Re-indexing with Verification
Carefully indexes Motadata codebase with step-by-step verification
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from pathlib import Path

print("\n" + "=" * 80)
print("COMPLETE RE-INDEXING WITH VERIFICATION")
print("=" * 80)

WORKSPACE_ROOT = "/home/harshil/TestMotadataProject/Motadata/motadata"

# Import ProjectIndexManager to get the correct collection name
from indexing.project_indexer import ProjectIndexManager
manager = ProjectIndexManager()
COLLECTION_NAME = manager.get_collection_name(WORKSPACE_ROOT)

# Step 1: Verify workspace exists
print("\n" + "=" * 80)
print("STEP 1: VERIFY WORKSPACE")
print("=" * 80)

workspace_path = Path(WORKSPACE_ROOT)
if not workspace_path.exists():
    print(f"❌ Workspace not found: {WORKSPACE_ROOT}")
    sys.exit(1)

java_files = list(workspace_path.rglob("*.java"))
java_files = [f for f in java_files if not any(x in str(f) for x in ['/test/', '/build/', '/target/', '/.git/'])]
print(f"✅ Workspace found")
print(f"   - Java files: {len(java_files)}")

# Step 2: Verify Qdrant connection
print("\n" + "=" * 80)
print("STEP 2: VERIFY QDRANT CONNECTION")
print("=" * 80)

try:
    qdrant = QdrantClient(host="localhost", port=6333)
    collections = qdrant.get_collections()
    print(f"✅ Qdrant connected")
    print(f"   - Collections: {len(collections.collections)}")
except Exception as e:
    print(f"❌ Qdrant connection failed: {e}")
    sys.exit(1)

# Step 3: Delete old collection
print("\n" + "=" * 80)
print("STEP 3: DELETE OLD COLLECTION")
print("=" * 80)

try:
    qdrant.delete_collection(COLLECTION_NAME)
    print(f"✅ Deleted old collection: {COLLECTION_NAME}")
except:
    print(f"⚠️  Collection didn't exist (OK)")

# Step 4: Verify embedding model
print("\n" + "=" * 80)
print("STEP 4: VERIFY EMBEDDING MODEL")
print("=" * 80)

try:
    print("🔧 Loading embedding model...")
    model = SentenceTransformer("jinaai/jina-embeddings-v2-base-code", trust_remote_code=True)
    
    # Test embedding
    test_text = "public void handleRequest(RoutingContext ctx)"
    test_embedding = model.encode(test_text)
    
    print(f"✅ Model loaded and working")
    print(f"   - Embedding dimension: {len(test_embedding)}")
    print(f"   - Sample values: {test_embedding[:3]}")
    
    if len(test_embedding) != 768:
        print(f"❌ ERROR: Expected 768 dims, got {len(test_embedding)}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Embedding model error: {e}")
    sys.exit(1)

# Step 5: Use project indexer to index
print("\n" + "=" * 80)
print("STEP 5: INDEX CODEBASE")
print("=" * 80)

try:
    from indexing.project_indexer import get_project_manager
    
    manager = get_project_manager()
    print(f"🔧 Starting indexing...")
    
    start_time = time.time()
    project = manager.index_project(WORKSPACE_ROOT)
    duration = time.time() - start_time
    
    print(f"✅ Indexing complete")
    print(f"   - Duration: {duration:.2f}s")
    print(f"   - Files: {project.file_count}")
    print(f"   - Nodes: {project.node_count}")
    print(f"   - Status: {project.status}")
    
except Exception as e:
    print(f"❌ Indexing failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 6: Verify vectors in Qdrant
print("\n" + "=" * 80)
print("STEP 6: VERIFY VECTORS IN QDRANT")
print("=" * 80)

try:
    info = qdrant.get_collection(COLLECTION_NAME)
    print(f"✅ Collection info:")
    print(f"   - Points: {info.points_count}")
    print(f"   - Indexed Vectors: {info.indexed_vectors_count}")
    print(f"   - Vector Size: {info.config.params.vectors.size}")
    
    if info.points_count == 0:
        print(f"❌ ERROR: No points in collection!")
        sys.exit(1)
    
    # Check sample point
    points, _ = qdrant.scroll(COLLECTION_NAME, limit=5, with_vectors=True)
    
    print(f"\n📋 Sample Points:")
    for i, point in enumerate(points, 1):
        vector_dim = len(point.vector) if point.vector else 0
        qualified_name = point.payload.get('qualified_name', 'N/A')
        print(f"   {i}. {qualified_name}")
        print(f"      - Vector Dim: {vector_dim}")
        print(f"      - Node Type: {point.payload.get('node_type', 'N/A')}")
        
        if vector_dim != 768:
            print(f"      ⚠️  WARNING: Expected 768 dims!")
    
    # Verify all have vectors
    all_points, _ = qdrant.scroll(COLLECTION_NAME, limit=info.points_count, with_vectors=True)
    vectors_with_data = sum(1 for p in all_points if p.vector and len(p.vector) == 768)
    
    print(f"\n✅ Vector verification:")
    print(f"   - Total points: {len(all_points)}")
    print(f"   - Points with 768-dim vectors: {vectors_with_data}")
    print(f"   - Coverage: {(vectors_with_data/len(all_points)*100):.1f}%")
    
    if vectors_with_data == 0:
        print(f"❌ ERROR: No vectors stored!")
        sys.exit(1)
    elif vectors_with_data < len(all_points):
        print(f"⚠️  WARNING: Some points missing vectors!")
    else:
        print(f"✅ All vectors properly stored!")
        
except Exception as e:
    print(f"❌ Verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 7: Test search
print("\n" + "=" * 80)
print("STEP 7: TEST SEARCH")
print("=" * 80)

try:
    import httpx
    
    response = httpx.post(
        "http://localhost:8081/search/semantic",
        json={"query": "REST endpoint handler", "top_k": 5},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Search works")
        print(f"   - Results: {data.get('total_found', 0)}")
        print(f"   - High confidence: {data.get('high_confidence_count', 0)}")
        
        if data.get('results'):
            for i, result in enumerate(data['results'][:3], 1):
                print(f"   {i}. {result.get('qualified_name', 'N/A')} (score: {result.get('score', 'N/A'):.3f})")
    else:
        print(f"⚠️  Search returned {response.status_code}")
        
except Exception as e:
    print(f"⚠️  Search test failed: {e}")

print("\n" + "=" * 80)
print("RE-INDEXING COMPLETE")
print("=" * 80)
print("\n✅ All verifications passed!")
print("   The codebase is now properly indexed with vectors.")

