#!/usr/bin/env python3
"""
Re-index Codebase Script
Triggers a full re-index of the Motadata codebase using the new AST parser.
"""

import os
import sys
import time

# Add current directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project_indexer import get_project_manager

WORKSPACE_ROOT = "/home/harshil/TestMotadataProject/Motadata/motadata"

def main():
    print(f"Starting re-indexing for: {WORKSPACE_ROOT}")
    
    manager = get_project_manager()
    
    # Check if project exists
    status = manager.get_status(WORKSPACE_ROOT)
    print(f"Current status: {status['status']}")
    
    start_time = time.time()
    try:
        # Force re-index
        print("Indexing started... this may take a while.")
        project = manager.index_project(WORKSPACE_ROOT)
        
        duration = time.time() - start_time
        print(f"Indexing completed in {duration:.2f} seconds.")
        print(f"Files: {project.file_count}")
        print(f"Nodes: {project.node_count}")
        print(f"Status: {project.status}")
        
    except Exception as e:
        print(f"Indexing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
