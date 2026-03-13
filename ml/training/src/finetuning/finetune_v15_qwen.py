#!/usr/bin/env python3
"""
Fine-tune Qwen2.5-Coder-7B on V15 dataset using Full Precision bfloat16

⚠️  CRITICAL: Do NOT use 4-bit quantization!
    4-bit → 16-bit conversion during merge corrupts weights.
    H100 has 80GB RAM - use full precision instead.

Configuration:
- Base Model: Qwen/Qwen2.5-Coder-7B-Instruct
- Training Method: LoRA with bfloat16 (FULL PRECISION)
- Batch Size: 16 (effective)
- Learning Rate: 2e-4
- Epochs: 5
- Expected Duration: 4-6 hours
- Memory: ~60GB (well within H100's 80GB limit)
"""

import json
import argparse
from pathlib import Path
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model
from datasets import Dataset
import torch


def load_dataset(file_path: Path):
    """Load dataset from JSONL file."""
    examples = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                example = json.loads(line)
                examples.append(example)
    return examples


def format_to_text(examples, tokenizer):
    """Format examples using tokenizer's chat template."""
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
            print(f"⚠️ Warning: Failed to format example: {e}")
            texts.append({"messages": msgs})
    return texts


def setup_model_and_tokenizer(model_name: str):
    """Setup model with FULL PRECISION bfloat16 (NO 4-bit quantization!)."""
    print(f"\n🔧 Loading model: {model_name}")
    print(f"Using FULL PRECISION bfloat16 (avoiding 4-bit corruption)")

    # Load model in full precision bfloat16
    # ✅ NO 4-bit quantization - H100 has 80GB RAM
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    print(f"✅ Model loaded: {model_name}")
    print(f"✅ Tokenizer loaded")
    print(f"✅ Using bfloat16 precision (no quantization)")

    return model, tokenizer


def setup_lora(model):
    """Setup LoRA configuration."""
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

    # Ensure model is in training mode
    model.train()

    print(f"✅ LoRA configured")

    return model


def main():
    parser = argparse.ArgumentParser(description='Fine-tune Qwen2.5-Coder-7B on V15 dataset')
    parser.add_argument('--train-file', required=True, help='Path to training set JSONL file')
    parser.add_argument('--val-file', required=True, help='Path to validation set JSONL file')
    parser.add_argument('--model', default='Qwen/Qwen2.5-Coder-7B-Instruct', help='Base model name')
    parser.add_argument('--output-dir', default='training/results/v15_finetuned', help='Output directory')
    parser.add_argument('--epochs', type=int, default=5, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=1, help='Per-device batch size')
    parser.add_argument('--grad-accum', type=int, default=8, help='Gradient accumulation steps')
    parser.add_argument('--learning-rate', type=float, default=2e-4, help='Learning rate')

    args = parser.parse_args()

    print("="*80)
    print("🚀 V15 FINE-TUNING - QWEN2.5-CODER-7B (FULL PRECISION bfloat16)")
    print("="*80)

    # Load tokenizer first
    print(f"\n🔧 Loading Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    # Verify chat template
    if tokenizer.chat_template:
        print(f"✅ Chat template found")
    else:
        print("⚠️ Warning: No chat template found in tokenizer")

    # Load datasets
    print(f"\n📂 Loading datasets...")
    train_data = load_dataset(Path(args.train_file))
    val_data = load_dataset(Path(args.val_file))

    print(f"✅ Training examples: {len(train_data)}")
    print(f"✅ Validation examples: {len(val_data)}")

    # Format using chat template
    print(f"\n🔄 Formatting examples with chat template...")
    train_formatted = format_to_text(train_data, tokenizer)
    val_formatted = format_to_text(val_data, tokenizer)

    # Convert to HuggingFace Dataset format
    train_dataset = Dataset.from_list(train_formatted)
    val_dataset = Dataset.from_list(val_formatted)

    # Tokenize datasets
    print(f"\n🔧 Tokenizing dataset...")
    def tokenize_function(examples):
        return tokenizer(
            examples['text'],
            truncation=True,
            max_length=4096,
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
    print(f"✅ Tokenization complete")

    # Setup model and tokenizer
    model, _ = setup_model_and_tokenizer(args.model)

    # Setup LoRA
    model = setup_lora(model)

    # Training arguments (matching V15 config)
    print(f"\n🔧 Setting up training arguments...")
    training_args = TrainingArguments(
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        warmup_ratio=0.05,
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
        fp16=False,
        bf16=True,
        logging_steps=10,
        optim="paged_adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        output_dir=args.output_dir,
        save_strategy="epoch",
        save_total_limit=2,
        eval_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        report_to="none",
        gradient_checkpointing=False,  # Disabled for full precision training
        max_grad_norm=0.3,
    )

    print(f"✅ Training arguments configured")
    print(f"  Epochs: {args.epochs}")
    print(f"  Per-device batch size: {args.batch_size}")
    print(f"  Gradient accumulation: {args.grad_accum}")
    print(f"  Effective batch size: {args.batch_size * args.grad_accum}")
    print(f"  Learning rate: {args.learning_rate}")

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    # Initialize trainer
    print(f"\n🔧 Initializing Trainer...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
    )

    print(f"✅ Trainer initialized")

    # Start training
    print(f"\n{'='*80}")
    print("🚀 STARTING TRAINING...")
    print(f"Expected training time: ~4-6 hours on H100")
    print(f"{'='*80}\n")

    trainer.train()

    # Save final model
    print(f"\n{'='*80}")
    print("✅ TRAINING COMPLETE!")
    print(f"{'='*80}")
    print(f"\n💾 Saving model to: {args.output_dir}")

    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    print(f"✅ Model saved successfully!")
    print(f"\n📊 Next steps:")
    print(f"   1. Merge LoRA adapters with base model")
    print(f"   2. Deploy with vLLM")
    print(f"   3. Run evaluation on test set")


if __name__ == '__main__':
    main()

