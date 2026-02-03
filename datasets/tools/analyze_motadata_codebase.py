#!/usr/bin/env python3
"""
Motadata Codebase Structure Analyzer

Analyzes the Motadata repository to understand file distribution and
identify gaps in the CPT dataset generation.
"""

import os
from pathlib import Path
from collections import defaultdict
import re

REPO_PATH = "/home/harshil/Motadata/motadata"

# File patterns to track (filename patterns)
FILE_PATTERNS = {
    "Store": lambda f: "Store" in f,
    "Auth": lambda f: "Auth" in f or "auth" in f.lower(),
    "Security": lambda f: "Security" in f or "security" in f.lower(),
    "Service": lambda f: "Service" in f,
    "Validator": lambda f: "Validator" in f,
    "Exception": lambda f: "Exception" in f,
    "Config": lambda f: "Config" in f,
    "Handler": lambda f: "Handler" in f,
    "Repository": lambda f: "Repository" in f,
    "DAO": lambda f: "DAO" in f,
    "Manager": lambda f: "Manager" in f,
    "DTO": lambda f: "DTO" in f,
    "Request": lambda f: "Request" in f,
    "Response": lambda f: "Response" in f,
    "Converter": lambda f: "Converter" in f,
    "Verticle": lambda f: "Verticle" in f,
    "Router": lambda f: "Router" in f,
    "Engine": lambda f: "Engine" in f,
    "Consumer": lambda f: "Consumer" in f,
    "Provider": lambda f: "Provider" in f,
    "Factory": lambda f: "Factory" in f,
    "Abstract": lambda f: f.startswith("Abstract"),
    "EventBus": lambda f: "EventBus" in f or "eventbus" in f.lower(),
    "APIRouter": lambda f: "APIRouter" in f,
}

def main():
    repo = Path(REPO_PATH)
    
    if not repo.exists():
        print(f"❌ Repo not found: {REPO_PATH}")
        return
    
    print("🔍 Analyzing Motadata Codebase Structure...")
    print("=" * 90)
    
    # Scan all Java files
    pattern_counts = defaultdict(list)  # pattern -> list of files
    directory_counts = defaultdict(int)
    total_files = 0
    java_files = []
    
    for java_file in repo.rglob("*.java"):
        # Skip test files
        if "test" in str(java_file).lower():
            continue
        
        # Only include src/main files
        if "src/main" not in str(java_file):
            continue
        
        total_files += 1
        filename = java_file.name
        java_files.append(java_file)
        
        # Count by directory
        rel_path = java_file.relative_to(repo)
        dir_path = str(rel_path.parent)
        directory_counts[dir_path] += 1
        
        # Count by pattern - find first matching pattern
        matched = False
        for pattern_name, pattern_func in FILE_PATTERNS.items():
            if pattern_func(filename):
                pattern_counts[pattern_name].append(filename)
                matched = True
                break
        
        if not matched:
            pattern_counts["Other"].append(filename)
    
    # Print results
    print(f"\n📊 TOTAL JAVA FILES (src/main): {total_files}")
    
    print(f"\n📋 File Distribution by Pattern:")
    print("-" * 90)
    
    sorted_patterns = sorted(pattern_counts.items(), key=lambda x: len(x[1]), reverse=True)
    
    for pattern, files in sorted_patterns:
        count = len(files)
        pct = (count / total_files * 100) if total_files > 0 else 0
        print(f"  {pattern:20s}: {count:4d} files ({pct:5.1f}%)")
    
    print(f"\n📂 Top 15 Directories by File Count:")
    print("-" * 90)
    
    sorted_dirs = sorted(directory_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    
    for dir_path, count in sorted_dirs:
        # Shorten path for display
        short_path = dir_path.replace("src/main/java/com/mindarray/", "")
        print(f"  {count:3d} files: {short_path}")
    
    # Coverage analysis
    print(f"\n🎯 Current CPT Dataset vs Actual Codebase:")
    print("-" * 90)
    print(f"Current Dataset Focus (from v1 review):")
    print(f"  • EventBus:    54.7%  (2,235 chunks)")
    print(f"  • Schema:      22.9%    (936 chunks)")
    print(f"  • AbstractXxx: 10.7%    (440 chunks)")
    print(f"  • Other:       11.7%    (475 chunks)")
    print(f"  TOTAL:        100.0%  (4,086 chunks)")
    
    print(f"\nActual Codebase Distribution (top 10):")
    for i, (pattern, files) in enumerate(sorted_patterns[:10], 1):
        count = len(files)
        pct = (count / total_files * 100) if total_files > 0 else 0
        print(f"  {i:2d}. {pattern:20s}: {count:4d} files ({pct:5.1f}%)")
    
    # Identify gaps
    print(f"\n⚠️  COVERAGE GAPS (missing/under-represented in current dataset):")
    print("-" * 90)
    
    covered = {"EventBus", "Schema", "AbstractAPI", "AbstractConfigStore", "Verticle", "Handler"}
    
    for pattern, files in sorted_patterns:
        count = len(files)
        if count > 0 and pattern not in covered and pattern != "Other":
            pct = (count / total_files * 100) if total_files > 0 else 0
            print(f"  ❌ {pattern:20s}: {count:4d} files ({pct:5.1f}%) - MISSING OR UNDER-REPRESENTED")
            # Show sample files
            samples = files[:3]
            for sample in samples:
                print(f"       └─ {sample}")
    
    # Recommendations
    print(f"\n✅ RECOMMENDATIONS FOR CPT V2 EXPANSION:")
    print("-" * 90)
    print(f"Priority: HIGH (Business Logic + Persistence)")
    print(f"  1. Service classes     - Core business logic layer")
    print(f"  2. Store subclasses    - Database persistence patterns")
    print(f"  3. Manager classes     - Coordination and orchestration")
    print(f"  4. Repository/DAO      - Data access layer")
    print(f"")
    print(f"Priority: MEDIUM (Validation + Configuration)")
    print(f"  5. Validator classes   - Input validation patterns")
    print(f"  6. Config classes      - Configuration management")
    print(f"  7. Exception classes   - Error types and hierarchy")
    print(f"  8. Router classes      - API routing")
    print(f"")
    print(f"Priority: MEDIUM (Data Models + Utilities)")
    print(f"  9. DTO/Request/Response - Data transfer objects")
    print(f" 10. Converter classes   - Data transformation")
    print(f" 11. Factory classes     - Object creation patterns")
    print(f" 12. Provider classes    - Service provisioning")
    print(f"")
    print(f"Priority: MEDIUM (Security)")
    print(f" 13. Auth/Security files - Authentication/authorization")
    print(f"")
    print(f"Target Expansion:")
    print(f"  • Current: 25M tokens (4,086 chunks, EventBus-heavy)")
    print(f"  • Target:  100-150M tokens with balanced coverage")
    print(f"  • Rebalance EventBus from 54.7% to 20-30%")
    print(f"  • Introduce Service, Store, Manager to 20-30% coverage")
    print(f"  • Maintain comprehensive architectural patterns")
    print("=" * 90)

if __name__ == "__main__":
    main()
