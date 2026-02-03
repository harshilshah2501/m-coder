#!/usr/bin/env python3
"""
Fix Qdrant Vectors - Re-embed and store vectors properly
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer

print("\n" + "=" * 80)
print("QDRANT VECTOR FIX - RE-EMBEDDING AND STORING VECTORS")
print("=" * 80)

# Connect to Qdrant
qdrant = QdrantClient(host="localhost", port=6333)

# Load embedding model
print("\n🔧 Loading embedding model...")
model = SentenceTransformer("jinaai/jina-embeddings-v2-base-code", trust_remote_code=True)
print("✅ Model loaded")

# Process each collection
collections = ["motadata_code", "project_motadata_d954c2755285", "project_test_project_4d5e736d63ec"]

for collection_name in collections:
    try:
        print(f"\n" + "=" * 80)
        print(f"Processing: {collection_name}")
        print("=" * 80)
        
        info = qdrant.get_collection(collection_name)
        print(f"Points: {info.points_count}")
        
        if info.points_count == 0:
            print("⏭️  Skipping empty collection")
            continue
        
        # Scroll through all points
        print(f"\n📥 Re-embedding {info.points_count} points...")
        
        batch_size = 32
        offset = 0
        total_processed = 0
        
        while offset < info.points_count:
            # Get batch of points
            points, next_offset = qdrant.scroll(
                collection_name=collection_name,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            if not points:
                break
            
            # Extract text from payload and generate embeddings
            texts = []
            point_ids = []
            payloads = []
            
            for point in points:
                # Try to reconstruct text from payload
                payload = point.payload
                qualified_name = payload.get('qualified_name', '')
                node_type = payload.get('node_type', '')
                file_path = payload.get('file_path', '')
                
                # Create a meaningful text representation
                text = f"{node_type}: {qualified_name} in {file_path}"
                texts.append(text)
                point_ids.append(point.id)
                payloads.append(payload)
            
            # Generate embeddings
            embeddings = model.encode(texts, show_progress_bar=False)
            
            # Create updated points with vectors
            updated_points = [
                PointStruct(
                    id=point_ids[i],
                    vector=embeddings[i].tolist(),
                    payload=payloads[i]
                )
                for i in range(len(point_ids))
            ]
            
            # Upsert with vectors
            qdrant.upsert(
                collection_name=collection_name,
                points=updated_points
            )
            
            total_processed += len(points)
            print(f"   ✅ Processed {total_processed}/{info.points_count}")
            
            offset = next_offset
            if next_offset is None or next_offset >= info.points_count:
                break
        
        # Verify
        updated_info = qdrant.get_collection(collection_name)
        print(f"\n✅ Collection updated:")
        print(f"   - Points: {updated_info.points_count}")
        print(f"   - Indexed Vectors: {updated_info.indexed_vectors_count}")
        
        # Check sample point
        sample_points, _ = qdrant.scroll(collection_name, limit=1, with_vectors=True)
        if sample_points:
            sample_vector_dim = len(sample_points[0].vector) if sample_points[0].vector else 0
            print(f"   - Sample Vector Dim: {sample_vector_dim}")
            
            if sample_vector_dim == 768:
                print(f"   ✅ Vectors properly stored!")
            else:
                print(f"   ⚠️  Vectors still not stored properly")
        
    except Exception as e:
        print(f"❌ Error processing {collection_name}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("FIX COMPLETE")
print("=" * 80)

