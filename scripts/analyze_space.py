import os
from pathlib import Path

# Relative to RAG-Datastore (cwd)
ROOT = Path("..").resolve()

DIRS_TO_CHECK = [
    "Finetuning",
    "Dataset-Generation",
    "Iter10-Training",
    "Iter11-Training",
    "motadata-coder-iter6",
    "motadata-coder-iter10",
    "motadata-coder-iter11",
    "model-backups",
    "logs",
    "RAG-Datastore/training-artifacts",
    "RAG-Datastore/evaluation/finetuning/finetuning_output",
    "RAG-Datastore/unsloth_compiled_cache"
]

print(f"{'DIRECTORY':<50} | {'SIZE (MB)':<10} | {'SIZE (GB)':<10}")
print("-" * 75)

for d in DIRS_TO_CHECK:
    path = ROOT / d
    if not path.exists():
        continue
    
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
    except PermissionError:
        print(f"{d:<50} | PERMISSION DENIED")
        continue
        
    size_mb = total_size / (1024 * 1024)
    size_gb = size_mb / 1024
    
    print(f"{d:<50} | {size_mb:,.0f} MB{'':<3} | {size_gb:.2f} GB")
