#!/usr/bin/env python3
"""
V16 TRAINING - SURGICALLY ENHANCED DATASET
Enhanced V15 with targeted examples to fill capability gaps

Dataset: v15_enhanced_splits (3,020 examples)
Base Model: Qwen/Qwen2.5-Coder-7B-Instruct

Enhancements over V15:
- Multi-file: 11.5% → 15.0% (+154 examples)
- Refactoring: 1.9% → 6.4% (+144 examples)
- Diff generation: 15.4% → 15.0% (+54 examples)
- File creation: 5.8% → 6.4% (+44 examples)
- Code review: 11.5% → 10.7% (+25 examples)
- Total: 2,599 → 3,020 (+421 examples)
"""

import json
import torch
from pathlib import Path
from transformers import (
    TrainingArguments,
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model
from datasets import Dataset

# CONFIGURATION
BASE_MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"
TRAIN_FILE = "datasets/v15_enhanced_splits/train.jsonl"
VAL_FILE = "datasets/v15_enhanced_splits/val.jsonl"
OUTPUT_DIR = "training/results/v16_checkpoints"
FINAL_MODEL_DIR = "training/results/v16_finetuned"


def load_jsonl(filepath):
    """Load JSONL file"""
    examples = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    return examples


def prepare_data(tokenizer, train_file, val_file):
    """Prepare train and val datasets"""
    print("="*80)
    print("LOADING ENHANCED DATASET")
    print("="*80)
    
    # Load data
    print(f"\n📊 Loading training data from {train_file}...")
    train_examples = load_jsonl(train_file)
    print(f"✅ Loaded {len(train_examples)} training examples")
    
    print(f"\n📊 Loading validation data from {val_file}...")
    val_examples = load_jsonl(val_file)
    print(f"✅ Loaded {len(val_examples)} validation examples")
    
    # Show category distribution
    from collections import Counter
    train_cats = Counter(ex.get('metadata', {}).get('category', 'unknown') for ex in train_examples)
    
    print(f"\n📊 Training Category Distribution:")
    for cat, count in sorted(train_cats.items(), key=lambda x: -x[1]):
        pct = count / len(train_examples) * 100
        print(f"   {cat:20s}: {count:4d} ({pct:5.1f}%)")
    
    # Format using chat template
    def format_examples(examples):
        texts = []
        for ex in examples:
            msgs = ex['messages']
            try:
                formatted = tokenizer.apply_chat_template(
                    msgs,
                    tokenize=False,
                    add_generation_prompt=False
                )
                texts.append({"text": formatted})
            except Exception as e:
                print(f"⚠️  Skipping example: {e}")
        return texts
    
    print("\n🔧 Formatting examples...")
    train_texts = format_examples(train_examples)
    val_texts = format_examples(val_examples)
    print(f"✅ Formatted {len(train_texts)} train, {len(val_texts)} val")
    
    # Tokenize
    def tokenize_fn(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=4096,
            padding=False
        )
    
    print("\n🔧 Creating datasets...")
    train_dataset = Dataset.from_list(train_texts).map(
        tokenize_fn,
        batched=True,
        remove_columns=["text"]
    )
    val_dataset = Dataset.from_list(val_texts).map(
        tokenize_fn,
        batched=True,
        remove_columns=["text"]
    )
    
    print(f"✅ Train dataset: {len(train_dataset)} examples")
    print(f"✅ Val dataset: {len(val_dataset)} examples")
    
    return train_dataset, val_dataset


def main():
    print("="*80)
    print("V16 ENHANCED TRAINING")
    print("="*80)
    print()
    
    # Load tokenizer
    print("🔧 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    print("✅ Tokenizer loaded")
    
    # Prepare data
    train_dataset, val_dataset = prepare_data(tokenizer, TRAIN_FILE, VAL_FILE)
    
    # Load model
    print("\n🔧 Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    print("✅ Model loaded")
    
    # LoRA configuration (same as V15)
    print("\n🔧 Configuring LoRA...")
    lora_config = LoraConfig(
        r=16,
        lora_alpha=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.0,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=5,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_steps=100,
        eval_steps=100,
        save_total_limit=3,
        bf16=True,
        optim="paged_adamw_8bit",
        weight_decay=0.01,
        max_grad_norm=0.3,
        eval_strategy="steps",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="none"
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator
    )
    
    # Train
    print("\n" + "="*80)
    print("STARTING TRAINING")
    print("="*80)
    print()
    
    trainer.train()
    
    # Save final model
    print("\n💾 Saving final model...")
    trainer.save_model(FINAL_MODEL_DIR)
    tokenizer.save_pretrained(FINAL_MODEL_DIR)
    print(f"✅ Model saved to {FINAL_MODEL_DIR}")
    
    print("\n" + "="*80)
    print("✅ V16 TRAINING COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()

