#!/usr/bin/env python3
"""
ITERATION 10 TRAINING - FULL PRECISION
Based on proven Iter9 approach with 1,148 real production examples
CRITICAL: No 4-bit quantization to avoid merge corruption
"""

import json
import torch
from pathlib import Path
from transformers import TrainingArguments, AutoTokenizer, AutoModelForCausalLM
from trl import SFTTrainer
from datasets import Dataset

def prepare_data():
    """Prepare training/validation split from JSONL."""
    script_dir = Path(__file__).parent
    data_path = script_dir / 'motadata_finetuning_data.jsonl'
    output_dir = script_dir / 'finetuning_output'

    examples = []
    with open(data_path, 'r') as f:
        for line in f:
            examples.append(json.loads(line))

    # 90/10 split
    split_idx = int(len(examples) * 0.9)
    train_examples = examples[:split_idx]
    val_examples = examples[split_idx:]

    # Convert to text format for SFTTrainer
    train_texts = []
    val_texts = []

    for ex in train_examples:
        text = ""
        for msg in ex['messages']:
            text += f"{msg['role']}: {msg['content']}\n"
        train_texts.append({"text": text})

    for ex in val_examples:
        text = ""
        for msg in ex['messages']:
            text += f"{msg['role']}: {msg['content']}\n"
        val_texts.append({"text": text})

    return Dataset.from_list(train_texts), Dataset.from_list(val_texts)

def main():
    print("=" * 80)
    print("🚀 ITERATION 10 TRAINING - FULL PRECISION")
    print("=" * 80)
    print("Base Model: motadata-coder-iter9")
    print("Precision: bfloat16 (NO QUANTIZATION)")
    print("LoRA: r=16, alpha=16, dropout=0")
    print("Dataset: 1,148 real production examples")
    print("=" * 80)

    # Prepare data
    print("\n📂 Preparing training data...")
    train_dataset, eval_dataset = prepare_data()
    print(f"✅ Train: {len(train_dataset)} examples")
    print(f"✅ Val: {len(eval_dataset)} examples")

    # Load model (CRITICAL: Full precision, no quantization)
    print("\n🔧 Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        "/home/harshil/Harshil-PoCs/motadata-coder-iter9",
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    tokenizer = AutoTokenizer.from_pretrained(
        "/home/harshil/Harshil-PoCs/motadata-coder-iter9"
    )

    # Training arguments (Iter9 proven config)
    training_args = TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        num_train_epochs=2,
        learning_rate=2e-4,
        fp16=False,
        bf16=True,
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="./finetuning_output/checkpoint-iter10",
        eval_strategy="epoch",
        save_strategy="epoch",
    )

    # Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        dataset_text_field="text",
        max_seq_length=8192,
        args=training_args,
    )

    # Train
    print("\n🚀 Starting training...")
    trainer.train()

    print("\n✅ Training complete!")
    print(f"📁 Checkpoint: ./finetuning_output/checkpoint-iter10")
    print("\n📝 Next steps:")
    print("  1. Merge LoRA weights: python merge_iter10.py")
    print("  2. Deploy to vLLM")
    print("  3. Run benchmark evaluation")

if __name__ == '__main__':
    main()

