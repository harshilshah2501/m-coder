#!/usr/bin/env python3
"""
Stage-08 LoRA SFT training harness.
Single-GPU, constitution-locked. No DeepSpeed/FSDP/QLoRA/TRL/DPO/gradient_checkpointing.
Dataset: SCRIPT_DIR/dataset or ml/training/datasets/sft (Golden Exemplars). Fields: input, output, phase.

Training runs on GPU only. Use a PyTorch build that supports your GPU (e.g. sm_120).
"""
from pathlib import Path
import json

try:
    from ._path_utils import get_canonical_sft_dataset_dir
except ImportError:
    from _path_utils import get_canonical_sft_dataset_dir
import os
import yaml
import torch
# Disable fused SDP/Flash to avoid Blackwell kernel issues; use math SDP only
torch.backends.cuda.enable_flash_sdp(False)
torch.backends.cuda.enable_mem_efficient_sdp(False)
torch.backends.cuda.enable_math_sdp(True)
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
    TrainerCallback,
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
from sklearn.model_selection import train_test_split

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent.parent  # stage08->pipeline->training->ml->repo
MAX_LENGTH = 4096
VALID_PHASES = {"REF", "CONF", "DES", "MIX", "CODE"}
EARLY_STOP_DIVERGENCE = 1.15
LABEL_PAD_ID = -100


def collate_causal_lm_with_labels(features, tokenizer, pad_to_multiple_of=8):
    """Pad input_ids and labels; preserve precomputed labels (input portion = -100)."""
    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    max_len = max(len(f["input_ids"]) for f in features)
    if pad_to_multiple_of:
        max_len = ((max_len + pad_to_multiple_of - 1) // pad_to_multiple_of) * pad_to_multiple_of
    batch_input_ids = []
    batch_labels = []
    for f in features:
        inp = f["input_ids"]
        lab = f["labels"]
        pad_len = max_len - len(inp)
        batch_input_ids.append(inp + [pad_id] * pad_len)
        batch_labels.append(lab + [LABEL_PAD_ID] * pad_len)
    return {
        "input_ids": torch.tensor(batch_input_ids, dtype=torch.long),
        "labels": torch.tensor(batch_labels, dtype=torch.long),
    }


def load_config():
    with open(SCRIPT_DIR / "configs" / "lora_config.yaml") as f:
        cfg = yaml.safe_load(f)
    cfg["model_name_or_path"] = str(SCRIPT_DIR / "base_model")
    return cfg


def discover_dataset_dir():
    local = SCRIPT_DIR / "dataset"
    if local.exists():
        jsonl_files = list(local.glob("*.jsonl"))
        if jsonl_files:
            return local
    canonical = get_canonical_sft_dataset_dir()
    if canonical.exists():
        jsonl_files = list(canonical.glob("*.jsonl"))
        if jsonl_files:
            return canonical
    return SCRIPT_DIR / "dataset"


def load_jsonl_records(dataset_dir, dataset_file=None):
    records = []
    if dataset_file:
        paths = [dataset_dir / dataset_file] if (dataset_dir / dataset_file).exists() else []
    else:
        paths = sorted(dataset_dir.glob("*.jsonl"))
    for path in paths:
        if not path.exists():
            continue
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not all(k in obj for k in ("input", "output", "phase")):
                    continue
                records.append(obj)
    return records


def _base_id_and_phase(rec):
    base_id = rec.get("base_id") or rec.get("sample_id") or ""
    phase = str(rec.get("phase", "")).strip().upper()
    if phase not in VALID_PHASES:
        phase = "MIX"
    return base_id, phase


# Val bases per phase for balanced split (deterministic: first N by sorted base_id).
# Corrected split: val = REF/CONF/DES only; train = remaining REF/CONF/DES + ALL MIX + ALL CODE.
BALANCED_VAL_SPEC = {"REF": 1, "CONF": 2, "DES": 1}


def balanced_base_split(records):
    """Deterministic split: val = 1 REF, 2 CONF, 1 DES base; train = remaining REF/CONF/DES + ALL MIX + ALL CODE. All variants of each base together."""
    base_to_phase = {}
    base_to_indices = {}
    for i, r in enumerate(records):
        bid, phase = _base_id_and_phase(r)
        base_to_phase[bid] = phase
        base_to_indices.setdefault(bid, []).append(i)
    bases_by_phase = {}
    for bid, phase in base_to_phase.items():
        bases_by_phase.setdefault(phase, []).append(bid)
    for phase in bases_by_phase:
        bases_by_phase[phase].sort()
    val_bases = set()
    for phase, count in BALANCED_VAL_SPEC.items():
        bases = bases_by_phase.get(phase, [])
        for b in bases[:count]:
            val_bases.add(b)
    base_ids = list(base_to_indices.keys())
    train_records = [records[i] for b in base_ids for i in base_to_indices[b] if b not in val_bases]
    val_records = [records[i] for b in base_ids for i in base_to_indices[b] if b in val_bases]
    phases_before = [str(r.get("phase", "")).strip().upper() for r in records]
    for i, p in enumerate(phases_before):
        if p not in VALID_PHASES:
            phases_before[i] = "MIX"
    return train_records, val_records, phases_before


def stratified_split_by_base(records, seed=42):
    """Group by base_id; stratified 80/20 split at base level. All variants of a base stay in same split."""
    base_to_phase = {}
    base_to_indices = {}
    for i, r in enumerate(records):
        bid, phase = _base_id_and_phase(r)
        base_to_phase[bid] = phase
        base_to_indices.setdefault(bid, []).append(i)
    base_ids = list(base_to_indices.keys())
    base_phases = [base_to_phase[b] for b in base_ids]
    try:
        train_bases, val_bases = train_test_split(
            base_ids,
            test_size=0.2,
            random_state=seed,
            stratify=base_phases,
        )
    except ValueError:
        train_bases, val_bases = train_test_split(
            base_ids,
            test_size=0.2,
            random_state=seed,
        )
        stratified_fallback = True
    else:
        stratified_fallback = False
    train_set = set(train_bases)
    train_records = [records[i] for b in base_ids for i in base_to_indices[b] if b in train_set]
    val_records = [records[i] for b in base_ids for i in base_to_indices[b] if b not in train_set]
    phases_before = [str(r.get("phase", "")).strip().upper() for r in records]
    for i, p in enumerate(phases_before):
        if p not in VALID_PHASES:
            phases_before[i] = "MIX"
    return train_records, val_records, phases_before, stratified_fallback


def write_split_stats(train_records, val_records, phases_before, stratified_fallback=None, split_header=None):
    train_phases = [str(r.get("phase", "")).strip().upper() for r in train_records]
    val_phases = [str(r.get("phase", "")).strip().upper() for r in val_records]
    from collections import Counter
    before = Counter(phases_before)
    train_c = Counter(train_phases)
    val_c = Counter(val_phases)
    header = split_header or "Stage-stratified 80/20 split at BASE level (seed=42). All variants of same base_id in same split."
    lines = [header]
    if stratified_fallback is not None:
        lines.append("Stratified fallback used (non-stratified): " + str(stratified_fallback))
    lines.append("")
    lines.append("Before split (counts per phase, row-level):")
    for p in VALID_PHASES:
        lines.append(f"  {p}: {before.get(p, 0)}")
    lines.extend([
        "",
        f"Train: {len(train_records)} rows",
        "Train per phase:",
    ])
    for p in VALID_PHASES:
        lines.append(f"  {p}: {train_c.get(p, 0)}")
    lines.extend([
        "",
        f"Val: {len(val_records)} rows",
        "Val per phase:",
    ])
    for p in VALID_PHASES:
        lines.append(f"  {p}: {val_c.get(p, 0)}")
    out = SCRIPT_DIR / "logs" / "split_stats.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        f.write("\n".join(lines))


def tokenize_and_label(examples, tokenizer):
    input_ids_list = []
    labels_list = []
    for inp, out in zip(examples["input"], examples["output"]):
        prompt_str = tokenizer.apply_chat_template(
            [{"role": "user", "content": inp}],
            tokenize=False,
            add_generation_prompt=True,
        )
        full_str = prompt_str + out + (tokenizer.eos_token or "")
        prefix_ids = tokenizer(
            prompt_str,
            truncation=True,
            max_length=MAX_LENGTH,
            return_tensors=None,
        )["input_ids"]
        full_enc = tokenizer(
            full_str,
            truncation=True,
            max_length=MAX_LENGTH,
            return_tensors=None,
        )
        full_ids = full_enc["input_ids"]
        input_len = min(len(prefix_ids), len(full_ids))
        labels = [-100] * input_len + full_ids[input_len:]
        if len(labels) > len(full_ids):
            labels = labels[: len(full_ids)]
        elif len(labels) < len(full_ids):
            labels = labels + [-100] * (len(full_ids) - len(labels))
        input_ids_list.append(full_ids)
        labels_list.append(labels)
    return {"input_ids": input_ids_list, "labels": labels_list}


class EarlyStopCallback(TrainerCallback):
    def __init__(self, log_dir):
        self.log_dir = Path(log_dir)
        self.early_stopped = False

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        if metrics is None or "eval_loss" not in metrics:
            return
        eval_loss = metrics["eval_loss"]
        train_loss_approx = None
        for i in range(len(state.log_history) - 1, -1, -1):
            if "loss" in state.log_history[i]:
                train_loss_approx = state.log_history[i]["loss"]
                break
        if train_loss_approx is None:
            return
        if eval_loss > train_loss_approx * EARLY_STOP_DIVERGENCE:
            control.should_training_stop = True
            self.early_stopped = True
            msg = f"Early stop triggered: eval_loss={eval_loss}, train_loss_approx={train_loss_approx}, step={state.global_step}"
            out = self.log_dir / "early_stop.txt"
            with open(out, "w") as f:
                f.write(msg + "\n")


class TrainEvalLogCallback(TrainerCallback):
    def __init__(self, log_dir):
        self.log_dir = Path(log_dir)
        self.train_log = self.log_dir / "train_log.txt"
        self.eval_log = self.log_dir / "eval_log.txt"

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            with open(self.train_log, "a") as f:
                f.write(json.dumps(logs) + "\n")
                f.flush()

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        if metrics:
            with open(self.eval_log, "a") as f:
                f.write(json.dumps(metrics) + "\n")
                f.flush()


def main():
    # TF32: off by default. Set PHASE08_ENABLE_TF32=1 to turn on.
    enable_tf32 = os.environ.get("PHASE08_ENABLE_TF32", "").strip().lower() in ("1", "true", "yes")
    torch.backends.cuda.matmul.allow_tf32 = enable_tf32
    if not enable_tf32:
        print("TF32 disabled (matmul.allow_tf32=False). Set PHASE08_ENABLE_TF32=1 to enable.")
    config = load_config()
    model_name_or_path = config["model_name_or_path"]

    dataset_dir = discover_dataset_dir()
    dataset_file = config.get("dataset_file")
    records = load_jsonl_records(dataset_dir, dataset_file=dataset_file)
    if not records:
        raise RuntimeError(
            f"No valid JSONL records with input/output/phase in {dataset_dir}. "
            "Use SCRIPT_DIR/dataset or ml/training/datasets/sft."
        )

    if config.get("balanced_val_split"):
        train_records, val_records, phases_before = balanced_base_split(records)
        write_split_stats(
            train_records, val_records, phases_before,
            split_header="Corrected split: val = 1 REF, 2 CONF, 1 DES base; train = remaining REF/CONF/DES + ALL MIX + ALL CODE. All variants of same base_id in same split.",
        )
    else:
        train_records, val_records, phases_before, stratified_fallback = stratified_split_by_base(records)
        write_split_stats(train_records, val_records, phases_before, stratified_fallback)

    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    train_data = Dataset.from_list(train_records)
    val_data = Dataset.from_list(val_records)

    def tokenize_fn(examples):
        return tokenize_and_label(examples, tokenizer)

    train_data = train_data.map(
        tokenize_fn,
        batched=True,
        remove_columns=train_data.column_names,
        desc="Tokenize train",
    )
    val_data = val_data.map(
        tokenize_fn,
        batched=True,
        remove_columns=val_data.column_names,
        desc="Tokenize val",
    )

    def data_collator(features):
        return collate_causal_lm_with_labels(features, tokenizer, pad_to_multiple_of=8)

    device_map = {"": 0}
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    use_bf16 = torch.cuda.is_bf16_supported()
    use_fp16 = not use_bf16

    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        dtype=dtype,
        device_map=device_map,
        trust_remote_code=True,
    )
    peft_config = LoraConfig(
        r=config["lora_rank"],
        lora_alpha=config["lora_alpha"],
        lora_dropout=config["lora_dropout"],
        target_modules=config["target_modules"],
        bias=config["bias"],
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, peft_config)

    eval_steps = config.get("logging_steps", 10)
    output_dir = str(SCRIPT_DIR / "checkpoints")
    log_dir = SCRIPT_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=config["num_train_epochs"],
        per_device_train_batch_size=config["per_device_train_batch_size"],
        per_device_eval_batch_size=config["per_device_eval_batch_size"],
        learning_rate=config["learning_rate"],
        warmup_ratio=config["warmup_ratio"],
        weight_decay=config["weight_decay"],
        max_grad_norm=config["max_grad_norm"],
        lr_scheduler_type=config["lr_scheduler_type"],
        eval_strategy=config["evaluation_strategy"],
        eval_steps=eval_steps,
        save_strategy=config["save_strategy"],
        save_total_limit=2,
        logging_steps=config["logging_steps"],
        load_best_model_at_end=config["load_best_model_at_end"],
        bf16=use_bf16,
        fp16=use_fp16,
        gradient_checkpointing=False,
    )

    callbacks = [TrainEvalLogCallback(log_dir)]
    if not config.get("disable_early_stop"):
        callbacks.append(EarlyStopCallback(log_dir))
    early_stop_cb = EarlyStopCallback(log_dir) if not config.get("disable_early_stop") else None

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_data,
        eval_dataset=val_data,
        data_collator=data_collator,
        callbacks=callbacks,
    )

    trainer.train()

    final_train_loss = None
    final_eval_loss = None
    for i in range(len(trainer.state.log_history) - 1, -1, -1):
        d = trainer.state.log_history[i]
        if "loss" in d and final_train_loss is None:
            final_train_loss = d["loss"]
        if "eval_loss" in d and final_eval_loss is None:
            final_eval_loss = d["eval_loss"]
        if final_train_loss is not None and final_eval_loss is not None:
            break

    peak_mem_gb = torch.cuda.max_memory_allocated(0) / 1e9 if torch.cuda.is_available() else 0.0
    early_stopped = early_stop_cb.early_stopped if early_stop_cb is not None else False
    summary_lines = [
        f"Final train loss: {final_train_loss}",
        f"Final val loss: {final_eval_loss}",
        f"Early stop triggered: {early_stopped}",
        f"Total training steps: {trainer.state.global_step}",
        f"GPU peak memory (GB): {peak_mem_gb:.2f}",
    ]
    with open(log_dir / "training_summary.txt", "w") as f:
        f.write("\n".join(summary_lines))

    print("Training finished.")
    print("\n".join(summary_lines))


if __name__ == "__main__":
    main()
