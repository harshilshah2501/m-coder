#!/usr/bin/env python3
"""
V16.1 TRAINING - SURGICALLY PRECISE DATASET
Merges V15 (2,598 code edits) + Motadata (1,314 Q&A pairs) = 3,912 examples
Base Model: Qwen/Qwen2.5-Coder-14B-Instruct
Dataset: v16_1_surgical.jsonl (100% valid, 0 duplicates)

Dataset Composition:
- V15 (66.4%): Real Motadata code editing examples
  - code_edits: 799 (30.8%)
  - single_file: 600 (23.1%)
  - diff_generation: 400 (15.4%)
  - multi_file: 300 (11.5%)
  - code_review: 299 (11.5%)
  - file_creation: 150 (5.8%)
  - refactoring: 50 (1.9%)
- Motadata (33.6%): JavaDoc Q&A pairs (1,314 qa_pair)
"""

import json
import torch
import os
from pathlib import Path
from datetime import datetime
from transformers import (
    TrainingArguments,
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model
from datasets import Dataset

# CONFIGURATION
BASE_MODEL_ID = "Qwen/Qwen2.5-Coder-14B-Instruct"
DATASET_DIR = "/home/harshil/Harshil-PoCs/datasets/v16_1_fixed"  # Fixed dataset with SEARCH/REPLACE format
OUTPUT_DIR = "/home/harshil/Harshil-PoCs/models/v16_1_finetuned"
CHECKPOINT_DIR = "/home/harshil/Harshil-PoCs/training/checkpoints/v16_1"

# Training parameters - OPTIMIZED for H100 (2-3 hour target)
# Key changes:
# - Reduced seq length: 8192->4096 (4x faster attention, fits most examples)
# - Batch size 2 with gradient checkpointing ON (memory safe)
# - Reduced epochs: 3->2 (fewer steps needed)
BATCH_SIZE = 2
GRADIENT_ACCUM = 4
LEARNING_RATE = 3e-5
EPOCHS = 2
MAX_SEQ_LENGTH = 4096
WARMUP_RATIO = 0.05

print("="*80)
print("V16.1 TRAINING - SURGICALLY PRECISE DATASET")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"Base Model: {BASE_MODEL_ID}")
print(f"Dataset: {DATASET_DIR}")
print(f"Output: {OUTPUT_DIR}")
print("="*80)

def prepare_data(tokenizer):
    """Prepare dataset from v16_1 splits with proper chat template formatting."""
    
    print("\nSTEP 1: Loading Dataset")
    print("-" * 80)
    
    train_path = Path(DATASET_DIR) / "train.jsonl"
    val_path = Path(DATASET_DIR) / "val.jsonl"
    
    if not train_path.exists():
        raise FileNotFoundError(f"Training data not found at {train_path}")
    if not val_path.exists():
        raise FileNotFoundError(f"Validation data not found at {val_path}")
    
    # Load training data
    train_examples = []
    with open(train_path, 'r') as f:
        for line in f:
            if line.strip():
                train_examples.append(json.loads(line))
    
    # Load validation data
    val_examples = []
    with open(val_path, 'r') as f:
        for line in f:
            if line.strip():
                val_examples.append(json.loads(line))
    
    print(f"✓ Training examples: {len(train_examples):,}")
    print(f"✓ Validation examples: {len(val_examples):,}")
    
    # Format using tokenizer's chat template
    # Note: All data is now in 'messages' format after fix_dataset_v16_1.py
    def format_to_text(ex_list):
        texts = []
        for ex in ex_list:
            # All examples now have 'messages' format (fixed dataset)
            if "messages" not in ex:
                print(f"Warning: Example missing 'messages' key, skipping")
                continue

            msgs = ex['messages']

            try:
                formatted = tokenizer.apply_chat_template(
                    msgs,
                    tokenize=False,
                    add_generation_prompt=False
                )
                texts.append({"text": formatted})
            except Exception as e:
                print(f"Warning: Failed to format example: {e}")
                continue

        return texts
    
    print("\nSTEP 2: Formatting Data")
    print("-" * 80)

    train_texts = format_to_text(train_examples)
    val_texts = format_to_text(val_examples)

    print(f"✓ Formatted training: {len(train_texts):,} examples")
    print(f"✓ Formatted validation: {len(val_texts):,} examples")

    # Create datasets
    train_dataset = Dataset.from_dict({"text": [t["text"] for t in train_texts]})
    val_dataset = Dataset.from_dict({"text": [t["text"] for t in val_texts]})

    # Tokenize
    print("\nSTEP 2.5: Tokenizing Data")
    print("-" * 80)

    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=MAX_SEQ_LENGTH,
            padding="max_length",
            return_tensors=None
        )

    train_dataset = train_dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=["text"],
        desc="Tokenizing training data"
    )

    val_dataset = val_dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=["text"],
        desc="Tokenizing validation data"
    )

    # Rename label column
    train_dataset = train_dataset.rename_columns({"input_ids": "input_ids"})
    val_dataset = val_dataset.rename_columns({"input_ids": "input_ids"})

    print(f"✓ Tokenized training: {len(train_dataset):,} examples")
    print(f"✓ Tokenized validation: {len(val_dataset):,} examples")

    return train_dataset, val_dataset

def main():
    print("\nSTEP 3: Loading Model and Tokenizer")
    print("-" * 80)
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    tokenizer.pad_token = tokenizer.eos_token
    
    # Prepare data
    train_dataset, val_dataset = prepare_data(tokenizer)
    
    print("\nSTEP 4: Loading Base Model")
    print("-" * 80)

    # Load model in bfloat16 (full precision, NO 4-bit quantization)
    # This avoids the "catastrophic corruption" seen with 4-bit QLoRA merge
    print("Loading in bfloat16 (full precision for clean LoRA merge)...")

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )

    model.enable_input_require_grads()  # Required for LoRA training

    # LoRA config
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("✓ Model loaded with LoRA (bfloat16)")
    
    print("\nSTEP 5: Training")
    print("-" * 80)
    
    # Create output directories
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(CHECKPOINT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=CHECKPOINT_DIR,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUM,
        learning_rate=LEARNING_RATE,
        warmup_ratio=WARMUP_RATIO,
        max_grad_norm=1.0,
        weight_decay=0.01,
        logging_steps=10,
        save_steps=100,
        eval_steps=100,
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        eval_strategy="steps",
        save_strategy="steps",
        bf16=True,
        gradient_checkpointing=True,  # Required for 14B model in bf16
        report_to=[],
        overwrite_output_dir=True,
        dataloader_pin_memory=True,
        dataloader_num_workers=4,
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )
    
    # Train
    trainer.train()
    
    print("\nSTEP 6: Saving Model")
    print("-" * 80)
    
    # Save final model
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    
    print(f"✓ Model saved to {OUTPUT_DIR}")
    
    print("\n" + "="*80)
    print("V16.1 TRAINING COMPLETE")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Output: {OUTPUT_DIR}")
    print("="*80)

if __name__ == "__main__":
    main()

