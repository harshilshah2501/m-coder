import json, re, hashlib, random
from collections import Counter
from pathlib import Path

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from tqdm import tqdm

# =====================
# CONFIG
# =====================
DATASET = "/home/harshil/Harshil-PoCs/datasets/cpt/cpt_dataset.jsonl"
SAMPLE_TOKENS = 20000
MODEL_NAME = "Qwen/Qwen2.5-Coder-14B-Instruct"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

SECRET_REGEX = re.compile(
    r"(api[_-]?key|password|secret|token)\s*[:=]\s*[\"'][^\"']+",
    re.IGNORECASE
)

# =====================
# LOAD TOKENIZER
# =====================
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True
)

# =====================
# STEP 1: JSONL + SCHEMA
# =====================
texts = []
bad_lines = 0

with open(DATASET) as f:
    for i, line in enumerate(f, 1):
        try:
            obj = json.loads(line)
            if "text" not in obj or not isinstance(obj["text"], str):
                raise ValueError("Invalid CPT schema")
            texts.append(obj["text"])
        except Exception:
            bad_lines += 1

print(f"\n[1] JSONL CHECK")
print(f"  Total records: {len(texts)}")
print(f"  Invalid lines: {bad_lines}")

if bad_lines > 0:
    print("❌ FAIL: Invalid CPT records found")
    exit(1)

# =====================
# STEP 2: SECRET SCAN
# =====================
secret_hits = sum(bool(SECRET_REGEX.search(t)) for t in texts)

print(f"\n[2] SECRET SCAN")
print(f"  Secret hits: {secret_hits}")

if secret_hits > 0:
    print("❌ FAIL: Secrets detected")
    exit(1)

# =====================
# STEP 3: TOKEN STATS
# =====================
token_counts = [len(tokenizer.encode(t)) for t in texts]
total_tokens = sum(token_counts)

print(f"\n[3] TOKEN STATS")
print(f"  Total tokens: {total_tokens:,}")
print(f"  Avg tokens/file: {int(sum(token_counts)/len(token_counts))}")

if total_tokens < 50_000:
    print("❌ FAIL: Dataset too small for CPT")
    exit(1)

# =====================
# STEP 4: DUPLICATION
# =====================
hashes = [hashlib.md5(t.encode()).hexdigest() for t in texts]
dup_ratio = 1 - (len(set(hashes)) / len(hashes))

print(f"\n[4] DUPLICATION")
print(f"  Exact duplicate ratio: {dup_ratio:.2%}")

if dup_ratio > 0.05:
    print("❌ FAIL: Excessive duplication")
    exit(1)

# =====================
# STEP 5: STRUCTURE SIGNALS
# =====================
signals = Counter()
for t in texts:
    if "class " in t: signals["class"] += 1
    if "package " in t: signals["package"] += 1
    if "@Override" in t: signals["override"] += 1

print(f"\n[5] STRUCTURAL SIGNALS")
for k, v in signals.items():
    print(f"  {k}: {v}")

if signals["class"] < len(texts) * 0.05:
    print("⚠ WARNING: Low Java class density")

# =====================
# STEP 6: PERPLEXITY (SAMPLE)
# =====================
print(f"\n[6] PERPLEXITY CHECK (sampled)")

# model = AutoModelForCausalLM.from_pretrained(
#     MODEL_NAME,
#     trust_remote_code=True,
#     torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32
# ).to(DEVICE)
# model.eval()

# sample_text = ""
# random.shuffle(texts)
# for t in texts:
#     if len(tokenizer.encode(sample_text)) >= SAMPLE_TOKENS:
#         break
#     sample_text += "\n" + t

# inputs = tokenizer(sample_text, return_tensors="pt").to(DEVICE)

# with torch.no_grad():
#     outputs = model(**inputs, labels=inputs["input_ids"])
#     loss = outputs.loss.item()
#     perplexity = torch.exp(torch.tensor(loss)).item()

# print(f"  Loss: {loss:.4f}")
# print(f"  Perplexity: {perplexity:.2f}")

print("  Skipped (first-party codebase)")
# =====================
# FINAL VERDICT
# =====================
print("\n=====================")
# if perplexity <= 14:
#     print("✅ CPT AUDIT PASSED — SAFE TO TRAIN")
# else:
#     print("❌ CPT AUDIT FAILED — FIX DATASET FIRST")
print("=====================")
