#!/usr/bin/env python3
"""
ITERATION 14 TRAINING - MULTI-FILE FORMAT
Based on v13 training approach with multi-file dataset.
Base Model: Qwen/Qwen2.5-Coder-7B-Instruct (Reset from scratch)
Dataset: v14_multifile_final.jsonl (115 multi-file examples)

Key Improvements over v13:
- Multi-file commits kept together (not split)
- Average 5.5 files per example
- Patch*.java files filtered out
- Proper <thinking> and <code> wrappers
- Cross-file consistency training
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
DATASET_FILE = "v14_multifile_final.jsonl"
OUTPUT_DIR = "./finetuning_output/checkpoint-v14"
FINAL_MODEL_DIR = "./finetuning_output/motadata-coder-v14"


def prepare_data(tokenizer):
    """Prepare dataset from v14 JSONL with proper chat template formatting."""
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

    # Format using tokenizer's chat template (same as v13)
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

    print("Formatting examples with chat template...")
    train_data = format_to_text(examples)

    # For v14, we use all data for training (only 115 examples)
    # No validation split needed for such small dataset
    return Dataset.from_list(train_data)


def main():
    print("=" * 80)
    print("🚀 ITERATION 14 TRAINING - MULTI-FILE FORMAT")
    print("=" * 80)
    print(f"Base Model: {BASE_MODEL_ID}")
    print("Strategy: Multi-file commits kept together")
    print("Dataset: v14_multifile_final.jsonl (115 examples)")
    print("Key Fix: Multi-file generation with cross-file consistency")
    print("=" * 80)

    # Load Tokenizer
    print("\n🔧 Loading Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    # Verify chat template
    if tokenizer.chat_template:
        print(f"✅ Chat template found: {tokenizer.chat_template[:100]}...")
    else:
        print("⚠️ Warning: No chat template found in tokenizer")

    # Prepare data
    print("\n📂 Preparing training data...")
    train_dataset = prepare_data(tokenizer)
    print(f"✅ Train: {len(train_dataset)} examples")

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
            max_length=16384,  # Longer for multi-file examples
            padding=False,
        )

    train_dataset = train_dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=train_dataset.column_names,
        desc="Tokenizing train"
    )
    print("✅ Tokenization complete")

    # Load model with QLoRA (same as v13)
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

    # Configure LoRA
    print("\n🔧 Configuring LoRA...")
    lora_config = LoraConfig(
        r=64,
        lora_alpha=128,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    print("✅ LoRA configured")

    # Training arguments (adapted for small dataset)
    training_args = TrainingArguments(
        per_device_train_batch_size=1,  # Small batch for long sequences
        gradient_accumulation_steps=4,  # Effective batch = 4
        warmup_ratio=0.1,  # More warmup for small dataset
        num_train_epochs=5,  # More epochs since we have fewer examples
        learning_rate=2e-4,
        fp16=False,
        bf16=True,
        logging_steps=5,
        optim="paged_adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        output_dir=OUTPUT_DIR,
        save_strategy="epoch",
        save_total_limit=2,
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
        data_collator=data_collator,
    )
    print("✅ Trainer initialized")

    # Train
    print("\n🚀 Starting training...")
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
    print("   3. Test on multi-file tasks")
    print("   4. Compare with v13 baseline")

if __name__ == '__main__':
    main()

