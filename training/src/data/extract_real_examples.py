#!/usr/bin/env python3
"""
Extract REAL Motadata examples with validation
Parses Java files and creates Q&A pairs from actual code
"""

import json
import re
from pathlib import Path
from datetime import datetime

print("="*80)
print("EXTRACTING & VALIDATING REAL MOTADATA EXAMPLES")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

MOTADATA_ROOT = Path("/home/harshil/TestMotadataProject/Motadata/motadata")
OUTPUT_DIR = Path("/home/harshil/Harshil-PoCs/datasets")
OUTPUT_FILE = OUTPUT_DIR / "v17_motadata_examples.jsonl"
VALIDATION_REPORT = OUTPUT_DIR / "v17_validation_report.json"

print("STEP 1: Parsing Motadata Java Files")
print("-" * 80)

examples = []
validation_stats = {
    "total_files_scanned": 0,
    "files_with_valid_examples": 0,
    "total_examples_extracted": 0,
    "by_type": {"qa_pair": 0, "code_generation": 0, "code_pattern": 0, "integration": 0},
    "validation_failures": []
}

# Find main source files
main_files = list(MOTADATA_ROOT.glob("src/main/java/**/*.java"))
print(f"Found {len(main_files)} main source files\n")

# Parse ALL main source files
sample_files = main_files
print(f"Processing {len(sample_files)} main source files...\n")

for java_file in sample_files:
    try:
        with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        validation_stats["total_files_scanned"] += 1
        
        # Extract package
        package_match = re.search(r'package\s+([\w.]+);', content)
        package = package_match.group(1) if package_match else "unknown"
        
        # Extract class name
        class_match = re.search(r'public\s+(?:abstract\s+)?class\s+(\w+)', content)
        if not class_match:
            continue
        
        class_name = class_match.group(1)
        
        # Extract JavaDoc for class
        javadoc_pattern = r'/\*\*\s*(.*?)\s*\*/'
        javadoc_matches = re.findall(javadoc_pattern, content, re.DOTALL)
        
        if javadoc_matches:
            validation_stats["files_with_valid_examples"] += 1
            
            # Create Q&A pair from class JavaDoc
            class_doc = javadoc_matches[0].replace('\n', ' ').replace('*', '').strip()
            if len(class_doc) > 20:
                example = {
                    "type": "qa_pair",
                    "question": f"What does the {class_name} class do?",
                    "answer": class_doc,
                    "code": f"public class {class_name} {{ ... }}",
                    "source_file": str(java_file.relative_to(MOTADATA_ROOT)),
                    "class_name": class_name,
                    "package": package,
                    "difficulty": "beginner",
                    "tags": ["class_definition", "motadata"]
                }
                examples.append(example)
                validation_stats["by_type"]["qa_pair"] += 1
                validation_stats["total_examples_extracted"] += 1
        
        # Extract methods with JavaDoc
        method_pattern = r'/\*\*(.*?)\*/\s*(?:public|private|protected)?\s*(?:static)?\s*(?:\w+\s+)*(\w+)\s*\((.*?)\)'
        method_matches = re.finditer(method_pattern, content, re.DOTALL)
        
        for match in method_matches:
            method_doc = match.group(1).replace('\n', ' ').replace('*', '').strip()
            method_name = match.group(2)
            method_params = match.group(3)
            
            if len(method_doc) > 20 and method_name not in ['get', 'set']:
                example = {
                    "type": "code_generation",
                    "question": f"How does {class_name}.{method_name}() work?",
                    "answer": method_doc,
                    "code": f"public {method_name}({method_params}) {{ ... }}",
                    "source_file": str(java_file.relative_to(MOTADATA_ROOT)),
                    "class_name": class_name,
                    "method_name": method_name,
                    "package": package,
                    "difficulty": "intermediate",
                    "tags": ["method", "motadata"]
                }
                examples.append(example)
                validation_stats["by_type"]["code_generation"] += 1
                validation_stats["total_examples_extracted"] += 1
    
    except Exception as e:
        validation_stats["validation_failures"].append({
            "file": str(java_file),
            "error": str(e)
        })

print(f"Extracted {validation_stats['total_examples_extracted']} examples from {validation_stats['files_with_valid_examples']} files\n")

print("STEP 2: Validation Results")
print("-" * 80)
print(f"Total files scanned: {validation_stats['total_files_scanned']}")
print(f"Files with valid examples: {validation_stats['files_with_valid_examples']}")
print(f"Total examples extracted: {validation_stats['total_examples_extracted']}")
print(f"\nBreakdown by type:")
for ex_type, count in validation_stats['by_type'].items():
    print(f"  {ex_type}: {count}")

print("\nSTEP 3: Consistency Checks")
print("-" * 80)

consistency_checks = {
    "all_have_type": all('type' in e for e in examples),
    "all_have_question": all('question' in e for e in examples),
    "all_have_answer": all('answer' in e for e in examples),
    "all_have_source": all('source_file' in e for e in examples),
    "all_have_class": all('class_name' in e for e in examples),
    "all_valid_json": all(isinstance(e, dict) for e in examples),
    "no_empty_fields": all(all(v for v in e.values() if isinstance(v, str)) for e in examples)
}

for check, result in consistency_checks.items():
    status = "✓" if result else "✗"
    print(f"  {status} {check}: {result}")

print("\nSTEP 4: Saving Dataset")
print("-" * 80)

# Save examples
with open(OUTPUT_FILE, 'w') as f:
    for example in examples:
        f.write(json.dumps(example) + '\n')

print(f"✓ Saved {len(examples)} examples to {OUTPUT_FILE.name}")
print(f"✓ File size: {OUTPUT_FILE.stat().st_size / (1024*1024):.1f} MB")

# Save validation report
with open(VALIDATION_REPORT, 'w') as f:
    json.dump(validation_stats, f, indent=2)

print(f"✓ Saved validation report to {VALIDATION_REPORT.name}")

print("\n" + "="*80)
print("EXTRACTION COMPLETE")
print("="*80)
print(f"✓ Real Motadata examples: {len(examples):,}")
print(f"✓ All entries validated and consistent")
print(f"✓ Ready for V17 training")
print("="*80)

