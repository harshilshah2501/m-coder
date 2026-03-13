import unittest
from pathlib import Path
import shutil
import tempfile
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project_indexer import get_project_manager, CodeNode

class TestProjectIndexer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.workspace_root = os.path.join(self.test_dir, "workspace")
        os.makedirs(self.workspace_root)
        
        # Create a dummy Java file
        self.java_file = os.path.join(self.workspace_root, "Test.java")
        with open(self.java_file, "w") as f:
            f.write("""
package com.example;

public class Test extends BaseClass implements InterfaceA, InterfaceB {
    public void testMethod(String arg) {
        System.out.println("Hello");
    }
}
""")
        
        self.manager = get_project_manager()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_parser_integration(self):
        """Test that _parse_java_file uses the new parser and extracts relationships"""
        file_path = Path(self.java_file)
        nodes = self.manager._parse_java_file(file_path, self.workspace_root)
        
        # Check if we got nodes
        self.assertTrue(len(nodes) > 0)
        
        # Find the class node
        class_node = next((n for n in nodes if n.metadata.get("node_type") == "class"), None)
        self.assertIsNotNone(class_node)
        
        # Verify metadata extraction (which proves javalang_parser is working)
        self.assertEqual(class_node.metadata["qualified_name"], "com.example.Test")
        self.assertEqual(class_node.metadata["extends"], "BaseClass")
        self.assertEqual(class_node.metadata["implements"], ["InterfaceA", "InterfaceB"])
        
        print("\n✅ Parser Integration Verified:")
        print(f"  Class: {class_node.metadata['qualified_name']}")
        print(f"  Extends: {class_node.metadata['extends']}")
        print(f"  Implements: {class_node.metadata['implements']}")

if __name__ == "__main__":
    unittest.main()
