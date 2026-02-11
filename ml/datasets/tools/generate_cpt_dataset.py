#!/usr/bin/env python3
"""
CPT Dataset Generator - RAW FORMAT (Correct for Continual Pre-Training)

Instead of snippets, CPT needs COMPLETE FILES as they exist in the codebase.
Each line in JSONL = one complete raw Java file with full context.

Why complete files?
- CPT learns token distributions as they naturally occur
- Distribution-aligned: code as developers actually write it
- Full context: imports, class hierarchy, surrounding methods
- Not curated/explanatory, just raw code from the filesystem
"""

import json
import os
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class RawCPTConfig:
    """Configuration for raw CPT dataset generation"""
    internal_repo_path: str = "/home/harshil/Motadata/motadata"
    datasets_path: str = "/home/harshil/Harshil-PoCs/datasets"
    output_dir: str = "/home/harshil/Harshil-PoCs/datasets/cpt_v2_raw"
    
    # File types to include
    file_extensions: List[str] = None
    
    # Security: files to exclude
    security_patterns: List[str] = None
    
    def __post_init__(self):
        if self.file_extensions is None:
            self.file_extensions = ['.java', '.json', '.yaml', '.yml', '.py']
        
        if self.security_patterns is None:
            self.security_patterns = [
                "GlobalConstants", "ErrorCodes", "DBConstants", "OAuthUtil",
                "LDAPServer", "User", "Integration", "ProxyServer",
                "PersonalAccessToken", "RadiusServer", "APIConstants",
                "RUMServiceProfile", "MailServerConfiguration",
                "LogPatternDetector", "GeoDBSyncJob", "ServiceOpsIntegration",
                "IntegrationConstants", "SSHClientManager", "ConfigConstants",
                "SNMPTrapListenerConfiguration", "ErrorMessageConstants"
            ]


class CodeHygiene:
    """Remove secrets and sensitive data"""
    
    @staticmethod
    def has_secrets(content: str) -> bool:
        """Check if content contains secrets"""
        secret_patterns = [
            r"password\s*=",
            r"secret\s*=",
            r"api[_-]?key\s*=",
            r"token\s*=",
            r"credential",
            r"aws_access",
            r"BEGIN RSA PRIVATE",
            r"BEGIN CERTIFICATE",
        ]
        for pattern in secret_patterns:
            if __import__('re').search(pattern, content, __import__('re').IGNORECASE):
                return True
        return False
    
    @staticmethod
    def is_secure_file(filename: str, config: RawCPTConfig) -> bool:
        """Check if file should be included (no secrets in filename)"""
        for pattern in config.security_patterns:
            if pattern in filename:
                return False
        return True


class RawCPTDatasetGenerator:
    """Generate CPT dataset from complete, raw Java files"""
    
    def __init__(self, config: RawCPTConfig = None):
        self.config = config or RawCPTConfig()
        self.total_tokens = 0
        self.files_processed = 0
        self.files_skipped = 0
        self.security_exclusions = []
        
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough token estimation: ~4 chars per token"""
        return len(text) // 4
    
    def collect_java_files(self) -> List[Path]:
        """Collect all code files from Motadata repo and datasets folder"""
        code_files = []
        
        # Phase 1: Motadata repo (Java, JSON, YAML)
        repo_path = Path(self.config.internal_repo_path)
        if repo_path.exists():
            for ext in self.config.file_extensions:
                for file in repo_path.rglob(f"*{ext}"):
                    # Skip test files, build artifacts
                    path_str = str(file).lower()
                    if any(skip in path_str for skip in ["test", "target", "node_modules", "test-plugin-metrics"]):
                        continue
                    code_files.append(file)
            print(f"📂 Found {len(code_files)} code files in {repo_path}")
        else:
            print(f"❌ Repository path not found: {repo_path}")
        
        # Phase 2: Datasets folder (Python scripts, YAML configs)
        datasets_path = Path(self.config.datasets_path)
        if datasets_path.exists():
            datasets_files = []
            for ext in ['.py', '.yaml', '.yml']:
                for file in datasets_path.rglob(f"*{ext}"):
                    # Skip __pycache__, .venv
                    path_str = str(file)
                    if any(skip in path_str for skip in ["__pycache__", ".venv", ".git", "node_modules"]):
                        continue
                    datasets_files.append(file)
            code_files.extend(datasets_files)
            print(f"📂 Found {len(datasets_files)} additional files in {datasets_path}")
        
        print(f"📊 Total files to process: {len(code_files)}")
        return code_files
    
    def generate(self):
        """Generate raw CPT dataset from complete files"""
        print("=" * 70)
        print("🔧 CPT Dataset Generator - RAW FORMAT (Multi-Language)")
        print("=" * 70)
        
        code_files = self.collect_java_files()
        all_entries = []
        
        print(f"\n📖 Processing {len(code_files)} code files...")
        
        for idx, code_file in enumerate(code_files):
            # Progress report every 50 files
            if (idx + 1) % 50 == 0:
                print(f"   Progress: {idx + 1}/{len(code_files)} files, {self.total_tokens:,} tokens")
            
            try:
                # Check security patterns in filename
                if not CodeHygiene.is_secure_file(code_file.name, self.config):
                    self.files_skipped += 1
                    self.security_exclusions.append(code_file.name)
                    continue
                
                # Read complete file
                with open(code_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().strip()
                
                if not content:
                    self.files_skipped += 1
                    continue
                
                # Check for secrets in content
                if CodeHygiene.has_secrets(content):
                    self.files_skipped += 1
                    self.security_exclusions.append(java_file.name)
                    continue
                
                # Add complete file as single entry
                tokens = self.estimate_tokens(content)
                self.total_tokens += tokens
                
                entry = {
                    "text": content  # RAW file content, no wrapping
                }
                all_entries.append(entry)
                self.files_processed += 1
                
            except Exception as e:
                self.files_skipped += 1
                continue
        
        # Write output
        output_path = Path(self.config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        dataset_file = output_path / "cpt_dataset_raw.jsonl"
        print(f"\n💾 Writing {len(all_entries)} files to {dataset_file}...")
        
        with open(dataset_file, 'w') as f:
            for entry in all_entries:
                f.write(json.dumps(entry) + '\n')
        
        # Write metadata
        metadata_file = output_path / "cpt_metadata_raw.json"
        metadata = {
            "total_files": len(all_entries),
            "total_tokens": self.total_tokens,
            "files_processed": self.files_processed,
            "files_skipped": self.files_skipped,
            "security_exclusions": len(self.security_exclusions),
            "excluded_files": self.security_exclusions[:20],  # First 20
            "avg_tokens_per_file": self.total_tokens // len(all_entries) if all_entries else 0,
            "format": "raw_cpt",
            "file_types": self.config.file_extensions,
            "description": "Complete files (Java, JSON, YAML, Python) as they exist in repo, no snippets"
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Print summary
        print("\n" + "=" * 70)
        print("✅ RAW CPT Dataset Generation Complete!")
        print("=" * 70)
        print(f"📊 Statistics:")
        print(f"   • Total files: {len(all_entries):,}")
        print(f"   • Total tokens: {self.total_tokens:,}")
        print(f"   • Files processed: {self.files_processed:,}")
        print(f"   • Files skipped: {self.files_skipped:,}")
        print(f"   • Avg tokens/file: {self.total_tokens // len(all_entries) if all_entries else 0:,}")
        print(f"   • Security exclusions: {len(self.security_exclusions)}")
        
        if self.security_exclusions[:5]:
            print(f"\n🔒 Sample exclusions:")
            for f in self.security_exclusions[:5]:
                print(f"   - {f}")
        
        print(f"\n📁 Output:")
        print(f"   • Dataset: {dataset_file}")
        print(f"   • Metadata: {metadata_file}")
        
        print("\n" + "=" * 70)
        print("✅ Success! Raw CPT dataset ready at:")
        print(f"   {dataset_file}")
        print("=" * 70)


if __name__ == "__main__":
    generator = RawCPTDatasetGenerator()
    generator.generate()
