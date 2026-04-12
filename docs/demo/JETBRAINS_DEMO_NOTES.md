# let me know how to execute scenarios like Ask, debug, plan, code? 

---

Good — now we’re finally at the point where everything connects.
Let’s strip this down to **how you actually execute Ask / Debug / Plan / Code in this system**, not just what exists.

I’ll give you **clear execution flows + what to click + what happens underneath**.

---

# 🧠 First: Mental Model (Don’t skip this)

Your system is now **NOT an IDE assistant**.

It is:

```
User (IDE) → Context Layer (WSL) → Plan-Gate (GPU) → vLLM (optional) → Response
```

* **IDE = input + display**
* **WSL = truth (code understanding)**
* **GPU = brain (planning + governance)**

Everything you do (Ask / Debug / Plan / Code) is just a **different intent routed through the same pipeline**.

---

# ⚙️ Core Execution Flow (Universal)

This is the **only flow that matters**:

```
1. User action (Ask / Debug / Plan / Code)
2. Plugin → export evidence (WSL)
3. Evidence → POST /v1/ask (GPU)
4. Plan-Gate:
   → validate evidence
   → build ContextBundle
   → planner / reasoner
5. Response → plugin UI
```

This is already confirmed in your system:

* `/v1/ask` + evidence bundle ✔️ 
* Evidence-first path ✔️ 

---

# 🧩 Now: How Each Scenario Works

## 1️⃣ ASK (General Question)

### 👇 What you do in IDE

* Trigger **Ask Motadata AI**
* Example:

  ```
  How does alert correlation work in this repo?
  ```

---

### ⚙️ What happens internally

```
Plugin:
 → POST /v1/export_evidence (WSL)
 → receives evidence_bundle

 → build ask_request.v1.0
 → POST /v1/ask (GPU)
```

Plan-Gate:

```
evidence → ContextBundle
→ PlanOnlyPlanner
→ returns PLAN_ONLY response
```

---

### ✅ Expected output

* Plan steps
* Evidence snippets
* NO execution

From your doc:

* `governance_posture = PLAN_ONLY` ✔️ 

---

### 🎯 What to validate

* `ask_path = v1_evidence`
* Evidence entries present
* Plan steps logical

---

### 🧠 Reality check

This is **NOT answering from memory**
This is:

> “Given THESE files, what is happening?”

---

## 2️⃣ DEBUG (Explain / Investigate)

This is just a **special Ask mode**.

---

### 👇 What you do

* Select file / error / stack trace
* Ask:

  ```
  Why is this failing?
  ```

---

### ⚙️ What changes internally

* Evidence includes:

  * selected file
  * surrounding code
  * possibly logs

Plan-Gate:

```
task_type = EXPLAIN_DEBUG
→ explain_debug path
```

(you mentioned this in A8)

---

### ✅ Output

* Root cause explanation
* Code-level reasoning
* No execution

---

### 🎯 What to validate

* Does it refer to **actual code lines**?
* Not hallucinated reasoning

---

### 🧠 Important

Debug = **Ask + focused evidence**

Nothing more.

---

## 3️⃣ PLAN (Design / Change Request)

---

### 👇 What you do

Ask:

```
How should we implement feature X?
```

---

### ⚙️ Internally

Same flow:

```
evidence → /v1/ask → planner
```

But output becomes:

```
Plan steps
→ file changes
→ dependency impacts
```

---

### ✅ Output

* Multi-step plan
* Files involved
* Structured reasoning

---

### 🎯 Validate

* Is plan grounded in repo?
* Does it reference actual modules?

---

### 🧠 Truth

Plan = **Ask with forward-looking intent**

---

## 4️⃣ CODE (Execution path — future / controlled)

Right now:

👉 You are **NOT executing automatically**

From your system:

```
execution = false
PLAN_ONLY
```

---

### 👇 What will happen later (M3 execution path)

Flow:

```
Ask → Plan → Plan-Gate decision:

safe_execute → Sandbox → execution
bounded_allow → restricted execution
refuse → blocked
```

---

### Current state

* You are at:

  ```
  Ask → Plan → STOP
  ```

---

### 🧠 Important clarity

You do NOT yet have:

❌ Autonomous coding
❌ Direct file modification

You have:

✅ Governed planning system

---

# 🔥 How to Run a Proper Demo (Your System)

Use your scenarios doc as backbone 

---

## 🎬 Demo Flow (Real)

### Step 1 — Health

```
Windows:
curl 8091 (WSL)
curl 8089 (GPU)
```

---

### Step 2 — Evidence export

```
POST /v1/export_evidence
```

Show:

* entries
* schema_hint

---

### Step 3 — Ask

In IDE:

```
How does topology service work?
```

Show:

* Evidence panel
* Plan steps
* ask_path = v1_evidence

---

### Step 4 — Debug

Select file → ask:

```
Why is this method failing?
```

---

### Step 5 — No match

```
quantum entanglement handler in repo
```

Show:

* empty / weak evidence
* honest response

(THIS IS CRITICAL) 

---

### Step 6 — Failure mode

Stop Context Layer:

* Ask → fallback or error behavior

---

# ⚠️ Where People Get Confused (You MUST avoid this)

## ❌ Misconception 1

“This is an AI answering questions”

✔️ Reality:

```
This is a retrieval + planner system
```

---

## ❌ Misconception 2

“Model understands repo”

✔️ Reality:

```
Model only sees evidence_bundle
```

---

## ❌ Misconception 3

“More models = better”

✔️ Reality:

```
Better evidence > better model
```

---

# 🧭 Where You Are in Roadmap

From tracker:

* L5.5 / L5.6 COMPLETE ✔️
* Now in:

  ```
  VALIDATING (E2E)
  ```



---

# 🚀 What You Should Do Next (No fluff)

## 1. Run full IDE demo

Not curl. Not CLI.

👉 JetBrains → Ask

---

## 2. Validate 4 cases

| Case     | Must work  |
| -------- | ---------- |
| Ask      | grounded   |
| Debug    | file-aware |
| Plan     | structured |
| No-match | honest     |

---

## 3. Break it intentionally

* stop WSL service
* corrupt evidence
* mismatch identity

Verify:

👉 No silent fallback

---

## 4. Only after this

Move to:

```
L5.7 (dirty buffers)
L5.8 (metrics)
```

---

# 💡 Final clarity (the most important line)

Your system is now:

> A **governed reasoning pipeline over deterministic evidence**, not an LLM assistant.

---

If you want next:

👉 I can design **real production-grade scenarios** (incident debugging, RCA, feature rollout, PR analysis) aligned with AIOps use-cases — that’s where this becomes truly powerful.
