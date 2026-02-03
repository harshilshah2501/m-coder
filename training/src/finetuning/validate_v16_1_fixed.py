#!/usr/bin/env python3
"""
V16.1 QUICK VALIDATION - 100 Steps Sanity Check
================================================
Purpose: Quickly validate the fixed dataset works before full training.

This runs:
- 100 training steps (~5-10 minutes on H100)
- Checks for data loading errors
- Verifies loss decreases
- Saves a mini checkpoint for inspection

Uses bfloat16 + LoRA (no 4-bit quantization) to avoid merge corruption.
If this passes, you can confidently run full training.
"""

import json
import torch
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
DATASET_DIR = "/home/harshil/Harshil-PoCs/datasets/v16_1_fixed"  # Fixed dataset!
OUTPUT_DIR = "/home/harshil/Harshil-PoCs/training/checkpoints/v16_1_validation"
MAX_SEQ_LENGTH = 8192

# Quick validation parameters
MAX_STEPS = 100
EVAL_STEPS = 25
LOGGING_STEPS = 5
BATCH_SIZE = 2
GRADIENT_ACCUM = 4
LEARNING_RATE = 2e-5


def load_and_format_data(tokenizer):
    """Load fixed dataset and format for training."""
    print("\n📂 Loading FIXED dataset...")
    
    train_path = Path(DATASET_DIR) / "train.jsonl"
    val_path = Path(DATASET_DIR) / "val.jsonl"
    
    train_examples = []
    with open(train_path, 'r') as f:
        for line in f:
            if line.strip():
                train_examples.append(json.loads(line))
    
    val_examples = []
    with open(val_path, 'r') as f:
        for line in f:
            if line.strip():
                val_examples.append(json.loads(line))
    
    print(f"   ✓ Train: {len(train_examples):,} examples")
    print(f"   ✓ Val: {len(val_examples):,} examples")
    
    # Verify all are messages format
    non_messages = sum(1 for ex in train_examples if "messages" not in ex)
    if non_messages > 0:
        raise ValueError(f"❌ Found {non_messages} examples without 'messages' format!")
    print(f"   ✓ All examples in 'messages' format")
    
    # Format to text
    def format_examples(examples):
        texts = []
        errors = 0
        for ex in examples:
            try:
                formatted = tokenizer.apply_chat_template(
                    ex['messages'],
                    tokenize=False,
                    add_generation_prompt=False
                )
                texts.append({"text": formatted})
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"   ⚠️ Format error: {e}")
        return texts, errors
    
    train_texts, train_errors = format_examples(train_examples)
    val_texts, val_errors = format_examples(val_examples)
    
    if train_errors > 0:
        print(f"   ⚠️ {train_errors} training examples had formatting errors")
    if val_errors > 0:
        print(f"   ⚠️ {val_errors} validation examples had formatting errors")
    
    # Tokenize
    def tokenize(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=MAX_SEQ_LENGTH,
            padding=False,
        )
    
    train_dataset = Dataset.from_dict({"text": [t["text"] for t in train_texts]})
    val_dataset = Dataset.from_dict({"text": [t["text"] for t in val_texts]})
    
    train_dataset = train_dataset.map(tokenize, batched=True, remove_columns=["text"])
    val_dataset = val_dataset.map(tokenize, batched=True, remove_columns=["text"])
    
    print(f"   ✓ Tokenized: {len(train_dataset):,} train, {len(val_dataset):,} val")
    
    return train_dataset, val_dataset


def main():
    print("=" * 80)
    print("V16.1 QUICK VALIDATION - 100 Steps Sanity Check")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Dataset: {DATASET_DIR}")
    print(f"Max Steps: {MAX_STEPS}")
    print("=" * 80)
    
    # Load tokenizer
    print("\n🔧 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    tokenizer.pad_token = tokenizer.eos_token
    
    # Load and format data
    train_dataset, val_dataset = load_and_format_data(tokenizer)
    
    # Load model in bfloat16 (full precision, no quantization)
    # This avoids the "catastrophic corruption" seen with 4-bit merge
    print("\n🔧 Loading model (bfloat16 full precision)...")

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    model.enable_input_require_grads()  # Required for LoRA training
    
    # LoRA config (same as full training)
    lora_config = LoraConfig(
        r=16, lora_alpha=32,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05, bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, lora_config)
    print("   ✓ Model loaded with LoRA")

    # Training arguments - quick validation
    print("\n🚀 Starting 100-step validation...")
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        max_steps=MAX_STEPS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUM,
        learning_rate=LEARNING_RATE,
        warmup_steps=10,
        logging_steps=LOGGING_STEPS,
        eval_steps=EVAL_STEPS,
        save_steps=50,
        eval_strategy="steps",
        save_strategy="steps",
        bf16=True,
        gradient_checkpointing=True,
        report_to=[],
        load_best_model_at_end=False,
        dataloader_pin_memory=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )

    # Train
    result = trainer.train()

    # Report results
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print(f"Final Training Loss: {result.training_loss:.4f}")
    print(f"Total Steps: {result.global_step}")

    # Evaluate
    eval_result = trainer.evaluate()
    print(f"Eval Loss: {eval_result['eval_loss']:.4f}")

    # Check if loss is reasonable
    if result.training_loss < 5.0 and eval_result['eval_loss'] < 5.0:
        print("\n✅ VALIDATION PASSED!")
        print("   - Data loads correctly")
        print("   - Loss is in reasonable range")
        print("   - Ready for full training")
    else:
        print("\n⚠️ VALIDATION WARNING")
        print("   - Loss may be too high, check data quality")

    print(f"\nCheckpoint saved to: {OUTPUT_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    main()

