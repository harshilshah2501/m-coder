#!/usr/bin/env python3
"""
QUICK TEST RUN - Train on 50 examples to verify setup
"""

import json
import torch
import os
from pathlib import Path
from transformers import TrainingArguments, AutoTokenizer, AutoModelForCausalLM
from trl import SFTTrainer
from datasets import Dataset

BASE_MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"
DATASET_FILE = "v12_combined.jsonl"
OUTPUT_DIR = "./test_output"
NUM_EXAMPLES = 50

def prepare_data(tokenizer):
    """Load and format 50 examples for testing."""
    script_dir = Path(__file__).parent
    data_path = script_dir / DATASET_FILE
    
    print(f"Loading {NUM_EXAMPLES} examples from {data_path}...")
    examples = []
    with open(data_path, 'r') as f:
        for i, line in enumerate(f):
            if i >= NUM_EXAMPLES:
                break
            if line.strip():
                examples.append(json.loads(line))

    print(f"✅ Loaded {len(examples)} examples")

    # Format using tokenizer's chat template
    texts = []
    for ex in examples:
        msgs = ex['messages']
        formatted = tokenizer.apply_chat_template(
            msgs, 
            tokenize=False, 
            add_generation_prompt=False
        )
        texts.append({"text": formatted})

    # Use 90% for train, 10% for val
    split_idx = int(len(texts) * 0.9)
    return Dataset.from_list(texts[:split_idx]), Dataset.from_list(texts[split_idx:])

def main():
    print("=" * 80)
    print("🧪 V12 TEST RUN - 50 Examples")
    print("=" * 80)

    # Load Tokenizer
    print("\n🔧 Loading Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    # Prepare data
    print("\n📂 Preparing data...")
    train_dataset, eval_dataset = prepare_data(tokenizer)
    print(f"✅ Train: {len(train_dataset)} | Val: {len(eval_dataset)}")

    # Load model
    print("\n🔧 Loading model...")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_ID,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
            attn_implementation="flash_attention_2"
        )
        print("✅ Using FlashAttention2")
    except:
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_ID,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
        print("✅ Using default attention")

    # Training arguments - minimal for testing
    training_args = TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=1,
        num_train_epochs=1,
        learning_rate=2e-5,
        bf16=True,
        logging_steps=5,
        output_dir=OUTPUT_DIR,
        eval_strategy="steps",
        eval_steps=10,
        save_strategy="steps",
        save_steps=20,
        save_total_limit=1,
        report_to="none"
    )

    # Trainer
    print("\n🔧 Initializing trainer...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        dataset_text_field="text",
        max_seq_length=8192,
        args=training_args,
    )

    # Train
    print("\n🚀 Starting test training...")
    trainer.train()

    print("\n✅ TEST COMPLETE!")
    print(f"If this worked, you can run the full training with train_v12.py")

if __name__ == '__main__':
    main()

