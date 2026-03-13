🚀 POST-CPT VALIDATION (PROVES CPT ACTUALLY HELPED) CPT without validation = placebo. Phase A — Loss Curve Sanity (Immediate) During CPT training: Healthy Smooth monotonic loss ↓ No spikes No NaNs Unhealthy Flat loss → CPT useless Sudden collapse → bad corpus 📌 If loss doesn’t move in first 1–2K steps, stop. Phase B — Perplexity Delta (Objective) Re-run same perplexity test: Metric Expectation Base Qwen PPL e.g. 12.4 After CPT ↓ by 10–30% If delta <5% → CPT added little value. Phase C — Code Completion Probe (Most Honest Test) Create a frozen prompt set (10–20 cases): public class EventRouter { private final EventBus bus; public EventRouter(EventBus bus) { this.bus = bus; } public void route(Event event) { // COMPLETE Compare: Base model CPT-trained model Look for: Correct imports Domain-specific class usage No hallucinated frameworks If CPT model uses Motadata-specific abstractions → success. Phase D — Diff-Based Regression Check Run both models on same prompt: diff base_output.txt cpt_output.txt CPT success signature: More identifiers from your codebase Less generic boilerplate Shorter, decisive completions Phase E — Read-Only Safety Check Ask: “Explain what LocalEventChangeNotificationHandler does.” CPT model should: Summarize your architecture Not invent features Use your terminology If it hallucinates → dataset contamination. 🧾 FINAL CPT ACCEPTANCE CHECKLIST Before Training ☐cpt_audit.py passed ☐ Perplexity ≤14 ☐ Duplication <5% After Training ☐ Loss curve healthy ☐ PPL ↓ ≥10% ☐ Domain completions improved ☐ No hallucinated APIs Decision ☐ CPT ACCEPTED ☐ Move to SFT / RAG One brutal truth (remember this) CPT doesn’t teach behavior. It teaches instinct. You’ve now: Audited it correctly Trained it responsibly Proven it helped This is exactly how serious product teams do CPT. If you want next: SFT dataset design on top of this CPT Or RAG vs CPT boundary for Motadata Or benchmark harness for coding accuracy Say the word. Good catch. This is exactly why the audit exists. Now let’s fix it safely, fast, and correctly — without manual pain. 🔥 What this means (no sugar-coating) CPT must be zero-secret. Even commented secrets poison the distribution. 3 hits is small — this is easy to fix.


Perfect. This is the **right next move**, and we’ll do it **fast, controlled, and honest**.

Below is a **ready-to-run Phase-C Completion Probe plan** that fits in **30–45 minutes**, no heroics, no infra pain.

---

# 🔬 Phase-C — CPT Completion Probe (Execution Plan)

## 🎯 Objective (lock this in)

Answer **one question only**:

> *Does the CPT model complete Motadata code more like a Motadata engineer than the base Qwen model?*

Not fluency.
Not verbosity.
Not explanations.

**Just instinct.**

---

## 🧪 Test Design (Minimal, High-Signal)

### Number of probes

* **10 prompts** (minimum viable)
* 15–20 if you want extra confidence

### Prompt rules (VERY important)

* ❌ No instructions (“complete this carefully…”)
* ❌ No docstrings explaining behavior
* ❌ No chat framing
* ✅ Pure code context
* ✅ Cursor-style `// COMPLETE HERE`

We want to **force the model to rely on priors**.

---

## 🧱 Probe Categories (Pick 2–3 from each)

### Category A — Class / Method Completion

Tests: naming, imports, control flow

```java
public class EventRouter {

    private final EventBus eventBus;

    public EventRouter(EventBus eventBus) {
        this.eventBus = eventBus;
    }

    public void route(Event event) {
        // COMPLETE
    }
}
```

---

### Category B — Registration / Wiring Patterns

Tests: architectural instinct

```java
public class BootstrapSecondary {

    public void start() {
        // COMPLETE
    }
}
```

(Use a **trimmed version**, not the full file.)

---

### Category C — Handler / Processor Logic

Tests: domain abstraction recall

```java
public class LocalEventChangeNotificationHandler {

    @Override
    public void handle(Event event) {
        // COMPLETE
    }
}
```

---

### Category D — Async / Vertx Patterns

Tests: concurrency idioms

```java
vertx.executeBlocking(promise -> {
    // COMPLETE
});
```

---

## ⚙️ How to Run (Concrete Commands)

### Models to compare

1. **Base model**

   * `Qwen/Qwen2.5-Coder-14B`
2. **CPT model**

   * `motadata-coder-cpt-v1` (checkpoint-2000)

### Generation settings (keep fixed)

```
temperature = 0.2
top_p = 0.95
max_new_tokens = 200
do_sample = false   # important
```

Deterministic > creative.

---

## 📄 Output Capture (Do this cleanly)

For **each prompt**, save:

```
probe_01_base.txt
probe_01_cpt.txt
```

Do NOT edit outputs.

---

## 🔍 Evaluation Criteria (This is the heart)

For each probe, score **Base vs CPT** on these axes:

### 1️⃣ Domain Token Usage

* Uses Motadata classes?
* Correct package assumptions?
* Avoids alien frameworks (Spring, Netty, etc.)

### 2️⃣ Structural Correctness

* Correct method calls
* Reasonable control flow
* No fantasy APIs

### 3️⃣ Brevity & Confidence

* Short, decisive completions
* No “TODO-style” waffle
* No over-generalization

### 4️⃣ Hallucination Penalty (hard fail)

* Invented classes ❌
* Invented config ❌
* Invented infra ❌

---

## 📊 Simple Scoring (Don’t overthink)

For each probe:

| Probe          | Base   | CPT    |
| -------------- | ------ | ------ |
| Domain fit     | 0–2    | 0–2    |
| Structure      | 0–2    | 0–2    |
| Brevity        | 0–1    | 0–1    |
| Hallucinations | -2 / 0 | -2 / 0 |

You’re not chasing absolute scores.
You’re looking for **consistent CPT advantage**.

---

## ✅ CPT Phase-C PASS CONDITION

Declare **Phase-C PASSED** if:

* CPT wins on **≥70% of probes**
* CPT shows **more Motadata identifiers**
* CPT shows **fewer hallucinations**
* CPT outputs feel “locally obvious”

If CPT ties but is **shorter & safer** → still a pass.

---

## 🚫 What NOT to Do (Common Traps)

* ❌ Don’t add RAG context yet
* ❌ Don’t explain prompts
* ❌ Don’t cherry-pick best outputs
* ❌ Don’t rerun with different temperatures

We want **raw instinct**, not best-of-N.

---

## 🧠 What Good Looks Like (Qualitative)

You’ll *feel* it when CPT wins:

* Base model: generic, polite, framework-agnostic
* CPT model: *“oh, this is clearly Motadata code”*

That “feels right” signal is real — and reliable.

---

## ⏱ Time Budget

* Prompt prep: ~10 min
* Inference runs: ~15–20 min
* Review + diff: ~10 min

Total: **~35–40 minutes**

---

## 🔜 After You Run It

Come back with **one of these**:

* “CPT wins clearly”
* “CPT ties”
* “CPT loses on X category”

I’ll then:

* Update the **live tracker**
* Decide **ACCEPT / FIX / RERUN**
* Tell you whether to move to **Embeddings or SFT next**

You’re doing exactly what serious teams do.
Go run Phase-C — I’ll be here when you’re back.

📋 Phase-C: CPT Completion Probe - Implementation Complete
✅ What Was Implemented
Script Location: test_cpt_model.py

Features:

10 Frozen Prompts across 4 categories (exactly as specified):

3 Class/Method completions
2 Registration/Wiring patterns
3 Handler/Processor logic
2 Async/Vertx patterns
Deterministic Generation (Phase-C spec):

temperature = 0.2
top_p = 0.95
max_tokens = 200
do_sample = False
Comprehensive Scoring (4 criteria):

Domain Fit (0-2): Motadata tokens vs alien frameworks
Structure (0-2): Valid syntax, reasonable logic
Brevity (0-1): Short & decisive
Hallucinations (-2/0): Hard penalty for invented APIs
Detailed Outputs:

Individual probe files: probe_XX_base.txt and probe_XX_cpt.txt
JSON report with full metrics
Markdown comparison document
Pass Criteria (from your spec):

CPT wins ≥70% of probes
More Motadata tokens than base
Fewer hallucinations than base

How to run:
cd /home/harshil/Harshil-PoCs
source venv/training/bin/activate
python evaluation/test_cpt_model.py

Optional: Specify custom paths:
python evaluation/test_cpt_model.py <cpt_path> <base_path>

📊 Expected Outputs
Location: evaluation/results/phase_c/

phase_c_report_YYYYMMDD_HHMMSS.json

Complete metrics and scores
Win/loss/tie breakdown
Aggregate statistics
phase_c_comparison_YYYYMMDD_HHMMSS.md

Human-readable side-by-side comparison
All 10 probes with completions
Scoring details for each
Individual probe files:

probe_01_base.txt through probe_10_base.txt
probe_01_cpt.txt through probe_10_cpt.txt

📈 What the Report Will Show
Summary Metrics:

Win/Loss/Tie counts
CPT win rate percentage
Average domain token scores
Total Motadata tokens used (base vs CPT)
Hallucination counts
Per-Probe Details:

Prompt used
Both completions (base & CPT)
Individual scores breakdown
Winner determination
Final Verdict:

✅ PASSED if CPT wins ≥70% + better domain usage
⚠️ MARGINAL if 50-70% win rate
❌ FAILED if CPT doesn't improve
⏱️ Estimated Runtime
Model loading: ~2-3 minutes (both models)
Generation: ~2-3 minutes per probe × 10 = ~20-30 minutes
Scoring & reporting: ~1 minute
Total: ~25-35 minutes

🎯 Next Steps After Phase-C
If PASSED:

Review the comparison markdown for qualitative assessment
Confirm CPT shows "Motadata instinct"
Proceed to SFT training
If MARGINAL/FAILED:

Review individual probe outputs
Identify weak categories
Consider:
More CPT training steps
Better dataset coverage
Adjusted learning rate
💡 Usage Tips
To run just one category:
Modify the script to filter FROZEN_PROBES by category before running.

To test different generation settings:
Modify the generate_completion() function parameters (but note: this breaks comparability per Phase-C spec).

To add more probes:
Add entries to the FROZEN_PROBES list following the same structure.