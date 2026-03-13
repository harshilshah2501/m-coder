#!/usr/bin/env python3
"""
ITERATION 12 TRAINING - FRESH START
Based on 'Quality First' Strategy.
Base Model: Qwen/Qwen2.5-Coder-7B-Instruct (Reset from scratch)
Dataset: v12_combined.jsonl (Verified Real Data: Git + JIRA + Tools)
"""

import json
import torch
import os
from pathlib import Path
from transformers import (
    TrainingArguments,
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset

# CONFIGURATION
BASE_MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct" 
# NOTE: If you have a local copy of base model, replace above string with path.
DATASET_FILE = "v12_combined.jsonl"
OUTPUT_DIR = "./finetuning_output/checkpoint-v12"

def prepare_data(tokenizer):
    """Prepare training/validation split from v12 JSONL with proper chat template formatting."""
    script_dir = Path(__file__).parent
    data_path = script_dir / DATASET_FILE

    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    print(f"Loading data from {data_path}...")
    examples = []
    with open(data_path, 'r') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))

    print(f"✅ Loaded {len(examples)} examples")

    # Shuffle
    import random
    random.seed(42)
    random.shuffle(examples)

    # 95/5 split (since we have 2.5k examples, 5% is ~125 validation)
    split_idx = int(len(examples) * 0.95)
    train_examples = examples[:split_idx]
    val_examples = examples[split_idx:]

    # Format using tokenizer's chat template
    # Qwen2.5 has a built-in chat template that properly handles special tokens
    def format_to_text(ex_list):
        texts = []
        for ex in ex_list:
            msgs = ex['messages']
            # Apply chat template to get properly formatted text with special tokens
            # add_generation_prompt=False because we have the assistant response already
            try:
                formatted = tokenizer.apply_chat_template(
                    msgs,
                    tokenize=False,
                    add_generation_prompt=False
                )
                texts.append({"text": formatted})
            except Exception as e:
                print(f"⚠️ Warning: Failed to format example: {e}")
                # Fallback: keep messages format
                texts.append({"messages": msgs})
        return texts

    print("Formatting examples with chat template...")
    train_data = format_to_text(train_examples)
    val_data = format_to_text(val_examples)

    return Dataset.from_list(train_data), Dataset.from_list(val_data)

def main():
    print("=" * 80)
    print("🚀 ITERATION 12 TRAINING - FRESH START")
    print("=" * 80)
    print(f"Base Model: {BASE_MODEL_ID}")
    print("Strategy: Clean Rebuild (No legacy weights)")
    print("Dataset: v12_combined.jsonl")
    print("=" * 80)

    # Load Tokenizer
    print("\n🔧 Loading Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token # Qwen config

    # Verify chat template exists
    if tokenizer.chat_template:
        print(f"✅ Chat template found: {tokenizer.chat_template[:100]}...")
    else:
        print("⚠️ Warning: No chat template found in tokenizer")

    # Prepare data
    print("\n📂 Preparing training data...")
    train_dataset, eval_dataset = prepare_data(tokenizer)
    print(f"✅ Train: {len(train_dataset)} examples")
    print(f"✅ Val: {len(eval_dataset)} examples")

    # Show sample formatted text
    print("\n📝 Sample formatted text (first 500 chars):")
    print("-" * 80)
    print(train_dataset[0]['text'][:500])
    print("-" * 80)

    # Tokenize datasets
    print("\n🔧 Tokenizing datasets...")
    def tokenize_function(examples):
        return tokenizer(
            examples['text'],
            truncation=True,
            max_length=8192,
            padding=False,  # Will be done by data collator
        )

    train_dataset = train_dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=train_dataset.column_names,
        desc="Tokenizing train"
    )
    eval_dataset = eval_dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=eval_dataset.column_names,
        desc="Tokenizing eval"
    )
    print("✅ Tokenization complete")

    # Load model with QLoRA (4-bit quantization)
    print("\n🔧 Loading Base Model (4-bit QLoRA)...")

    # QLoRA quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    print("✅ Model loaded in 4-bit")

    # Prepare model for k-bit training
    model = prepare_model_for_kbit_training(model)

    # Enable gradient checkpointing to save memory
    model.gradient_checkpointing_enable()

    # Configure LoRA
    print("\n🔧 Configuring LoRA...")
    lora_config = LoraConfig(
        r=64,  # LoRA rank - higher = more capacity but more memory
        lora_alpha=128,  # LoRA scaling factor
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    print("✅ LoRA configured")

    # Training arguments
    training_args = TrainingArguments(
        per_device_train_batch_size=2,  # Max that fits in memory with QLoRA
        per_device_eval_batch_size=1,   # Keep eval small to avoid OOM
        gradient_accumulation_steps=2,  # Effective batch size = 4 (faster than grad_accum=4)
        warmup_ratio=0.03,
        num_train_epochs=3, # Fresh start needs decent epochs
        learning_rate=2e-4, # Higher LR for LoRA
        fp16=False,
        bf16=True,
        logging_steps=10,
        optim="paged_adamw_8bit",  # 8-bit optimizer for QLoRA
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        output_dir=OUTPUT_DIR,
        eval_strategy="steps",
        eval_steps=200,  # Less frequent eval to save time
        save_strategy="steps",
        save_steps=200,
        save_total_limit=2,
        report_to="none", # disable wandb for local run
        gradient_checkpointing=True,
        max_grad_norm=0.3,
    )

    # Data collator for causal LM
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # Causal LM, not masked LM
    )

    # Trainer
    print("\n🔧 Initializing Trainer...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )
    print("✅ Trainer initialized")

    # Train
    print("\n🚀 Starting training...")
    trainer.train()

    print("\n✅ Training complete!")
    print(f"📁 Checkpoint: {OUTPUT_DIR}")
    
    # Save Final
    final_path = "./finetuning_output/motadata-coder-v12"
    print(f"💾 Saving final model to {final_path}...")
    trainer.save_model(final_path)

if __name__ == '__main__':
    main()
