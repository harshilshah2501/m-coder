#!/usr/bin/env python3
"""
Stage-08D — Balanced Constitutional Retrain
Clean retrain using strengthened Layer-II base exemplars (BASE-001 through BASE-025).
Deterministic base-level split ensuring validation contains at least: 1 REF, 2 CONF, 1 DES, 1 MIX, 1 CODE.
"""
from pathlib import Path
import argparse
import json
import os
import yaml
import hashlib
import datetime
from collections import Counter, defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
MAX_LENGTH = 4096
VALID_PHASES = {"REF", "CONF", "DES", "MIX", "CODE"}
LABEL_PAD_ID = -100

# Stage-08D: Validation must contain at least 1 REF, 2 CONF, 1 DES, 1 MIX, 1 CODE
BALANCED_VAL_SPEC = {"REF": 1, "CONF": 2, "DES": 1, "MIX": 1, "CODE": 1}

def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_now_isoz():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _validate_freeze_certificate(dataset_path):
    cert_path = SCRIPT_DIR.parent / "FREEZE_CERTIFICATE_v1.json"

    if not cert_path.exists():
        raise SystemExit(f"FATAL: Freeze certificate not found: {cert_path}")

    with open(cert_path) as f:
        cert = json.load(f)

    expected_dataset = cert.get("frozen_dataset_path")
    expected_sha = cert.get("dataset_sha256")

    if not expected_dataset or not expected_sha:
        raise SystemExit("FATAL: Freeze certificate missing required fields")

    # Validate path
    if not str(dataset_path).endswith(expected_dataset):
        raise SystemExit(
            f"\nFATAL: Dataset path mismatch.\n"
            f"Expected: {expected_dataset}\n"
            f"Found: {dataset_path}\n"
        )

    # Validate SHA
    actual_sha = _sha256_file(dataset_path)
    if actual_sha != expected_sha:
        raise SystemExit(
            f"\nFATAL: Dataset SHA mismatch.\n"
            f"Expected: {expected_sha}\n"
            f"Actual:   {actual_sha}\n"
        )

    print("[FREEZE VERIFIED] Dataset matches freeze certificate.")


def _detect_schema(obj):
    if (
        isinstance(obj.get("instruction"), str)
        and isinstance(obj.get("response"), dict)
        and isinstance(obj.get("phase"), str)
    ):
        r = obj["response"]
        if all(k in r for k in ("posture", "allow", "block", "validation")):
            return "STAGE7"

    if (
        isinstance(obj.get("input"), str)
        and isinstance(obj.get("output"), str)
        and isinstance(obj.get("phase"), str)
    ):
        return "LEGACY"

    return None


def _render_stage7_response(resp):
    posture = resp.get("posture", "").strip()
    allow = resp.get("allow", "").strip()
    block = resp.get("block", "").strip()
    validation = resp.get("validation", "").strip()

    for field_name, value in {
        "posture": posture,
        "allow": allow,
        "block": block,
        "validation": validation,
    }.items():
        if not value:
            raise ValueError(f"Empty response field: {field_name}")

    return (
        f"POSTURE: {posture}\n"
        f"ALLOW:\n{allow}\n"
        f"BLOCK:\n{block}\n"
        f"VALIDATION:\n{validation}\n"
    )

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
    canonical = SCRIPT_DIR.parent / "datasets" / "sft"
    if canonical.exists():
        jsonl_files = list(canonical.glob("*.jsonl"))
        if jsonl_files:
            return canonical
    return SCRIPT_DIR / "dataset"


def _base_id_and_phase(rec):
    base_id = rec.get("base_id") or rec.get("sample_id") or ""
    phase = str(rec.get("phase", "")).strip().upper()
    if phase not in VALID_PHASES:
        raise SystemExit(
            f"FATAL: Invalid phase '{phase}' for base_id '{base_id}'"
        )
    return base_id, phase


def load_training_dataset(dataset_path):
    if not dataset_path.exists():
        raise SystemExit(f"FATAL: Dataset file not found: {dataset_path}")

    records = []
    schema_type = None
    json_error = None

    with open(dataset_path) as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                json_error = (lineno, str(e))
                break

            detected = _detect_schema(obj)

            if detected is None:
                preview = line[:500]
                raise SystemExit(
                    f"\nFATAL: Unknown schema at line {lineno}\n"
                    f"Keys: {list(obj.keys())}\n"
                    f"Example: {preview}\n"
                )

            if schema_type is None:
                schema_type = detected
            elif schema_type != detected:
                raise SystemExit(
                    f"\nFATAL: Mixed schema detected at line {lineno}\n"
                    f"Expected: {schema_type}, Found: {detected}\n"
                )

            phase = str(obj.get("phase", "")).strip().upper()
            if phase not in VALID_PHASES:
                raise SystemExit(
                    f"\nFATAL: Invalid phase at line {lineno}: '{phase}'\n"
                )

            if detected == "STAGE7":
                input_text = obj["instruction"].strip()
                output_text = _render_stage7_response(obj["response"])
            else:
                input_text = obj["input"].strip()
                output_text = obj["output"].strip()
                if not input_text or not output_text:
                    raise SystemExit(
                        f"\nFATAL: Empty input/output at line {lineno}\n"
                    )

            records.append({
                "input": input_text,
                "output": output_text,
                "phase": phase,
                "base_id": obj.get("base_id") or obj.get("sample_id")
            })

    if json_error:
        lineno, msg = json_error
        raise SystemExit(
            f"\nFATAL: JSON decode error at line {lineno}: {msg}\n"
        )

    if not records:
        raise SystemExit("FATAL: No valid records loaded.")

    # Audit
    rows_per_phase = Counter(r["phase"] for r in records)
    bases_per_phase = defaultdict(set)
    for r in records:
        if r["base_id"]:
            bases_per_phase[r["phase"]].add(r["base_id"])

    total_bases = len(set(r["base_id"] for r in records if r["base_id"]))

    print(
        f"[DATASET LOADED] path={dataset_path} "
        f"schema={schema_type} "
        f"rows={len(records)} "
        f"bases={total_bases} "
        f"rows_per_phase={dict(rows_per_phase)}"
    )

    audit = {
        "dataset_path": str(dataset_path),
        "dataset_sha256": _sha256_file(dataset_path),
        "schema_type": schema_type,
        "total_rows": len(records),
        "total_bases": total_bases,
        "rows_per_phase": dict(rows_per_phase),
        "bases_per_phase": {k: len(v) for k, v in bases_per_phase.items()},
        "created_at_utc": _utc_now_isoz(),
    }

    audit_path = SCRIPT_DIR / "logs" / "stage08D_training_input_audit.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_path, "w") as f:
        json.dump(audit, f, indent=2)

    return records


def balanced_base_split_phase08D(records):
    """Stage-08D: Deterministic split ensuring validation contains at least 1 REF, 2 CONF, 1 DES, 1 MIX, 1 CODE.
    All variants of each base stay together."""
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


def write_split_stats_phase08D(train_records, val_records, phases_before):
    train_phases = [str(r.get("phase", "")).strip().upper() for r in train_records]
    val_phases = [str(r.get("phase", "")).strip().upper() for r in val_records]
    before = Counter(phases_before)
    train_c = Counter(train_phases)
    val_c = Counter(val_phases)
    
    lines = [
        "Stage-08D: Deterministic base-level split",
        "Validation must contain at least: 1 REF, 2 CONF, 1 DES, 1 MIX, 1 CODE",
        "All variants of a base stay in same split",
        "",
        "Before split (counts per phase, row-level):",
    ]
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
    
    # Log validation base IDs
    val_bases = set()
    for r in val_records:
        bid = r.get("base_id") or r.get("sample_id", "")
        if bid:
            val_bases.add(bid)
    lines.extend([
        "",
        "Validation base IDs:",
    ])
    for bid in sorted(val_bases):
        phase = str([r.get("phase", "").upper() for r in val_records if (r.get("base_id") or r.get("sample_id", "")) == bid][0])
        lines.append(f"  {bid} ({phase})")
    
    out = SCRIPT_DIR / "logs" / "phase08D_split_stats.txt"
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-dataset-only", action="store_true")
    args = parser.parse_args()

    config = load_config()
    model_name_or_path = config["model_name_or_path"]

    dataset_dir = discover_dataset_dir()
    dataset_file = config.get("dataset_file", "golden_exemplars_v1_frozen.jsonl")
    dataset_path = dataset_dir / dataset_file
    print(f"Loading dataset from: {dataset_path}")
    _validate_freeze_certificate(dataset_path)
    records = load_training_dataset(dataset_path)

    if args.validate_dataset_only:
        print("Validation-only mode. Exiting before training.")
        return

    import torch
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        Trainer,
        TrainingArguments,
        TrainerCallback,
    )
    from peft import LoraConfig, get_peft_model, TaskType
    from datasets import Dataset

    globals()["torch"] = torch
    torch.backends.cuda.enable_flash_sdp(False)
    torch.backends.cuda.enable_mem_efficient_sdp(False)
    torch.backends.cuda.enable_math_sdp(True)

    class TrainEvalLogCallback(TrainerCallback):
        def __init__(self, log_dir):
            self.log_dir = Path(log_dir)
            self.train_log = self.log_dir / "phase08D_train_log.txt"
            self.eval_log = self.log_dir / "phase08D_eval_log.txt"

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

    # TF32: off by default
    enable_tf32 = os.environ.get("PHASE08_ENABLE_TF32", "").strip().lower() in ("1", "true", "yes")
    torch.backends.cuda.matmul.allow_tf32 = enable_tf32
    if not enable_tf32:
        print("TF32 disabled (matmul.allow_tf32=False). Set PHASE08_ENABLE_TF32=1 to enable.")

    # Stage-08D: Deterministic base-level split
    train_records, val_records, phases_before = balanced_base_split_phase08D(records)
    write_split_stats_phase08D(train_records, val_records, phases_before)
    print(f"Split: {len(train_records)} train, {len(val_records)} val")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    train_data = Dataset.from_list(train_records)
    val_data = Dataset.from_list(val_records)
    
    def tokenize_fn(examples):
        return tokenize_and_label(examples, tokenizer)
    
    print("Tokenizing datasets...")
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
    
    print(f"Loading model from {model_name_or_path}...")
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
    print(f"LoRA config: rank={config['lora_rank']}, alpha={config['lora_alpha']}, dropout={config['lora_dropout']}")
    
    eval_steps = config.get("logging_steps", 10)
    output_dir = str(SCRIPT_DIR / "checkpoints" / "phase08D")
    log_dir = SCRIPT_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
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
        save_steps=eval_steps,
        save_total_limit=2,
        logging_steps=config["logging_steps"],
        load_best_model_at_end=False,  # Stage-08D: No early stop, train full 2 epochs
        bf16=use_bf16,
        fp16=use_fp16,
        gradient_checkpointing=False,
        report_to=[],  # No wandb/tensorboard
    )
    
    callbacks = [TrainEvalLogCallback(log_dir)]
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_data,
        eval_dataset=val_data,
        data_collator=data_collator,
        callbacks=callbacks,
    )
    
    print("Starting training (Stage-08D)...")
    print(f"Epochs: {config['num_train_epochs']}, LR: {config['learning_rate']}, Batch size: {config['per_device_train_batch_size']}")
    trainer.train()
    
    # Extract final losses
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
    
    # Per-phase counts
    train_phases = Counter([str(r.get("phase", "")).strip().upper() for r in train_records])
    val_phases = Counter([str(r.get("phase", "")).strip().upper() for r in val_records])
    
    summary_lines = [
        "Stage-08D Training Summary",
        "=" * 50,
        f"Final train loss: {final_train_loss}",
        f"Final val loss: {final_eval_loss}",
        f"Total training steps: {trainer.state.global_step}",
        f"GPU peak memory (GB): {peak_mem_gb:.2f}",
        "",
        "Per-phase train row counts:",
    ]
    for p in VALID_PHASES:
        summary_lines.append(f"  {p}: {train_phases.get(p, 0)}")
    summary_lines.extend([
        "",
        "Per-phase val row counts:",
    ])
    for p in VALID_PHASES:
        summary_lines.append(f"  {p}: {val_phases.get(p, 0)}")
    summary_lines.extend([
        "",
        "Runtime errors: None",
        "Confirmation: Training completed successfully",
    ])
    
    out = log_dir / "phase08D_summary.txt"
    with open(out, "w") as f:
        f.write("\n".join(summary_lines))
    
    print("\n" + "=" * 50)
    print("Training finished.")
    print("\n".join(summary_lines))
    print(f"\nSummary written to: {out}")


if __name__ == "__main__":
    main()
