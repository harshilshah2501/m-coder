#!/usr/bin/env python3
"""
PHASE 3: V17 Training Configuration
Base Model: Qwen2.5-14B-Instruct
Focus: Enhanced Q&A with LoRA fine-tuning
"""

from dataclasses import dataclass
from datetime import datetime

print("="*80)
print("PHASE 3: V17 TRAINING CONFIGURATION")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

@dataclass
class V17TrainingConfig:
    """V17 Training Configuration"""
    
    # Model Configuration
    model_name: str = "Qwen/Qwen2.5-14B-Instruct"
    model_type: str = "causal_lm"
    dtype: str = "bfloat16"
    
    # LoRA Configuration
    use_lora: bool = True
    lora_rank: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: list = None
    
    # Training Configuration
    output_dir: str = "/home/harshil/Harshil-PoCs/training/artifacts/results/v17_training"
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 8
    per_device_eval_batch_size: int = 16
    gradient_accumulation_steps: int = 2
    learning_rate: float = 2e-4
    warmup_steps: int = 500
    max_grad_norm: float = 1.0
    
    # Data Configuration
    max_seq_length: int = 2048
    train_data_path: str = "/home/harshil/Harshil-PoCs/datasets/v17_training_data.jsonl"
    val_split: float = 0.1
    
    # Optimization
    optim: str = "paged_adamw_32bit"
    lr_scheduler_type: str = "cosine"
    weight_decay: float = 0.01
    
    # Checkpointing
    save_strategy: str = "steps"
    save_steps: int = 500
    eval_strategy: str = "steps"
    eval_steps: int = 500
    save_total_limit: int = 3
    
    # Hardware
    device_map: str = "auto"
    max_memory: dict = None
    
    def __post_init__(self):
        if self.lora_target_modules is None:
            self.lora_target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]
        
        if self.max_memory is None:
            self.max_memory = {"0": "50GB"}

# Create config instance
config = V17TrainingConfig()

print("STEP 1: Model Configuration")
print("-" * 80)
print(f"Base Model: {config.model_name}")
print(f"Model Type: {config.model_type}")
print(f"Data Type: {config.dtype}")
print(f"Device Map: {config.device_map}")

print("\nSTEP 2: LoRA Configuration")
print("-" * 80)
print(f"Use LoRA: {config.use_lora}")
print(f"LoRA Rank: {config.lora_rank}")
print(f"LoRA Alpha: {config.lora_alpha}")
print(f"LoRA Dropout: {config.lora_dropout}")
print(f"Target Modules: {', '.join(config.lora_target_modules)}")

print("\nSTEP 3: Training Hyperparameters")
print("-" * 80)
print(f"Epochs: {config.num_train_epochs}")
print(f"Batch Size: {config.per_device_train_batch_size}")
print(f"Gradient Accumulation: {config.gradient_accumulation_steps}")
print(f"Effective Batch Size: {config.per_device_train_batch_size * config.gradient_accumulation_steps}")
print(f"Learning Rate: {config.learning_rate}")
print(f"Warmup Steps: {config.warmup_steps}")
print(f"Max Grad Norm: {config.max_grad_norm}")

print("\nSTEP 4: Data Configuration")
print("-" * 80)
print(f"Max Sequence Length: {config.max_seq_length}")
print(f"Training Data: {config.train_data_path}")
print(f"Validation Split: {config.val_split * 100}%")

print("\nSTEP 5: Optimization Configuration")
print("-" * 80)
print(f"Optimizer: {config.optim}")
print(f"LR Scheduler: {config.lr_scheduler_type}")
print(f"Weight Decay: {config.weight_decay}")

print("\nSTEP 6: Checkpointing Strategy")
print("-" * 80)
print(f"Save Strategy: {config.save_strategy}")
print(f"Save Steps: {config.save_steps}")
print(f"Eval Strategy: {config.eval_strategy}")
print(f"Eval Steps: {config.eval_steps}")
print(f"Keep Total Limit: {config.save_total_limit}")

print("\nSTEP 7: Hardware Configuration")
print("-" * 80)
print(f"Max Memory: {config.max_memory}")
print(f"Expected VRAM: ~45-50 GB")
print(f"GPU: NVIDIA H100 PCIe (80GB)")

print("\nSTEP 8: Training Estimates")
print("-" * 80)
total_steps = (10000 * config.num_train_epochs) // (config.per_device_train_batch_size * config.gradient_accumulation_steps)
print(f"Total Training Steps: ~{total_steps:,}")
print(f"Estimated Training Time: 24-36 hours")
print(f"Checkpoint Frequency: Every {config.save_steps} steps")

print("\n" + "="*80)
print("PHASE 3 STATUS: CONFIGURATION READY")
print("="*80)
print("\nConfiguration Summary:")
print(f"  ✓ Base Model: Qwen2.5-14B-Instruct")
print(f"  ✓ Fine-tuning: LoRA (rank={config.lora_rank})")
print(f"  ✓ Training Examples: 10,000")
print(f"  ✓ Batch Size: {config.per_device_train_batch_size} (effective: {config.per_device_train_batch_size * config.gradient_accumulation_steps})")
print(f"  ✓ Learning Rate: {config.learning_rate}")
print(f"  ✓ Hardware: H100 80GB")
print("\nReady to start V17 training!")
print("="*80)

