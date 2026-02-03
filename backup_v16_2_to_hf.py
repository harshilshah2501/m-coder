#!/usr/bin/env python3
"""
Backup V16.2 Model to Hugging Face
===================================
Uploads the merged v16.2 model to private HF repo
"""

import os
import json
from pathlib import Path
from datetime import datetime
from huggingface_hub import HfApi, create_repo

# Configuration
MODEL_PATH = Path("/home/harshil/Harshil-PoCs/models/v16_2/motadata-coder-v16_2-merged")
HF_REPO_ID = "harshilshah25/motadata-coder-Qwen2.5-Coder-14B-Instruct-finetuned-v16.2"
HF_TOKEN = os.getenv("HF_TOKEN", "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")

def verify_model_files():
    """Verify all model files exist"""
    print("Verifying model files...")
    required_files = [
        "config.json",
        "generation_config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "model.safetensors.index.json",
    ]
    
    for f in required_files:
        if not (MODEL_PATH / f).exists():
            print(f"  ✗ Missing: {f}")
            return False
        print(f"  ✓ {f}")
    
    # Check safetensors files
    safetensors = list(MODEL_PATH.glob("model-*.safetensors"))
    print(f"  ✓ Found {len(safetensors)} safetensors files")
    
    return True

def create_model_card():
    """Create README.md for the model"""
    readme = """---
license: apache-2.0
language:
- en
- code
tags:
- motadata
- qwen
- code-generation
- finetuned
---

# Motadata Coder V16.2

Fine-tuned Qwen2.5-Coder-14B-Instruct for Motadata AIOps code generation tasks.

## Model Details

- **Base Model**: Qwen/Qwen2.5-Coder-14B-Instruct
- **Fine-tuning Method**: LoRA (Low-Rank Adaptation)
- **Model Size**: 27.53 GB
- **Max Sequence Length**: 8192 tokens
- **Training Date**: January 7, 2026

## Training Data

- Motadata production codebase (Java)
- Real JIRA tasks and commits
- Code refactoring patterns
- Bug fixes and feature implementations

## Benchmark Results

### Motadata-Bench (10 Real-World Tasks)

| Metric | Value |
|--------|-------|
| API Success Rate | 10/10 (100%) |
| Avg Quality Score | 90.0% |
| Avg File Coverage | 100% (enriched prompts) |
| Avg Latency | 10.94s |
| Total Tokens Generated | 5,436 |

### Task Breakdown

- **Hard Tasks (3)**: Avg 18.3s latency, 896 tokens
- **High Tasks (3)**: Avg 6.6s latency, 330 tokens  
- **Medium Tasks (4)**: Avg 8.7s latency, 440 tokens

## Recommended Settings

```python
# For optimal results:
temperature = 0.3  # Lower for precision
max_tokens = 1500  # Prevent runaway generation
```

## Known Issues

- Base model contains multilingual training data (Qwen2.5)
- Long sequences (>1500 tokens) may include non-ASCII content
- Recommend post-processing to strip non-ASCII characters

## Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "harshilshah25/motadata-coder-Qwen2.5-Coder-14B-Instruct-finetuned-v16.2"
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype="auto", device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_id)
```

## License

Apache 2.0

## Citation

```bibtex
@misc{motadata_coder_v16_2,
  title={Motadata Coder V16.2},
  author={Harshil Shah},
  year={2026},
  publisher={Hugging Face}
}
```
"""
    
    readme_path = MODEL_PATH / "README.md"
    readme_path.write_text(readme)
    print(f"✓ Created README.md")

def backup_to_hf():
    """Upload model to Hugging Face"""
    if not HF_TOKEN:
        print("❌ HF_TOKEN environment variable not set")
        return False
    
    print(f"\n{'='*80}")
    print("UPLOADING TO HUGGING FACE")
    print(f"{'='*80}")
    print(f"Repo: {HF_REPO_ID}")
    print(f"Model Path: {MODEL_PATH}")
    print(f"Model Size: 27.53 GB")
    
    try:
        api = HfApi(token=HF_TOKEN)
        
        # Create repo if it doesn't exist
        print("\n1. Creating/accessing repository...")
        try:
            repo_url = create_repo(
                repo_id=HF_REPO_ID,
                private=True,
                exist_ok=True,
                token=HF_TOKEN
            )
            print(f"   ✓ Repo ready: {repo_url}")
        except Exception as e:
            print(f"   ⚠ Repo access: {e}")
        
        # Upload files
        print("\n2. Uploading model files...")
        api.upload_folder(
            folder_path=str(MODEL_PATH),
            repo_id=HF_REPO_ID,
            repo_type="model"
        )
        
        print(f"\n✅ Model successfully uploaded to {HF_REPO_ID}")
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

def main():
    print("=" * 80)
    print("V16.2 MODEL BACKUP TO HUGGING FACE")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    # Step 1: Verify files
    if not verify_model_files():
        print("\n❌ Model verification failed")
        return 1
    
    # Step 2: Create model card
    print("\nCreating model card...")
    create_model_card()
    
    # Step 3: Backup to HF
    if not backup_to_hf():
        return 1
    
    print("\n" + "=" * 80)
    print("✅ BACKUP COMPLETE")
    print("=" * 80)
    print(f"Model available at: https://huggingface.co/{HF_REPO_ID}")
    
    return 0

if __name__ == "__main__":
    exit(main())

