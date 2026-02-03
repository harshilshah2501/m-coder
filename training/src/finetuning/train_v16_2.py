#!/usr/bin/env python3
"""
V16.2 TRAINING - 100% SURGICALLY CLEAN DATASET
===============================================
Dataset: 3,156 samples (2,808 train + 348 val)
Quality: 100% clean (zero critical issues)
Base Model: Qwen/Qwen2.5-Coder-14B-Instruct

Dataset Composition (v16.2):
- qa_knowledge:     1,178 (37.3%)
- debugging_rca:      959 (30.4%)
- multi_file_gen:     532 (16.9%)
- code_review:        295 (9.3%)
- single_file_gen:    190 (6.0%)

All samples have:
- Non-empty <thinking> tags with reasoning
- Proper SEARCH/REPLACE format (no ```diff)
- No legacy tool_calls format
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
DATASET_DIR = "/home/harshil/Harshil-PoCs/datasets/v16_2"
OUTPUT_DIR = "/home/harshil/Harshil-PoCs/models/v16_2_finetuned"
CHECKPOINT_DIR = "/home/harshil/Harshil-PoCs/training/checkpoints/v16_2"

# Training parameters - Optimized for H100
# v16.2 has 2,808 training samples (vs v16.1's 3,129)
# Effective batch size: 2 * 4 = 8 samples per gradient step
# Steps per epoch: 2,808 / 8 = 351 steps
# Total steps: 351 * 3 = 1,053 steps
# Estimated time: 3-4 hours (10-15s per step + eval overhead)
BATCH_SIZE = 2
GRADIENT_ACCUM = 4
LEARNING_RATE = 2e-5  # Slightly lower for stability
EPOCHS = 3
MAX_SEQ_LENGTH = 4096
WARMUP_RATIO = 0.05

print("="*80)
print("V16.2 TRAINING - 100% SURGICALLY CLEAN DATASET")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"Base Model: {BASE_MODEL_ID}")
print(f"Dataset: {DATASET_DIR}")
print(f"Output: {OUTPUT_DIR}")
print(f"Training: {EPOCHS} epochs, LR={LEARNING_RATE}")
print("="*80)

def load_jsonl(path):
    """Load JSONL file."""
    samples = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))
    return samples

def prepare_data(tokenizer):
    """Prepare dataset from v16_2 splits."""
    
    print("\nSTEP 1: Loading Dataset")
    print("-" * 80)
    
    train_path = Path(DATASET_DIR) / "train.jsonl"
    val_path = Path(DATASET_DIR) / "val.jsonl"
    
    if not train_path.exists():
        raise FileNotFoundError(f"Training data not found at {train_path}")
    if not val_path.exists():
        raise FileNotFoundError(f"Validation data not found at {val_path}")
    
    train_examples = load_jsonl(train_path)
    val_examples = load_jsonl(val_path)
    
    print(f"✓ Training examples: {len(train_examples):,}")
    print(f"✓ Validation examples: {len(val_examples):,}")
    
    # Format using tokenizer's chat template
    def format_to_text(ex_list):
        texts = []
        skipped = 0
        for ex in ex_list:
            if "messages" not in ex:
                skipped += 1
                continue
            try:
                formatted = tokenizer.apply_chat_template(
                    ex['messages'],
                    tokenize=False,
                    add_generation_prompt=False
                )
                texts.append({"text": formatted})
            except Exception as e:
                skipped += 1
                continue
        if skipped > 0:
            print(f"  (skipped {skipped} malformed examples)")
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
    print("\nSTEP 3: Tokenizing Data")
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

    print(f"✓ Tokenized training: {len(train_dataset):,} examples")
    print(f"✓ Tokenized validation: {len(val_dataset):,} examples")

    return train_dataset, val_dataset


def main():
    print("\nSTEP 4: Loading Model and Tokenizer")
    print("-" * 80)

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    tokenizer.pad_token = tokenizer.eos_token

    train_dataset, val_dataset = prepare_data(tokenizer)

    print("\nSTEP 5: Loading Base Model")
    print("-" * 80)
    print("Loading in bfloat16 (full precision for clean LoRA merge)...")

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )

    model.enable_input_require_grads()

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

    print("\nSTEP 6: Training")
    print("-" * 80)

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(CHECKPOINT_DIR).mkdir(parents=True, exist_ok=True)

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
        gradient_checkpointing=True,
        report_to=[],
        overwrite_output_dir=True,
        dataloader_pin_memory=True,
        dataloader_num_workers=4,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )

    trainer.train()

    print("\nSTEP 7: Saving Model")
    print("-" * 80)

    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    print(f"✓ Model saved to {OUTPUT_DIR}")

    print("\n" + "="*80)
    print("V16.2 TRAINING COMPLETE")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Next: Run merge_v16_2.py to create final merged model")
    print("="*80)


if __name__ == "__main__":
    main()

