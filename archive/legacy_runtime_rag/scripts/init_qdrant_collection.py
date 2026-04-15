#!/usr/bin/env python3
"""
Initialize Qdrant with motadata_code collection

Creates an empty collection that the RAG API can connect to.
This allows the system to start while we index the actual codebase.
"""

import sys
import time
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

def init_qdrant():
    """Initialize Qdrant with motadata_code collection"""
    
    # Wait for Qdrant to be ready
    max_retries = 30
    for attempt in range(max_retries):
        try:
            client = QdrantClient(host="localhost", port=6333)
            client.get_collections()
            print("✓ Qdrant is ready")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⏳ Waiting for Qdrant... ({attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                print(f"✗ Failed to connect to Qdrant: {e}")
                return False
    
    try:
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if "motadata_code" in collection_names:
            print("✓ Collection 'motadata_code' already exists")
            return True
        
        # Create collection with 768 dimensions (Jina embeddings)
        print("Creating collection 'motadata_code'...")
        client.create_collection(
            collection_name="motadata_code",
            vectors_config=VectorParams(
                size=768,
                distance=Distance.COSINE
            )
        )
        print("✓ Collection 'motadata_code' created successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error initializing Qdrant: {e}")
        return False

if __name__ == "__main__":
    success = init_qdrant()
    sys.exit(0 if success else 1)

