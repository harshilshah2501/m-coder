#!/usr/bin/env python3
"""
Index Motadata Codebase into Qdrant + Neo4j

Indexes all Java source files from the Motadata project into:
- Qdrant: Vector embeddings for semantic search
- Neo4j: Code structure and relationships
"""

import sys
import os
import time

# Add RAG src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'indexing'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'utils'))

from project_indexer import get_project_manager

# Motadata project location
WORKSPACE_ROOT = "/home/harshil/TestMotadataProject/Motadata/motadata"

def main():
    print("=" * 80)
    print("MOTADATA CODEBASE INDEXING")
    print("=" * 80)
    print(f"\nWorkspace: {WORKSPACE_ROOT}")
    print(f"Target Collection: motadata_code")
    print(f"Embedding Model: jinaai/jina-embeddings-v2-base-code (768 dims)")
    print()
    
    # Get project manager
    manager = get_project_manager()
    
    # Check current status
    status = manager.get_status(WORKSPACE_ROOT)
    print(f"Current Status: {status['status']}")
    if status['status'] == 'indexed':
        print(f"  - Files: {status['file_count']}")
        print(f"  - Nodes: {status['node_count']}")
        print(f"  - Indexed at: {status['indexed_at']}")
        print("\n✓ Codebase already indexed!")
        return True
    
    # Start indexing
    print("\n" + "=" * 80)
    print("STARTING INDEXING...")
    print("=" * 80)
    
    start_time = time.time()
    try:
        project = manager.index_project(WORKSPACE_ROOT)
        duration = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("INDEXING COMPLETE")
        print("=" * 80)
        print(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        print(f"Files Indexed: {project.file_count}")
        print(f"Nodes Created: {project.node_count}")
        print(f"Status: {project.status}")
        print(f"Collection: {project.collection_name}")
        print()
        
        if project.status == 'indexed':
            print("✓ Indexing successful!")
            return True
        else:
            print(f"✗ Indexing failed with status: {project.status}")
            if project.error_message:
                print(f"  Error: {project.error_message}")
            return False
            
    except Exception as e:
        print(f"\n✗ Indexing failed with exception:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

