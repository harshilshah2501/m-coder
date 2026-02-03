🧱 CPT AUDITING — DETAILED STEPS (OSS, PRACTICAL)

Goal: Decide “GO / NO-GO” for CPT in under 60 minutes

STEP 0 — Ground Rules (Read Once)

Before touching files:

❌ You are not validating correctness

❌ You are not reading everything

✅ You are validating distribution health

✅ CPT succeeds or fails statistically

If this mindset isn’t locked in, stop here.

STEP 1 — Verify Dataset Structure (5 minutes)
1.1 Check JSONL integrity

head -5 cpt_dataset.jsonl
tail -5 cpt_dataset.jsonl

Each line must be valid JSON, no truncation.

1.2 Validate schema consistency

Typical valid CPT record:

{ "text": "raw source code or config here" }

🚫 Red flags:

instruction, input, output

role, assistant, system

nested arrays or messages

If you see those → this is SFT contamination.

STEP 2 — Strip Metadata at Training Boundary (Critical)

You may store CPT as JSONL, but the model must never see keys.

Required guarantee

At training time, input to tokenizer must be:

ONLY the value of "text"

Not:
{"text": "..."}

If you can’t guarantee this → STOP.

STEP 3 — File-Type & Noise Audit (10 minutes)
3.1 Use metadata file first (fastest signal)

Open cpt_metadata.jsonl and check:

file extensions

source paths

sizes

Expected dominant types:

.java, .go, .py, .yaml, .conf

🚫 Immediate disqualifiers:

.jar, .class, .zip

.log, .dump, .trace

vendored libraries

3.2 Quick binary/junk scan on dataset

grep -R $'\x00' cpt_dataset.jsonl

Any hits = corrupted CPT → fix before proceeding.

STEP 4 — Deduplication Check (Non-Negotiable)
What you need to know

CPT dies by duplication, not noise

Repeated files overweight token probabilities

From metadata, verify:

exact duplicate ratio

near-duplicate ratio (≥90% similarity)

Acceptable ranges
Metric	Threshold
Exact duplicates	<5%
Near duplicates	<10%

If you don’t know these numbers → do not CPT yet.

STEP 5 — Tokenization Sanity (Qwen-specific)
5.1 Token count (use Qwen tokenizer only)