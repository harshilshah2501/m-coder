#!/usr/bin/env python3
"""
ITERATION 15 TRAINING - BALANCED MULTI-CAPABILITY
Fixes V14 regression by balancing all 7 capabilities.
Base Model: Qwen/Qwen2.5-Coder-7B-Instruct (Reset from scratch)
Dataset: v15_balanced.jsonl (2,599 examples)

Key Improvements over v14:
- All 7 capabilities present and balanced
- Tool use: 15.4% (balanced, not obsessed)
- Direct generation: 30.8% (restored)
- Single-file: 23.1% (restored)
- Multi-file: 11.5% (maintained from V14)
- Code review: 11.5% (NEW)
- File creation: 5.8% (NEW)
- Refactoring: 1.9% (NEW)
- Zero duplicates (removed 21)
- 100% categorized
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
DATASET_FILE = "v15_balanced.jsonl"
OUTPUT_DIR = "./finetuning_output/checkpoint-v15"
FINAL_MODEL_DIR = "./finetuning_output/motadata-coder-v15"


def prepare_data(tokenizer):
    """Prepare dataset from v15 JSONL with proper chat template formatting."""
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

    # Show category distribution
    from collections import Counter
    categories = [ex.get('metadata', {}).get('category', 'unknown') for ex in examples]
    cat_counts = Counter(categories)
    print(f"\n📊 Category Distribution:")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        pct = count / len(examples) * 100
        print(f"   {cat:20s}: {count:4d} ({pct:5.1f}%)")

    # Format using tokenizer's chat template
    def format_to_text(ex_list):
        texts = []
        for ex in ex_list:
            msgs = ex['messages']
            try:
                formatted = tokenizer.apply_chat_template(
                    msgs,
                    tokenize=False,
                    add_generation_prompt=False
                )
                texts.append({"text": formatted})
            except Exception as e:
                print(f"⚠️ Warning: Failed to format example: {e}")
                texts.append({"messages": msgs})
        return texts

    print("\nFormatting examples with chat template...")
    train_data = format_to_text(examples)

    # Split 95% train, 5% validation
    split_idx = int(len(train_data) * 0.95)
    train_split = train_data[:split_idx]
    val_split = train_data[split_idx:]

    return Dataset.from_list(train_split), Dataset.from_list(val_split)


def main():
    print("=" * 80)
    print("🚀 ITERATION 15 TRAINING - BALANCED MULTI-CAPABILITY")
    print("=" * 80)
    print(f"Base Model: {BASE_MODEL_ID}")
    print("Strategy: Balance all 7 capabilities to fix V14 regression")
    print("Dataset: v15_balanced.jsonl (2,599 examples)")
    print("Key Fix: Restore tool use, single-file, direct gen + maintain multi-file")
    print("=" * 80)

    # Load Tokenizer
    print("\n🔧 Loading Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    # Verify chat template
    if tokenizer.chat_template:
        print(f"✅ Chat template found")
    else:
        print("⚠️ Warning: No chat template found in tokenizer")

    # Prepare data
    print("\n📂 Preparing training data...")
    train_dataset, val_dataset = prepare_data(tokenizer)
    print(f"✅ Train: {len(train_dataset)} examples")
    print(f"✅ Validation: {len(val_dataset)} examples")

    # Show sample
    print("\n📝 Sample formatted text (first 500 chars):")
    print("-" * 80)
    print(train_dataset[0]['text'][:500])
    print("-" * 80)

    # Tokenize dataset
    print("\n🔧 Tokenizing dataset...")
    def tokenize_function(examples):
        return tokenizer(
            examples['text'],
            truncation=True,
            max_length=4096,  # Reduced from 8192 to avoid OOM during evaluation
            padding=False,
        )

    train_dataset = train_dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=train_dataset.column_names,
        desc="Tokenizing train"
    )
    
    val_dataset = val_dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=val_dataset.column_names,
        desc="Tokenizing validation"
    )
    print("✅ Tokenization complete")

    # Load model with QLoRA
    print("\n🔧 Loading Base Model (4-bit QLoRA)...")
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

    # Prepare for k-bit training
    model = prepare_model_for_kbit_training(model)
    model.gradient_checkpointing_enable()

    # Configure LoRA (optimized for balanced dataset)
    print("\n🔧 Configuring LoRA...")
    lora_config = LoraConfig(
        r=16,  # Reduced from V14's 64 - better generalization
        lora_alpha=16,  # Match r for stability
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.0,  # No dropout for stability
        bias="none",
        task_type="CAUSAL_LM"
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    print("✅ LoRA configured")

    # Training arguments (optimized for 2,599 examples)
    training_args = TrainingArguments(
        per_device_train_batch_size=1,  # Conservative for H100 memory
        per_device_eval_batch_size=1,  # CRITICAL: Same as train to avoid OOM during eval
        gradient_accumulation_steps=8,  # Effective batch = 8
        warmup_ratio=0.05,  # Less warmup for larger dataset
        num_train_epochs=5,  # 5 epochs for good coverage
        learning_rate=2e-4,
        fp16=False,
        bf16=True,
        logging_steps=10,
        optim="paged_adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        output_dir=OUTPUT_DIR,
        save_strategy="epoch",
        save_total_limit=2,
        eval_strategy="epoch",  # Evaluate each epoch with reduced max_length
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        report_to="none",
        gradient_checkpointing=True,
        max_grad_norm=0.3,
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    # Trainer
    print("\n🔧 Initializing Trainer...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
    )
    print("✅ Trainer initialized")

    # Train
    print("\n🚀 Starting training...")
    print("=" * 80)
    print("Expected training time: ~4-6 hours on A100")
    print("Total steps: ~325 (2,469 examples / 16 effective batch * 5 epochs)")
    print("=" * 80)

    trainer.train()

    print("\n✅ Training complete!")
    print(f"📁 Checkpoint: {OUTPUT_DIR}")

    # Save final model
    print(f"💾 Saving final model to {FINAL_MODEL_DIR}...")
    trainer.save_model(FINAL_MODEL_DIR)

    print("\n✅ All done!")
    print(f"📁 Final model: {FINAL_MODEL_DIR}")
    print("\n📊 Next steps:")
    print("   1. Merge LoRA adapters with base model")
    print("   2. Deploy with vLLM")
    print("   3. Test on all 7 capabilities:")
    print("      - Tool use (balanced)")
    print("      - Direct generation")
    print("      - Single-file edits")
    print("      - Multi-file commits")
    print("      - Code review")
    print("      - File creation")
    print("      - Refactoring")
    print("   4. Compare with V14 baseline")
    print("   5. Verify no regression on multi-file")

if __name__ == '__main__':
    main()

