import os
import sys
from pathlib import Path

# Add rag-system to path
sys.path.append(str(Path(__file__).parent / "rag-system"))

from project_indexer import get_project_manager

# Create a dummy Java file for testing
test_dir = Path("test_project/src/main/java/com/example")
test_dir.mkdir(parents=True, exist_ok=True)

(test_dir / "BaseService.java").write_text("""
package com.example;
public class BaseService {
    public void init() { }
}
""")

(test_dir / "UserService.java").write_text("""
package com.example;
public class UserService extends BaseService implements IService {
    public void createUser(String name) { }
}
""")

(test_dir / "IService.java").write_text("""
package com.example;
public interface IService {
    void execute();
}
""")

print("🚀 Starting test indexing...")
manager = get_project_manager()
project = manager.index_project(str(Path("test_project").absolute()))

print(f"✅ Indexing complete. Nodes: {project.node_count}")
print("Check Neo4j for EXTENDS relationship between UserService and BaseService")
