#!/usr/bin/env python3
"""
Chunk CPT dataset to prevent oversized records
Fixes: 5.9MB outlier files causing slow training

Target: 2-6K tokens per chunk (hard max 8K)
"""

import json
from pathlib import Path
from transformers import AutoTokenizer
from tqdm import tqdm

def chunk_dataset(
    input_path: str,
    output_path: str,
    model_name: str = "Qwen/Qwen2.5-Coder-14B",
    target_tokens: int = 4096,
    max_tokens: int = 8192,
    overlap_tokens: int = 256  # 5-10% overlap for context
):
    """Chunk oversized CPT records into bounded chunks"""
    
    print(f"🔧 Loading tokenizer: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    
    print(f"📂 Loading dataset: {input_path}")
    with open(input_path) as f:
        records = [json.loads(line) for line in f]
    
    print(f"✅ Loaded {len(records)} records")
    
    chunked_records = []
    oversized_count = 0
    total_chunks_created = 0
    
    print("🔪 Chunking oversized records...")
    for record in tqdm(records):
        text = record['text']
        
        # Tokenize to check size
        tokens = tokenizer.encode(text, add_special_tokens=False)
        
        if len(tokens) <= max_tokens:
            # Keep as-is
            chunked_records.append(record)
        else:
            # Split into chunks with overlap
            oversized_count += 1
            
            for start_idx in range(0, len(tokens), target_tokens - overlap_tokens):
                chunk_tokens = tokens[start_idx:start_idx + target_tokens]
                
                # Stop if chunk is too small (< 25% of target)
                if len(chunk_tokens) < target_tokens // 4:
                    break
                
                chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=False)
                chunked_records.append({'text': chunk_text})
                total_chunks_created += 1
    
    # Write chunked dataset
    print(f"💾 Writing chunked dataset: {output_path}")
    with open(output_path, 'w') as f:
        for record in chunked_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    # Update metadata
    metadata_path = Path(output_path).parent / "cpt_metadata.json"
    if metadata_path.exists():
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        metadata.update({
            'total_files': len(chunked_records),
            'chunked': True,
            'original_files': len(records),
            'oversized_files_chunked': oversized_count,
            'chunks_created': total_chunks_created,
            'avg_tokens_per_chunk': target_tokens,
            'max_tokens_per_chunk': max_tokens
        })
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 70)
    print("✅ Chunking Complete!")
    print("=" * 70)
    print(f"📊 Original records: {len(records)}")
    print(f"📊 Chunked records: {len(chunked_records)}")
    print(f"📊 Oversized files split: {oversized_count}")
    print(f"📊 New chunks created: {total_chunks_created}")
    print(f"📊 Avg chunk size: {target_tokens} tokens")
    print(f"📊 Hard max: {max_tokens} tokens")
    print("=" * 70)

if __name__ == "__main__":
    chunk_dataset(
        input_path="/home/harshil/Harshil-PoCs/datasets/cpt/cpt_dataset.jsonl",
        output_path="/home/harshil/Harshil-PoCs/datasets/cpt/cpt_dataset_chunked.jsonl",
        target_tokens=4096,
        max_tokens=8192,
        overlap_tokens=256
    )
