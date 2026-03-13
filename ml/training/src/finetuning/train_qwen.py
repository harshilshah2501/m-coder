from unsloth import FastLanguageModel
import torch
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset
import os

os.environ["TRL_EXPERIMENTAL_SILENCE"] = "1"

# --- CONFIG ---
OUTPUT_DIR = "training_outputs/h100_run"
TRAIN_PATH = "/home/harshil/Harshil-PoCs/Finetuning/full_training_train.jsonl"
EVAL_PATH  = "/home/harshil/Harshil-PoCs/Finetuning/full_training_test.jsonl"

max_seq_length = 16384
dtype = torch.bfloat16
load_in_4bit = False

print("=" * 50)
print("🚀 Launching H100 Native BFloat16 Training")
print(f" Context Window: {max_seq_length}")
print(f" Precision: {dtype}")
print("=" * 50)

# 1. Load Base Model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name      = "Qwen/Qwen2.5-Coder-7B-Instruct",
    max_seq_length  = max_seq_length,
    dtype           = dtype,
    load_in_4bit    = load_in_4bit,
)

# 2. Add LoRA
# Even without 4bit, LoRA is efficient and sufficient for style transfer
model = FastLanguageModel.get_peft_model(
    model,
    r                         = 16,
    target_modules            = ["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    lora_alpha                = 16,
    lora_dropout              = 0,
    bias                      = "none",
    use_gradient_checkpointing = True,
    random_state              = 3407,
)

# 3. Load Datasets
train_dataset = load_dataset("json", data_files=TRAIN_PATH, split="train")
eval_dataset  = load_dataset("json", data_files=EVAL_PATH,  split="train")

def formatting_prompts_func(examples):
    convos = examples["messages"]
    texts = [
        tokenizer.apply_chat_template(
            c,
            tokenize=False,
            add_generation_prompt=False,
        )
        for c in convos
    ]
    return {"text": texts}

# Map in single process to be safe
train_dataset = train_dataset.map(formatting_prompts_func, batched=True, num_proc=1)
eval_dataset  = eval_dataset.map(formatting_prompts_func,  batched=True, num_proc=1)

# 4. Train
trainer = SFTTrainer(
    model              = model,
    tokenizer          = tokenizer,
    train_dataset      = train_dataset,
    eval_dataset       = eval_dataset,
    dataset_text_field = "text",
    max_seq_length     = max_seq_length,
    dataset_num_proc   = 1,
    packing            = False,
    args = TrainingArguments(
        per_device_train_batch_size   = 8,
        gradient_accumulation_steps   = 2,     # Effective batch size = 16
        num_train_epochs              = 2,
        learning_rate                 = 2e-5,
        warmup_ratio                  = 0.03,
        fp16                          = False,
        bf16                          = True,
        logging_steps                 = 10,
        optim                         = "adamw_torch_fused",
        weight_decay                  = 0.01,
        lr_scheduler_type             = "cosine",
        output_dir                    = OUTPUT_DIR,
        report_to                     = "none",
        save_strategy                 = "epoch",
        save_total_limit              = 2,
        eval_strategy                 = "steps",
        eval_steps                    = 200,   # eval every ~200 optimizer steps
    ),
)

trainer.train()

# 5. Save
print(f"💾 Saving to {OUTPUT_DIR}/lora_model...")
model.save_pretrained(f"{OUTPUT_DIR}/lora_model")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/lora_model")
print("✅ Done.")
