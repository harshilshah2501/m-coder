#!/usr/bin/env python3
"""
V17 DPO Training Script
=======================

Direct Preference Optimization training on top of V16.1 SFT model.
This teaches the model to prefer correct outputs over hallucinations.

Base Model: V16.1 SFT (Qwen2.5-Coder-14B + LoRA merged)
Dataset: v17_dpo_pairs.jsonl (chosen/rejected pairs)
Output: V17 DPO-enhanced model

Usage:
    python train_v17_dpo.py

Requirements:
    pip install trl>=0.7.0 peft>=0.6.0
"""

import os
import torch
from pathlib import Path
from datetime import datetime
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from trl import DPOTrainer, DPOConfig
from datasets import load_dataset

# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths
BASE_DIR = Path("/home/harshil/Harshil-PoCs")
SFT_MODEL_PATH = BASE_DIR / "models/v16_1_merged"
DPO_DATASET_TRAIN = BASE_DIR / "datasets/v17_dpo_pairs_train.jsonl"
DPO_DATASET_VAL = BASE_DIR / "datasets/v17_dpo_pairs_val.jsonl"
OUTPUT_DIR = BASE_DIR / "models/v17_dpo"
LOGS_DIR = BASE_DIR / "training/logs/v17_dpo"

# DPO Hyperparameters
DPO_BETA = 0.1          # KL penalty coefficient (lower = more aggressive)
LEARNING_RATE = 5e-7    # Very low LR for DPO (prevents catastrophic forgetting)
NUM_EPOCHS = 1          # Usually 1 epoch is enough for DPO
BATCH_SIZE = 1          # Per-device batch size
GRAD_ACCUM = 8          # Effective batch size = 8
MAX_LENGTH = 4096       # Max sequence length
MAX_PROMPT_LENGTH = 1024

# LoRA config for DPO (lighter than SFT)
LORA_R = 8
LORA_ALPHA = 16
LORA_DROPOUT = 0.05
TARGET_MODULES = ["q_proj", "v_proj"]


def setup_logging():
    """Setup logging directory."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"dpo_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    return log_file


def load_model_and_tokenizer():
    """Load the SFT model and tokenizer."""
    print(f"Loading SFT model from: {SFT_MODEL_PATH}")
    
    model = AutoModelForCausalLM.from_pretrained(
        str(SFT_MODEL_PATH),
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    
    tokenizer = AutoTokenizer.from_pretrained(
        str(SFT_MODEL_PATH),
        trust_remote_code=True,
    )
    
    # Ensure pad token is set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        model.config.pad_token_id = model.config.eos_token_id
    
    return model, tokenizer


def add_lora_adapter(model):
    """Add LoRA adapter for DPO training."""
    print("Adding LoRA adapter for DPO...")
    
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        target_modules=TARGET_MODULES,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    return model


def load_preference_dataset():
    """Load the preference dataset (train and val splits)."""
    print(f"Loading preference dataset from: {DPO_DATASET_TRAIN}")
    
    if not DPO_DATASET_TRAIN.exists():
        raise FileNotFoundError(
            f"Train dataset not found: {DPO_DATASET_TRAIN}\n"
            "Run: python datasets/generation/generate_dpo_pairs_v2.py && python datasets/generation/create_splits.py"
        )
    
    train_dataset = load_dataset("json", data_files=str(DPO_DATASET_TRAIN), split="train")
    print(f"Loaded {len(train_dataset)} training pairs")
    
    # Load validation if available
    val_dataset = None
    if DPO_DATASET_VAL.exists():
        val_dataset = load_dataset("json", data_files=str(DPO_DATASET_VAL), split="train")
        print(f"Loaded {len(val_dataset)} validation pairs")
    
    return train_dataset, val_dataset


def main():
    print("=" * 70)
    print("V17 DPO TRAINING")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"SFT Model: {SFT_MODEL_PATH}")
    print(f"Dataset: {DPO_DATASET}")
    print(f"Output: {OUTPUT_DIR}")
    print()
    
    # Setup
    log_file = setup_logging()
    
    # Load components
    model, tokenizer = load_model_and_tokenizer()
    model = add_lora_adapter(model)
    train_dataset, val_dataset = load_preference_dataset()
    
    # DPO Config
    dpo_config = DPOConfig(
        output_dir=str(OUTPUT_DIR),
        beta=DPO_BETA,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=LEARNING_RATE,
        bf16=True,
        logging_dir=str(LOGS_DIR),
        logging_steps=10,
        save_steps=100,
        save_total_limit=3,
        max_length=MAX_LENGTH,
        max_prompt_length=MAX_PROMPT_LENGTH,
        remove_unused_columns=False,
        report_to="tensorboard",
    )
    
    # Create trainer
    print("\nInitializing DPO Trainer...")
    trainer = DPOTrainer(
        model=model,
        ref_model=None,  # Uses implicit reference (frozen copy)
        args=dpo_config,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
    )
    
    # Train
    print("\nStarting DPO training...")
    trainer.train()
    
    # Save
    print(f"\nSaving model to: {OUTPUT_DIR}")
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    
    print("\n" + "=" * 70)
    print("DPO TRAINING COMPLETE")
    print("=" * 70)
    print(f"Model saved to: {OUTPUT_DIR}")
    print(f"Logs saved to: {LOGS_DIR}")


if __name__ == "__main__":
    main()

