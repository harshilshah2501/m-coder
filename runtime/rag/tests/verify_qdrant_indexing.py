#!/usr/bin/env python3
"""
Comprehensive Qdrant Indexing Verification
Checks collection status, vector indexing, and data quality
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


async def verify_qdrant():
    """Verify Qdrant collection status and indexing"""
    
    print("\n" + "=" * 80)
    print("QDRANT INDEXING VERIFICATION")
    print("=" * 80)
    
    try:
        # Connect to Qdrant
        client = QdrantClient(host="localhost", port=6333)
        
        # Get collections
        collections = client.get_collections()
        print(f"\n✅ Connected to Qdrant")
        print(f"✅ Total Collections: {len(collections.collections)}")
        
        for col in collections.collections:
            print(f"   - {col.name}")
        
        # Check motadata_code collection
        print("\n" + "=" * 80)
        print("MOTADATA_CODE COLLECTION DETAILS")
        print("=" * 80)
        
        collection_info = client.get_collection("motadata_code")
        
        print(f"\n📊 Collection Status:")
        print(f"   - Status: {collection_info.status}")
        print(f"   - Points Count: {collection_info.points_count}")
        print(f"   - Indexed Vectors: {collection_info.indexed_vectors_count}")
        print(f"   - Segments: {collection_info.segments_count}")
        
        # Check vector config
        config = collection_info.config
        print(f"\n🔧 Vector Configuration:")
        print(f"   - Vector Size: {config.params.vectors.size}")
        print(f"   - Distance Metric: {config.params.vectors.distance}")
        
        # Sample some points
        print(f"\n📋 Sample Data Points (first 5):")
        points = client.scroll("motadata_code", limit=5)
        
        if points[0]:
            for i, point in enumerate(points[0], 1):
                payload = point.payload
                print(f"\n   Point {i}:")
                print(f"      - ID: {point.id}")
                print(f"      - Node Type: {payload.get('node_type', 'N/A')}")
                print(f"      - Qualified Name: {payload.get('qualified_name', 'N/A')}")
                print(f"      - File Path: {payload.get('file_path', 'N/A')}")
                print(f"      - Vector Dim: {len(point.vector) if point.vector else 0}")
        else:
            print("   ⚠️  No points found!")
        
        # Verify indexing status
        print(f"\n" + "=" * 80)
        print("INDEXING STATUS")
        print("=" * 80)
        
        if collection_info.indexed_vectors_count == 0:
            print("\n⚠️  WARNING: No indexed vectors!")
            print("   The collection has data but vectors are not indexed.")
            print("   This will cause searches to fail or be very slow.")
            print("\n   To fix:")
            print("   1. Rebuild the collection with proper vector indexing")
            print("   2. Or run: python scripts/index_motadata_codebase.py")
            return False
        
        if collection_info.points_count == 0:
            print("\n❌ ERROR: Collection is empty!")
            print("   No data points found in the collection.")
            print("   Run: python scripts/index_motadata_codebase.py")
            return False
        
        # Calculate indexing percentage
        index_percent = (collection_info.indexed_vectors_count / collection_info.points_count) * 100
        print(f"\n✅ Indexing Status: {index_percent:.1f}% ({collection_info.indexed_vectors_count}/{collection_info.points_count})")
        
        if index_percent == 100:
            print("   ✅ All vectors properly indexed!")
        elif index_percent > 80:
            print("   ⚠️  Most vectors indexed, but some may be missing")
        else:
            print("   ❌ Many vectors not indexed - search performance will be poor")
        
        # Test search
        print(f"\n" + "=" * 80)
        print("SEARCH FUNCTIONALITY TEST")
        print("=" * 80)
        
        # Create a test vector (all zeros for simplicity)
        test_vector = [0.0] * 768
        
        try:
            search_results = client.search(
                collection_name="motadata_code",
                query_vector=test_vector,
                limit=3
            )
            
            print(f"\n✅ Search executed successfully")
            print(f"   - Results returned: {len(search_results)}")
            
            if search_results:
                for i, result in enumerate(search_results, 1):
                    print(f"\n   Result {i}:")
                    print(f"      - Score: {result.score:.4f}")
                    print(f"      - Qualified Name: {result.payload.get('qualified_name', 'N/A')}")
        except Exception as e:
            print(f"\n❌ Search failed: {e}")
            return False
        
        print(f"\n" + "=" * 80)
        print("VERIFICATION COMPLETE")
        print("=" * 80)
        print("\n✅ Qdrant indexing appears to be working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(verify_qdrant())
    sys.exit(0 if success else 1)

