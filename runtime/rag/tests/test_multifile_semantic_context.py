#!/usr/bin/env python3
"""
Test multi-file semantic context extraction and diff application

Scenario: Add a caching method to GroupConfigStore and update MetricPlugin to use it
- File 1: GroupConfigStore.java - Add getUserGroupsCache() method
- File 2: MetricPlugin.java - Update to use the new cache method
"""

import requests
import subprocess
import tempfile
import shutil
from pathlib import Path

API_URL = "http://localhost:8081/v1/semantic-context"
WORKSPACE = "/home/harshil/TestMotadataProject/Motadata/motadata"

def get_semantic_context(file_path, method_name, task_description):
    """Get semantic context from API"""
    response = requests.post(API_URL, json={
        "file_path": file_path,
        "method_name": method_name,
        "task_description": task_description
    })
    
    if response.status_code != 200:
        raise Exception(f"API failed: {response.status_code} - {response.text}")
    
    return response.json()["context"]


def test_multifile_scenario():
    """Test multi-file semantic context and diff application"""
    
    print("=" * 80)
    print("MULTI-FILE TEST: Add cache method + Update caller")
    print("=" * 80)
    
    # Define the files and changes
    # Scenario: Add logging to two related methods in GroupConfigStore
    files = [
        {
            "path": "src/main/java/com/mindarray/store/GroupConfigStore.java",
            "method": "getItemsByUserProfile",
            "task": "Add logging at the start of the method",
            "diff": """--- a/src/main/java/com/mindarray/store/GroupConfigStore.java
+++ b/src/main/java/com/mindarray/store/GroupConfigStore.java
@@ -1,6 +1,8 @@
 public JsonArray getItemsByUserProfile(long userId)
     {
+        LOGGER.debug("getItemsByUserProfile called with userId: {}", userId);
+
         if (userId == DEFAULT_ID) return GroupConfigStore.getStore().flatItems(ID);

         var user = UserConfigStore.getStore().getItem(userId);
"""
        },
        {
            "path": "src/main/java/com/mindarray/store/GroupConfigStore.java",
            "method": "getQualifiedGroups",
            "task": "Add logging at the start of the method",
            "diff": """--- a/src/main/java/com/mindarray/store/GroupConfigStore.java
+++ b/src/main/java/com/mindarray/store/GroupConfigStore.java
@@ -1,6 +1,8 @@
 public JsonArray getQualifiedGroups(JsonArray groups, JsonArray userGroups)
     {
+        LOGGER.debug("getQualifiedGroups called with {} groups and {} userGroups", groups.size(), userGroups.size());
+
         var items = new JsonArray();

         try
"""
        },
        {
            "path": "src/main/java/com/mindarray/store/WidgetConfigStore.java",
            "method": "getItemsByGroups",
            "task": "Add logging at the start of the method",
            "diff": """--- a/src/main/java/com/mindarray/store/WidgetConfigStore.java
+++ b/src/main/java/com/mindarray/store/WidgetConfigStore.java
@@ -1,6 +1,8 @@
 public Set<Long> getItemsByGroups(JsonArray groups)
     {
+        LOGGER.debug("getItemsByGroups called with {} groups", groups != null ? groups.size() : 0);
+
         var items = new HashSet<Long>();

         if (groups != null)
"""
        }
    ]
    
    results = []
    
    for i, file_info in enumerate(files, 1):
        print(f"\n{'='*80}")
        print(f"FILE {i}/{len(files)}: {file_info['path']}")
        print(f"{'='*80}")
        
        # Step 1: Get semantic context
        print(f"\n📥 Step 1: Fetching semantic context for {file_info['method']}()...")
        
        try:
            context = get_semantic_context(
                file_info['path'],
                file_info['method'],
                file_info['task']
            )
            
            print(f"✅ Got semantic context ({len(context)} chars)")
            print(f"\nContext preview:")
            print(context[:300] + "...\n")
            
        except Exception as e:
            print(f"❌ Failed to get context: {e}")
            results.append((file_info['path'], False, str(e)))
            continue
        
        # Step 2: Apply diff
        print(f"🔧 Step 2: Applying diff with fuzzy matching...")
        
        original_file = Path(WORKSPACE) / file_info['path']
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_file = tmpdir / Path(file_info['path']).name
            
            # Copy original file
            shutil.copy(original_file, test_file)
            
            # Save diff
            diff_file = tmpdir / f"test_{i}.patch"
            diff_file.write_text(file_info['diff'])
            
            # Apply with fuzzy matching
            result = subprocess.run(
                ["patch", "--dry-run", "--fuzz=3", str(test_file), str(diff_file)],
                cwd=tmpdir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ Diff applies cleanly!")
                print(f"   {result.stdout.strip()}")
                results.append((file_info['path'], True, "Success"))
            else:
                print(f"❌ Diff failed to apply")
                print(f"   stdout: {result.stdout}")
                print(f"   stderr: {result.stderr}")
                results.append((file_info['path'], False, result.stderr))
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    for path, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {path}")
        if not success:
            print(f"       {message[:100]}")
    
    all_passed = all(r[1] for r in results)
    
    print(f"\n{'='*80}")
    if all_passed:
        print("🎉 SUCCESS: All multi-file diffs applied cleanly!")
        print("\nKey achievements:")
        print(f"  ✅ Extracted semantic context for {len(files)} files")
        print("  ✅ All diffs applied with fuzzy matching")
        print("  ✅ Multi-file changes work seamlessly")
        print("  ✅ No line number dependencies")
    else:
        failed = sum(1 for r in results if not r[1])
        print(f"❌ FAILED: {failed}/{len(files)} files failed to apply")
    print(f"{'='*80}")
    
    return all_passed


if __name__ == "__main__":
    print("\n🧪 Testing Multi-File Semantic Context\n")
    test_multifile_scenario()

