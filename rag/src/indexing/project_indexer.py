#!/usr/bin/env python3
"""
Project Indexer - Dynamic Multi-Project Indexing for RAG System

Manages multiple project indexes with:
- Separate Qdrant collection per project (project-based namespacing)
- Neo4j labels per project for graph relationships
- Background indexing with progress tracking
- Automatic project detection from workspace_root
"""

import os
import json
import hashlib
import threading
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, OptimizersConfigDiff, HnswConfigDiff
from sentence_transformers import SentenceTransformer

# Force CPU-only mode for embeddings
os.environ["CUDA_VISIBLE_DEVICES"] = ""


@dataclass
class ProjectIndex:
    """Metadata about an indexed project"""
    project_id: str  # Unique ID (hash of workspace_root)
    project_name: str  # Human-readable name
    workspace_root: str  # Absolute path
    collection_name: str  # Qdrant collection name
    indexed_at: Optional[str] = None
    file_count: int = 0
    node_count: int = 0
    status: str = "not_indexed"  # not_indexed, indexing, indexed, error
    progress: float = 0.0
    error_message: Optional[str] = None


@dataclass
class CodeNode:
    """A code element to be indexed"""
    id: str
    text: str  # Text to embed
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProjectIndexManager:
    """Manages multiple project indexes"""
    
    # Store project metadata
    _projects: Dict[str, ProjectIndex] = {}
    _indexing_locks: Dict[str, threading.Lock] = {}
    _index_file = Path(__file__).parent / "project_indexes.json"
    
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        embed_model: str = "jinaai/jina-embeddings-v2-base-code"
    ):
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
        
        # Lazy-load embedding model
        self._embed_model = None
        self._embed_model_name = embed_model
        
        # Load existing project metadata
        self._load_projects()
    
    @property
    def embed_model(self):
        """Lazy-load embedding model"""
        if self._embed_model is None:
            print(f"🔧 Loading embedding model: {self._embed_model_name}...")
            self._embed_model = SentenceTransformer(self._embed_model_name, trust_remote_code=True)
        return self._embed_model
    
    def _load_projects(self):
        """Load project metadata from disk"""
        if self._index_file.exists():
            try:
                with open(self._index_file, 'r') as f:
                    data = json.load(f)
                    for p in data:
                        proj = ProjectIndex(**p)
                        self._projects[proj.project_id] = proj
                print(f"📂 Loaded {len(self._projects)} project indexes")
            except Exception as e:
                print(f"⚠️ Error loading project indexes: {e}")
    
    def _save_projects(self):
        """Save project metadata to disk"""
        try:
            data = [asdict(p) for p in self._projects.values()]
            with open(self._index_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving project indexes: {e}")
    
    def get_project_id(self, workspace_root: str) -> str:
        """Generate unique project ID from workspace root"""
        return hashlib.md5(workspace_root.encode()).hexdigest()[:12]
    
    def get_collection_name(self, workspace_root: str) -> str:
        """Get Qdrant collection name for a project"""
        project_id = self.get_project_id(workspace_root)
        project_name = Path(workspace_root).name.lower().replace("-", "_").replace(" ", "_")
        return f"project_{project_name}_{project_id}"
    
    def get_project(self, workspace_root: str) -> Optional[ProjectIndex]:
        """Get project metadata"""
        project_id = self.get_project_id(workspace_root)
        return self._projects.get(project_id)
    
    def list_projects(self) -> List[ProjectIndex]:
        """List all indexed projects"""
        return list(self._projects.values())
    
    def is_indexed(self, workspace_root: str) -> bool:
        """Check if project is indexed"""
        project = self.get_project(workspace_root)
        return project is not None and project.status == "indexed"
    
    def get_status(self, workspace_root: str) -> Dict[str, Any]:
        """Get indexing status for a project"""
        project = self.get_project(workspace_root)
        if project is None:
            return {"status": "not_indexed", "workspace_root": workspace_root}
        return asdict(project)

    def _parse_java_file(self, file_path: Path, workspace_root: str) -> List[CodeNode]:
        """Parse a Java file into code nodes (simplified parser)"""
        nodes = []
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            rel_path = str(file_path.relative_to(workspace_root))

            # Extract package
            package = ""
            for line in content.split('\n'):
                if line.strip().startswith('package '):
                    package = line.strip().replace('package ', '').replace(';', '').strip()
                    break

            # Use AST Parser
            import sys
            from pathlib import Path as PathLib
            utils_path = PathLib(__file__).parent.parent / "utils"
            if str(utils_path) not in sys.path:
                sys.path.insert(0, str(utils_path))
            from javalang_parser import JavaParser
            parser = JavaParser()
            classes = parser.parse_file(str(file_path), content)

            for cls in classes:
                # Index Class
                nodes.append(CodeNode(
                    id=f"{rel_path}:{cls.qualified_name}",
                    text=f"Class: {cls.qualified_name}\nExtends: {cls.extends}\nImplements: {', '.join(cls.implements)}\nFile: {rel_path}\n{cls.content[:1000]}",
                    metadata={
                        "qualified_name": cls.qualified_name,
                        "node_type": "class",
                        "file_path": rel_path,
                        "package": cls.package,
                        "extends": cls.extends,
                        "implements": cls.implements,
                        "start_line": cls.start_line
                    }
                ))

                # Index Methods
                for method in cls.methods:
                    nodes.append(CodeNode(
                        id=f"{rel_path}:{cls.qualified_name}:{method.name}",
                        text=f"Method: {method.name}\nClass: {cls.qualified_name}\nReturns: {method.return_type}\nParams: {', '.join(method.parameters)}\nFile: {rel_path}\n{method.content[:1500]}",
                        metadata={
                            "qualified_name": f"{cls.qualified_name}.{method.name}",
                            "node_type": "method",
                            "file_path": rel_path,
                            "package": cls.package,
                            "return_type": method.return_type,
                            "start_line": method.start_line
                        }
                    ))

        except Exception as e:
            print(f"⚠️ Error parsing {file_path}: {e}")

        return nodes

    def index_project(self, workspace_root: str, file_extensions: List[str] = None) -> ProjectIndex:
        """Index a project (blocking)"""
        if file_extensions is None:
            file_extensions = ['.java']  # Default to Java

        workspace_path = Path(workspace_root)
        if not workspace_path.exists():
            raise ValueError(f"Workspace not found: {workspace_root}")

        project_id = self.get_project_id(workspace_root)
        collection_name = self.get_collection_name(workspace_root)
        project_name = workspace_path.name

        # Create or update project entry
        project = ProjectIndex(
            project_id=project_id,
            project_name=project_name,
            workspace_root=workspace_root,
            collection_name=collection_name,
            status="indexing",
            progress=0.0
        )
        self._projects[project_id] = project
        self._save_projects()

        try:
            # Find all matching files
            all_files = []
            for ext in file_extensions:
                all_files.extend(workspace_path.rglob(f"*{ext}"))

            # Filter out test/build directories and patch files
            exclude_patterns = [
                '/test/', '/build/', '/target/', '/.git/',
                '/Patch', 'Patch.java'  # Exclude patch migration files (e.g., Patch810.java, Patch811.java)
            ]
            files = [f for f in all_files if not any(x in str(f) for x in exclude_patterns)]
            project.file_count = len(files)
            print(f"📁 Found {len(files)} files to index in {project_name}")

            # Parse all files into nodes
            all_nodes = []
            for i, file_path in enumerate(files):
                nodes = self._parse_java_file(file_path, workspace_root)
                all_nodes.extend(nodes)
                project.progress = (i + 1) / len(files) * 0.5  # 50% for parsing

            print(f"📝 Extracted {len(all_nodes)} code nodes")

            # Create Qdrant collection (delete existing if present)
            try:
                self.qdrant.delete_collection(collection_name)
                print(f"🗑️ Deleted existing collection: {collection_name}")
            except Exception as e:
                print(f"ℹ️ No existing collection to delete: {e}")

            try:
                self.qdrant.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.embed_model.get_sentence_embedding_dimension(),
                        distance=Distance.COSINE
                    ),
                    optimizers_config=OptimizersConfigDiff(indexing_threshold=10000),
                    hnsw_config=HnswConfigDiff(m=16, ef_construct=100)
                )
                print(f"✅ Created collection: {collection_name}")
            except Exception as e:
                # If collection exists, try to use it
                print(f"⚠️ Collection creation issue: {e}")
                try:
                    # Force delete and recreate
                    self.qdrant.delete_collection(collection_name)
                    self.qdrant.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=self.embed_model.get_sentence_embedding_dimension(),
                            distance=Distance.COSINE
                        ),
                        optimizers_config=OptimizersConfigDiff(indexing_threshold=10000),
                        hnsw_config=HnswConfigDiff(m=16, ef_construct=100)
                    )
                    print(f"✅ Recreated collection after force delete")
                except Exception as e2:
                    raise Exception(f"Failed to create collection: {e2}")

            # Batch embed and index
            batch_size = 32
            for i in range(0, len(all_nodes), batch_size):
                batch = all_nodes[i:i+batch_size]
                texts = [n.text for n in batch]
                embeddings = self.embed_model.encode(texts, show_progress_bar=False)

                points = [
                    PointStruct(
                        id=hash(n.id) % (2**63),  # Convert to positive int
                        vector=embeddings[j].tolist(),
                        payload=n.metadata
                    )
                    for j, n in enumerate(batch)
                ]

                self.qdrant.upsert(collection_name=collection_name, points=points)
                project.progress = 0.5 + ((i + batch_size) / len(all_nodes)) * 0.5  # 50-100% for indexing

            # Update project status
            project.node_count = len(all_nodes)
            project.indexed_at = datetime.now().isoformat()
            project.status = "indexed"
            project.progress = 1.0
            self._save_projects()

            # Also populate Neo4j Graph if available
            try:
                from neo4j import GraphDatabase
                neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                neo4j_user = os.getenv("NEO4J_USER", "neo4j")
                neo4j_pass = os.getenv("NEO4J_PASSWORD", "password")
                
                driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
                with driver.session() as session:
                    # Create nodes
                    for node in all_nodes:
                        if node.metadata.get("node_type") == "class":
                            session.run(
                                """
                                MERGE (c:Class {qualified_name: $name})
                                SET c.file_path = $file, c.package = $pkg
                                """,
                                name=node.metadata["qualified_name"],
                                file=node.metadata["file_path"],
                                pkg=node.metadata["package"]
                            )
                    
                    # Create relationships
                    for node in all_nodes:
                        if node.metadata.get("node_type") == "class":
                            # EXTENDS
                            parent = node.metadata.get("extends")
                            if parent:
                                # Try to find fully qualified parent if possible, else match by name
                                session.run(
                                    """
                                    MATCH (c:Class {qualified_name: $name})
                                    MERGE (p:Class {qualified_name: $parent})
                                    MERGE (c)-[:EXTENDS]->(p)
                                    """,
                                    name=node.metadata["qualified_name"],
                                    parent=parent
                                )
                            
                            # IMPLEMENTS
                            interfaces = node.metadata.get("implements", [])
                            for iface in interfaces:
                                session.run(
                                    """
                                    MATCH (c:Class {qualified_name: $name})
                                    MERGE (i:Class {qualified_name: $iface})
                                    MERGE (c)-[:IMPLEMENTS]->(i)
                                    """,
                                    name=node.metadata["qualified_name"],
                                    iface=iface
                                )
                driver.close()
                print(f"✅ Populated Neo4j graph for {project_name}")
            except Exception as e:
                print(f"⚠️ Neo4j population failed (skipping): {e}")

            print(f"✅ Indexed {project_name}: {project.node_count} nodes in collection '{collection_name}'")
            return project

        except Exception as e:
            project.status = "error"
            project.error_message = str(e)
            self._save_projects()
            raise

    def index_project_async(self, workspace_root: str, file_extensions: List[str] = None):
        """Index a project in background thread"""
        def _index():
            try:
                self.index_project(workspace_root, file_extensions)
            except Exception as e:
                print(f"❌ Background indexing failed: {e}")

        thread = threading.Thread(target=_index, daemon=True)
        thread.start()
        return {"status": "started", "workspace_root": workspace_root}

    def search(self, workspace_root: str, query: str, top_k: int = 5) -> List[Dict]:
        """Search project index"""
        collection_name = self.get_collection_name(workspace_root)

        try:
            query_vector = self.embed_model.encode(query).tolist()
            # Use query_points instead of search (newer Qdrant client API)
            results = self.qdrant.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=top_k
            )

            return [
                {
                    "score": r.score,
                    "qualified_name": r.payload.get("qualified_name", ""),
                    "node_type": r.payload.get("node_type", ""),
                    "file_path": r.payload.get("file_path", ""),
                    "start_line": r.payload.get("start_line", 0),
                    "package": r.payload.get("package", "")
                }
                for r in results.points
            ]
        except Exception as e:
            print(f"⚠️ Search error: {e}")
            return []

    def delete_project(self, workspace_root: str) -> bool:
        """Delete project index"""
        project_id = self.get_project_id(workspace_root)
        project = self._projects.get(project_id)

        if project:
            try:
                self.qdrant.delete_collection(project.collection_name)
            except:
                pass
            del self._projects[project_id]
            self._save_projects()
            return True
        return False


# Singleton instance
_project_manager: Optional[ProjectIndexManager] = None

def get_project_manager() -> ProjectIndexManager:
    """Get singleton ProjectIndexManager instance"""
    global _project_manager
    if _project_manager is None:
        _project_manager = ProjectIndexManager()
    return _project_manager

