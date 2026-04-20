# m-coder — Comprehensive Understanding Guide (150 Q&A)

**Main guide — Questions 1–150:** numbered sections below are the canonical Q&A. **Supplementary appendices** after Question 150 are optional deep reads—they do not extend the numbered list.

**How to use this document:** Read sections in order for a full arc, or jump by section title. Terms in **bold** on first substantive use are collected in the **[Glossary](#glossary)** below Question 150. A separate **validation prompt** at the very end is for engineers checking claims against the repository—it is not part of the onboarding narrative.

**Visual diagrams (repository root, next to this file):**  
- **Interactive HTML** (open in a browser): [`mcoder_architecture_v2_corrected_1.html`](mcoder_architecture_v2_corrected_1.html) (architecture / pipeline tabs), [`mcoder_sequence_v3.html`](mcoder_sequence_v3.html) (WSL ↔ Plan-Gate sequence). First load uses **Google Fonts** (requires network unless fonts are cached).  
- **PNG exports** (for slides, wikis, or printing): [`E2E-SequenceDiagram.png`](E2E-SequenceDiagram.png), [`E2E-SequenceDiagramWithZones.png`](E2E-SequenceDiagramWithZones.png), [`ModeMap.png`](ModeMap.png) — valid PNGs; large pixel dimensions (~6k-wide for sequence), so scale down when embedding.  
- **Note:** Diagram detail inside the HTML is **illustrative**—validate critical paths against the live codebase.

---

## 📌 Section 1 — Foundations

**1. What exactly is m-coder?**  
m-coder is not just an AI coding assistant. It is a **governed decision system** built around an LLM. Instead of letting the model freely generate answers or code, m-coder controls *when*, *how*, and *whether* the model should respond. It ensures that every output is grounded in real code, validated by rules, and safe to act upon.

**2. Why was m-coder needed in the first place?**  
Because LLMs are powerful but unreliable. They can hallucinate, overconfidently suggest wrong solutions, or ignore constraints. In production systems—especially enterprise systems—this behavior is unacceptable. m-coder exists to convert an unreliable model into a **controlled, deterministic system**.

**3. What is the biggest misconception about AI assistants?**  
That giving them more context (bigger context window or better RAG) will solve correctness. In reality, the problem is not just *seeing more*, but *understanding what matters and when to refuse*. m-coder addresses this by focusing on **judgment, not just context**.

**4. What does “system-first, model-second” practically mean?**  
It means the model is never in charge. The system defines rules, validates inputs, enforces constraints, and only then allows the model to generate a response. The model is treated as a **reasoning engine, not an authority**.

**5. Why is the model treated as untrusted even if it is powerful?**  
Because even the best models can fail under pressure, incomplete context, or ambiguity. Treating the model as untrusted ensures that **every output is verified**, not assumed correct.

---

## 🏗️ Section 2 — Architecture

**6. What are the main components of the m-coder system?**  
The system has three main zones:

- Workspace (WSL/Linux): retrieval and context building
- GPU Server: reasoning + Plan-Gate
- IDE Plugin: user interface

These together form a **single controlled pipeline**.

**7. What are the layers in m-coder and why do they exist?**  
Think of the system as **four foundational layers** that define how the product is governed and trained, how it runs safely, and how behavior is watched over time—plus a **fifth slice** focused on **workspace intelligence** (finding code, building evidence, packaging context for the runtime). That fifth slice **supports** the runtime layer; it does **not** replace the rules that enforce safety and authority.

- **Governance** — constitution, policies, what is allowed
- **Compilation** — how models and artifacts are produced and versioned
- **Runtime** — Plan-Gate, validation, execution, the controlled loop
- **Observation** — traces, drift, signals that something changed
- **Workspace intelligence** — deterministic retrieval, evidence bundles, context assembly: the bridge between the **repository** and what the **model** is allowed to see

Together they keep concerns separate so the system stays **clear to reason about, safe to change, and possible to scale** without mixing “find the code” with “decide if we may run a command.”

**8. Why is retrieval separated from the model?**  
Because retrieval requires access to the codebase, while the model should not. That enforces strict boundaries and reduces the risk of uncontrolled data access.

**9. Why does the GPU not directly read the repository?**  
To enforce security and determinism. The model only sees what is explicitly passed as evidence. This helps reduce the risk of hidden dependencies and unpredictable behavior.

**10. Why is the plugin designed as a thin client?**  
Because decisions should not happen on the client side. The plugin only displays results from the backend, ensuring that **all logic remains centralized and governed**.

---

## 🔄 Section 3 — Execution Flow

**11. What happens when a user asks a question?**  
The system follows a strict flow:

1. Query is received
2. Context is retrieved
3. Evidence bundle is created
4. Plan-Gate validates request
5. Model processes within constraints
6. Output is validated
7. Response returned

Every step is controlled and observable.

**12. What is Plan-Gate and why is it critical?**  
Plan-Gate is the system’s **control layer**: the place where requests are checked before expensive or risky work happens. Depending on what you are doing—asking a question, planning a change, or executing a command—it may validate schemas, assess evidence, or decide **refuse / defer / allow / execute** in a governed way. The details differ by path, but the principle is the same: **nothing proceeds on trust alone.** Without Plan-Gate, the product collapses into an ordinary LLM wrapper.

**13. What is a “canonical execution intent” (conceptually)?**  
Before anything **runs on the machine**, the system turns a raw execution request into **one clear, stable description of what was asked**—what would run, where, under which constraints—so downstream steps (guards, Plan-Gate, sandbox, audit) all refer to the **same** intent instead of re-interpreting loose text. **Questions and explanations** (Ask flows) use **evidence bundles** and question contracts; **commands** use this normalized execution picture. Implementation details, hashing, and API shapes belong in a **separate technical note** so this guide stays readable end-to-end.

**14. What is the difference between planning and execution?**  
Planning is reasoning about what should be done. Execution is actually doing it. m-coder strictly separates the two to avoid unsafe actions.

**15. What reduces the risk of hallucinations in this flow?**  
The system refuses to answer unless sufficient evidence is present. This eliminates guesswork.

---

## 🔍 Section 4 — Retrieval & Context

**16. How does m-coder retrieve relevant context?**  
It uses deterministic retrieval based on keywords, structure, and code patterns. It prioritizes meaningful code over noise.

**17. Why doesn’t m-coder use embeddings or vector databases by default?**  
Because they can introduce unpredictability. m-coder prioritizes **control and determinism over flexibility**.

**18. What is evidence quality?**  
A measure of how reliable the retrieved context is. If quality is low, the system refuses to answer.

**19. What is the difference between NO_MATCH and INSUFFICIENT?**  
**NO_MATCH** means nothing relevant was found. **INSUFFICIENT** means something was found, but not enough to trust.

**20. Why is context prioritization more important than context size?**  
Because large context still contains noise. The system should decide what matters, not just include everything.

---

## 📦 Section 5 — Contracts & Validation

**21. Why does m-coder use strict schemas instead of flexible JSON?**  
Because flexibility in AI systems quickly becomes ambiguity. A strict schema acts like a **contract** between parts of the system: every field has a defined meaning and type, so components cannot “kind of” agree. That stops silent fixes and hidden drift—if evidence or a request is wrong, the boundary **fails fast** with an explicit error instead of corrupting everything downstream. The outer envelopes for the most important payloads are **fully closed** (no surprise fields); a few **inner** diagnostic or client-specific corners may allow extra detail where the contract deliberately allows it—the rule is **strict where it matters for safety and determinism.**

**22. What happens if a schema is violated at runtime?**  
The request is gracefully rejected at the boundary where the violation occurs (ingest, plan, or execution). The system emits a **clear validation error** that names what failed. No downstream component runs. This is critical because allowing partially valid data to flow forward creates compounded errors that are harder to debug.

**23. Why are contracts versioned (e.g., v1, v0.1)?**  
Versioning allows the system to evolve without breaking existing integrations. For example, the IDE may still speak an older **Ask contract** while the backend adds a newer one with extra optional fields—both can coexist behind explicit version pins. This ensures backward compatibility and controlled rollouts.

**24. What exactly is an evidence bundle and what does it contain?**  
An evidence bundle is a structured package produced by the Context Layer. It includes:

- Selected files/snippets (code-first, not logs/noise)
- Metadata (file paths, types, relevance scores)
- Anchors (precise lines or symbols)
- Quality indicators (STRONG / WEAK / INSUFFICIENT / NO_MATCH)  

This bundle is the *only* context the model sees. If something is not in the bundle, the model should not assume it.

**25. Why is strict validation especially important for AI pipelines?**  
Because AI outputs can look plausible even when inputs are slightly wrong. Strict validation ensures that errors are caught early and explicitly. It turns hidden inconsistencies into visible failures—making the system debuggable and trustworthy.

---

## ⚖️ Section 6 — Governance & Safety

**26. What is DeterministicGuard and what does it actually enforce?**  
It is a **deterministic guard** that runs **before** Plan-Gate on the **execution** path: fixed rules only, no LLM. It blocks classes of actions that are never acceptable from a raw command line—examples include obviously destructive operations, disallowed network fetch tools, targeting protected branches, and patterns that imply irreversible harm. It answers “is this class of action even eligible to be considered?”—**not** “is this user allowed per org chart?” Enterprise-grade role systems can wrap or extend this layer; the guard itself is **rule-driven and predictable**, not a full identity directory.

**27. What does “fail-closed” mean in real scenarios?**  
If the system cannot (by design) confidently validate a request (missing evidence, ambiguous intent, schema mismatch), it refuses to proceed. For example, if evidence quality is INSUFFICIENT for a debugging query, the system returns a refusal with reasons instead of attempting a best guess.

**28. Why are silent fallbacks considered dangerous?**  
A silent fallback is when the system **quietly** switches to a weaker path—fewer guarantees, less grounding—without making that obvious to the person relying on the answer. That creates false confidence. Where a fallback is unavoidable (for example, evidence-first assembly fails and an older context path is used), the response should carry **explicit signals** so users and operators can see **what path ran and why**. Separately, **different Ask modes** (evidence-in-the-request vs build-context-on-the-server) are **different front doors**; the product should not pretend they are the same experience without saying so. Automatic “try again another way” behavior, if any, belongs in the **client or integration layer** with visible disclosure—not as an invisible second chance inside one opaque response.

**29. What types of actions are always blocked regardless of context?**  
Actions that are:

- Irreversible (e.g., mass deletion)
- Outside user authority
- Potentially harmful without confirmation  

Even if the model suggests them, the guard layer blocks them deterministically.

**30. How does authority validation work across the system?**  
Authority is enforced in **layers**: hard **deterministic** rules first (what must never run), then Plan-Gate’s **policy posture** for the execution request (refuse, defer, bounded allow, safe execute in the product sense). Today’s runtime uses **explicit signals and command classes**—for example, dangerous commands are refused, and hints in the request can force refusal—rather than consulting a full corporate roles database inside every call. **Organizational** authority (who may merge to production, who owns a service) is expressed through **governance and product policy** and can grow over time; treat the runtime as the **enforceable core**, not the entire HR system.

---

## 🔁 Section 7 — Observability

**31. What is a trace identifier and how is it used end-to-end?**  
A **trace identifier** is a unique id attached when the user acts in the IDE and carried through context assembly, Plan-Gate, and any execution. Operators can **stitch logs** from different services into one story: what arrived, what was validated, what ran, and what came back.

**32. What does observability include beyond basic logging?**  
Observability in m-coder includes:

- Structured logs (request type, routing mode, status, duration)
- Decision artifacts (why a path was chosen)
- Evidence metrics (coverage, anchors, noise ratio)
- Error surfaces (explicit reasons, not generic failures)  

This enables both debugging and performance analysis.

**33. Why is transparency critical for user trust?**  
Because users need to understand *why* the system answered or refused. By exposing routing decisions, evidence quality, and limitations, the system avoids “black-box” behavior and builds confidence.

**34. What is routing visibility with a concrete example?**  
Routing visibility means you can always answer: **which path handled this request**, **whether the answer was plan-only or used deeper reasoning**, and **whether evidence was strong enough**. In practice, responses carry **routing mode** and **metadata** (evidence quality, reasons for refusal or weakness) so nothing looks like a generic chat reply. Logs tie the same request together with a **trace identifier** and timing. If an integration retries on a **different** service mode after a failure, that retry should be **visible** in the UI or ops tooling—not invisible—because the guarantees of the two modes are not identical.

**35. How do logs help improve the system over time?**  
Logs reveal patterns: frequent refusals, noisy retrieval, slow paths, or schema errors. These signals feed back into retrieval tuning, contract refinement, and guard rules—closing the improvement loop without guessing.

---

## 🧪 Section 8 — Validation & Testing

**36. Why is HTTP/CLI validation preferred over UI testing?**  
Because it tests the system at the contract level. UI layers can mask issues (formatting, retries). HTTP tests validate the exact request/response behavior of Plan-Gate and Context Layer—what actually matters in production.

**37. What defines a successful system test in m-coder?**  
Not just a correct answer, but:

- The **intended mode** was used (evidence-in-request vs server-side context build, etc.) and contracts were respected end-to-end
- **Strong** evidence quality when a grounded answer is expected—and honest **refusal** when it is not
- Proper refusal when needed
- Valid schemas at every step  

All of these should pass consistently.

**38. What is a run summary and what does it capture?**  
A **run summary** aggregates results across scenarios:

- Pass/fail counts
- evidence quality distribution
- latency stats (p50/p95)
- Routing patterns  

It acts as a single snapshot of system health for a given run.

**39. How does regression testing work with Golden Exemplars?**  
Golden Exemplars define expected behavior for key scenarios. On every change, the system re-runs these scenarios and checks metrics (refusal accuracy, evidence coverage, etc.). Any regression there should block the change.

**40. What is a failure scenario and how is it used constructively?**  
A failure scenario is a curated case where the system previously behaved incorrectly (e.g., answered with weak evidence). It is added to the test suite to ensure the same mistake never happens again—turning failures into permanent guards.

---

## 🚫 Section 9 — Design Principles (What NOT to Do)

**41. Why avoid fully autonomous agents in this system?**  
Autonomous agents make independent decisions and execute actions, which reduces control and increases risk. m-coder prioritizes governed execution where every step is validated and observable.

**42. Why is relying purely on prompt engineering insufficient?**  
Prompts can guide behavior but cannot (by design) enforce guarantees. They degrade with changes in models or context. m-coder uses **system-level enforcement** (schemas, guards, routing) instead of fragile prompt tricks.

**43. Why avoid heavy frameworks (graph DBs, complex pipelines) by default?**  
Because they introduce operational complexity and hidden behavior. m-coder prefers simpler, deterministic mechanisms (lexical retrieval + authority signals) that are easier to reason about and debug.

**44. Why isn’t the system optimized primarily for speed or convenience?**  
Because incorrect fast answers are worse than slower correct ones. The system optimizes for **correctness first**, then improves latency without compromising guarantees.

**45. Why keep UI logic separate from system logic?**  
To reduce the risk of divergence between what the user sees and what the system actually does. The plugin reflects backend truth; it does not implement decision logic.

---

## 🚀 Section 10 — Future Direction

**46. What is the Assist Layer and how does it fit without breaking guarantees?**  
The Assist Layer enhances user experience (suggestions, proactive hints, active-file awareness) but does not change core contracts. It sits on top of the governed pipeline and uses the same evidence-first principles.

**47. Which parts of the system are considered stable and why?**  
Stable components include:

- Plan-Gate rules and phases
- Evidence-first contract
- Retrieval baseline (deterministic, code-first)  

These are foundational guarantees that other features build upon.

**48. What areas are actively evolving and why?**

- Retrieval improvements (better ranking, authority signals)
- UX enhancements (Assist Layer)
- Integration surfaces (IDE, tooling)  

These evolve to improve usability and coverage without weakening core guarantees.

**49. How does m-coder stay model-agnostic in practice?**  
By isolating the model behind strict inputs (evidence bundle) and outputs (validated schemas). Upgrading from one model to another does not change system behavior because the *contracts* remain the same.

**50. What is the long-term goal of m-coder as a system?**  
To operationalize senior-engineer judgment at scale—where every AI-assisted decision is grounded, validated, and traceable, making it safe to use in real production workflows.

---

## 🔐 Final Principle

m-coder is not built to make AI more powerful.  
It is built to make AI **safe, reliable, and trustworthy**.

---

## 🧠 Section 11 — Advanced Retrieval (Depth)

**51. What makes retrieval “deterministic” in m-coder?**  
Deterministic retrieval means the same query over the same repo yields the same ranked results. There is no randomness, no hidden vector similarity drift. Ranking is based on explicit signals—tokens, paths, symbols, file classes—so behavior is reproducible and debuggable.

**52. How are file classes used in ranking?**  
Files are categorized (e.g., core code, supporting code, logs, tests). Core code is boosted; noisy classes are demoted. This helps reduce the risk of logs/tests from dominating results for code questions.

**53. What is “anchor selection” and why does it matter?**  
Anchors are the exact lines or symbols shown to the model. Good anchors point to logic (methods, conditions), not boilerplate (imports, headers). Correct anchors reduce hallucination and improve answer precision.

**54. How does the system avoid noise dominance?**  
By penalizing non-code artifacts and enforcing core-ratio thresholds. If too many results are from noisy classes, the system downgrades quality or refuses.

**55. What is LOW_CORE_RATIO and why is it important?**  
It flags when retrieved results contain too little actual code. Even if many files match, the system may refuse if the signal is weak—reducing the risk of false confidence.

---

## 🧩 Section 12 — Authority & Code Understanding

**56. What is the Product Authority layer?**  
A curated mapping of concepts → owners, collaborators, and known distractors. It biases retrieval toward the *true implementation owners* instead of keyword-heavy files.

**57. How does authority improve answers?**  
If multiple files mention a concept, authority boosts the one that *implements* it. This steers answers toward real logic rather than surface references.

**58. What is the code index (beyond plain files)?**  
A lightweight structure capturing symbols, methods, imports, and 1-hop relationships. It enables understanding of “who calls what” without heavy graph databases.

**59. Why avoid full graph DBs for code understanding?**  
They add operational complexity and latency. m-coder achieves sufficient structure with curated signals and lightweight indexing.

**60. How are distractors handled?**  
Known misleading files (e.g., handlers with many mentions) are explicitly demoted via authority rules to avoid top-rank pollution.

---

## 🧭 Section 13 — Plan-Gate Internals

**61. How does Plan-Gate classify a request?**  
Not every entry point uses the same internal labels—and that is intentional. **Command execution** flows through a compact decision: effectively **refuse, defer, allow in a bounded way, or allow execution** after guards and checks. **Planning and emulation** paths may speak in shorter **phase** names (such as reference-only vs confirm vs design) for teaching and tests. **Ask** paths emphasize **schema validity and evidence quality** before any model work. So “classification” is **one coherent idea** (is this allowed, and how?) with **different shapes** depending on whether you are asking, planning, or executing.

**62. What is phase doctrine in simple terms?**  
Doctrine describes **how much freedom** the system grants at each stage: from **hard refusal**, to **bounded** answers, to **design-only** guidance, to **sandboxed execution**, to **mixed** modes under tight constraints. The names in documentation (including shorthand like REF/CONF/DES/CODE/MIX) are a **shared vocabulary** for architects and reviewers. The runtime maps that vocabulary onto **concrete decisions** per pipeline—do not expect a single acronym to print identically in every log line.

**63. Why is phase classification separate from the model?**  
So **policy is enforced before generation**. The model proposes; it does not grant permission to execute or override safety outcomes.

**64. What is irreversibility detection?**  
It is the question: **if this action succeeds, can we cleanly undo it?** Irreversible or boundary-crossing work gets stricter handling—extra gates, refusal, or human-in-the-loop depending on product policy. Simple rule-based detectors cover obvious cases; richer policy can attach for structured actions. The principle matters more than any one implementation file.

**65. What is authority validation inside Plan-Gate?**  
It answers: **is this actor allowed to request this action under current policy?** In the core runtime that starts as **deterministic rules and explicit signals** (dangerous commands, denial hints), layered with **DeterministicGuard** and governance. Full **organizational** RBAC can sit above or beside this as the product matures.

---

## 🔁 Section 14 — Runtime Loop (Controlled Execution)

**66. What is the runtime loop in m-coder?**  
A **state machine** that cycles: propose → validate → execute (sandbox) → observe → decide next. Each step is **allowed or forbidden** explicitly—illegal transitions **stop** the loop rather than “best effort” forward. The codebase may implement this pattern in more than one integration layer; conceptually it is still **one idea**: **no step skips validation**, and **terminal outcomes** (success, refusal, block, failure) are real stops. Low-level wiring belongs in engineering docs; here, remember the **shape** of the loop.

**67. Why use a state machine instead of free-form loops?**  
To reduce the risk of illegal transitions (e.g., executing before validation). The loop enforces order and terminal conditions.

**68. What are terminal states?**  
States where execution should stop (success, refusal, failure). The system cannot (by design) continue past these points.

**69. What happens on invalid transitions?**  
The loop halts with an explicit error. No partial execution is allowed.

**70. How are intermediate results tracked?**  
Through structured artifacts (proposal, decision, tool result) linked per iteration, enabling full traceability.

---

## 🧪 Section 15 — Sandbox & Execution

**71. Why is execution sandboxed instead of running directly on the host?**  
Because execution is where a reasoning system stops being “advice” and starts having real consequences. Once a command runs against a filesystem, process table, network, or repository, the blast radius becomes real. A sandbox creates a controlled boundary around that blast radius. It gives the runtime a place to execute approved actions without giving the model, or even the broader runtime, unrestricted access to the developer machine or server. In practice, this means the system can allow bounded, inspectable operations while still blocking unsafe host-level side effects.

**72. What kinds of operations are allowed inside the sandbox?**  
Only operations that are explicitly supported by the runtime’s tool and execution policies. That usually means safe, bounded activities such as reading approved files, running selected tests, evaluating code in a controlled way, or producing structured artifacts for later inspection. The key point is that the sandbox is not a generic shell handed to the model. It is a constrained execution surface where every allowed action is known in advance, tied to a validated request, and observable afterward.

**73. How does the system decide whether something should be planned, sandboxed, or blocked?**  
The decision is made before execution, not during it. Plan-Gate classifies the request, checks authority, evaluates irreversibility, and assigns the proper runtime posture. If the request is design-only, it never reaches the sandbox. If it is a bounded code or tool action and the authority and boundary checks pass, it may enter the sandbox. If it crosses a protected boundary, lacks approval, or violates a guard rule, it is blocked before any execution starts. This separation is critical because it reduces the risk of the model “trying something first” and only later discovering it was unsafe.

**74. What does “normalized execution result” mean?**  
Raw execution output is often messy: exit codes, partial stdout, stack traces, generated files, and tool-specific error messages. The runtime converts this into a structured result so the rest of the system can reason about it deterministically. A normalized result usually contains a clear status, the relevant output streams, references to artifacts, timing metadata, and failure reasons if something went wrong. This lets the loop treat different tools consistently instead of having to special-case every command or runner.

**75. What happens when execution fails inside the sandbox?**  
Failure does not mean chaos. The sandbox reports the failure in a structured way, the loop records it, and the runtime decides what is allowed next. Depending on policy, the next step may be to stop immediately, return the failure to the user, or perform a bounded retry if retries are explicitly allowed. What does not happen is silent recovery or free-form improvisation. A failed execution becomes an observed event in the system, not a reason for the model to start inventing ungoverned workarounds.

**76. Why is direct execution by the model forbidden?**  
Because direct execution would collapse the most important boundary in the system. The model is good at proposing, not at being trusted with side effects. If the model could directly run commands, then authority validation, irreversibility checks, schema validation, and auditability would all become optional in practice. m-coder forbids this so that execution always remains a governed consequence of validated intent—not a spontaneous extension of model output.

**77. How does the sandbox support truthful outcomes like executed, blocked, or refused?**  
The runtime does not collapse all negative outcomes into a vague “failed.” It distinguishes between:

- **Refused**: the system gracefully rejected the request at a policy or authority layer
- **Blocked**: the request reached an execution-related boundary but was intentionally stopped for policy reasons  
- **Executed**: the action was allowed and actually ran  

This distinction matters operationally. It lets users and operators understand whether a request was impossible, unsafe, unauthorized, or simply unsuccessful after being allowed.

**78. Why is artifact capture important in sandboxed execution?**  
Because many execution results cannot (by design) be understood from a single success/failure bit. Test logs, generated patches, structured diagnostics, and captured outputs often explain *why* an execution succeeded or failed. Artifact capture gives the runtime and the user something concrete to inspect. It also makes replay, debugging, and later audit possible.

**79. How does sandboxing help future extensibility?**  
A good sandbox abstraction means the system can support new tools or backends later without changing core governance logic. The runtime can keep the same decision model—validate, allow, observe—while swapping how a tool is actually executed underneath. That is far safer than hard-coding execution logic all over the system.

**80. What is the deeper principle behind sandboxing in m-coder?**  
The deeper principle is simple: reasoning and side effects should never be fused. The model may help decide what to do, but the system should remain in charge of whether anything actually happens. The sandbox is the practical mechanism that enforces that separation.

---

## ⚡ Section 16 — Performance & Latency

**81. Where does most of the latency come from in a real m-coder request?**  
Latency usually comes from two places: getting the right context and getting the model to reason over it. Retrieval can be slow because it involves reading indexes, resolving files, ranking evidence, and building snippets. Inference can be slow because the model still needs to process the prompt and generate a response. The important point is that latency is not treated as a mystery. Each stage is measured separately so the system can tell whether slowness came from context assembly, routing, inference, validation, or execution.

**82. Why does m-coder not optimize for lowest possible latency at any cost?**  
Because an AI system that answers quickly but incorrectly is worse than a slower system that is honest and safe. m-coder optimizes for correctness first, then reduces latency without weakening guarantees. That means it is willing to spend time on better retrieval, stronger validation, and explicit refusal logic if that is what it takes to avoid a misleading answer.

**83. How does deterministic retrieval actually help performance?**  
Deterministic retrieval helps performance by reducing waste. If the system can reliably find the right files and snippets early, it does not need to send large, noisy prompts to the model. Smaller, sharper evidence bundles mean fewer irrelevant tokens, faster inference, and better answers. So determinism is not only about correctness—it also improves efficiency by cutting prompt bloat.

**84. Why is increasing the model context window not the same as solving latency or quality?**  
A larger context window lets the model *see* more, but it does not make the model *attend correctly* to what matters. In fact, feeding more material can increase both latency and confusion. The model may spend more time processing irrelevant context while still missing the critical invariant. m-coder chooses staged context and deliberate selection over brute-force context stuffing.

**85. What latency targets matter for an interactive engineering assistant?**  
What matters is not one magic number but the shape of the latency distribution. The system should feel responsive for common asks, predictable for heavier requests, and explainable when something is slow. That is why p50 and p95 matter more than a single average. A good system keeps the common path fast while making tail latency visible and actionable.

**86. How does the system diagnose slow paths without guesswork?**  
By propagating the same **correlation id** end-to-end and recording **per-stage timing**. That way, an operator can see whether a slow request spent time in retrieval, schema validation, Plan-Gate, model inference, or execution. Without this breakdown, teams end up arguing about whether the model or the retrieval layer is the bottleneck. With it, they can prove it.

**87. What are examples of healthy performance optimizations in m-coder?**  
Healthy optimizations include improving ranking so fewer snippets are needed, reducing noisy evidence before prompting, caching deterministic intermediate results, tightening schemas so invalid work is gracefully rejected early, and optimizing the inference stack itself. These all preserve system truth. Unhealthy optimizations would be things like silently skipping validation or lowering refusal standards to make the system appear faster.

**88. How does performance relate to trust?**  
Trust is not just about being correct; it is also about being predictably correct. If the system is fast sometimes, slow sometimes, and opaque all the time, users lose confidence. Performance observability—knowing what happened and why—is part of trust, not a separate concern.

**89. Why are latency warnings treated differently from correctness regressions?**  
Because correctness regressions attack the core promise of the system, while latency warnings are often operational follow-through unless they break usability outright. m-coder’s philosophy is that a slow truthful system can still be improved, but a fast misleading system is already broken.

**90. What is the deeper performance philosophy of m-coder?**  
The system is designed to be efficient through discipline, not through shortcuts. Better context selection, better routing, and tighter contracts beat raw token volume and accidental speed hacks.

---

## 🏗️ Section 17 — Infrastructure & Deployment

**91. Why is the system split between workspace-side retrieval and GPU-side reasoning?**  
Because the code lives near the workspace, while the heavy reasoning compute lives on the GPU server. m-coder respects that physical reality instead of pretending one node should do everything. Retrieval needs local, trustworthy access to repo state. Reasoning needs fast model serving and centralized control. Splitting them this way preserves both performance and governance boundaries.

**92. Why is WSL or Linux used as the source-of-truth side for context?**  
Because that is where the repository is actually present and where deterministic indexing and file inspection make sense. Letting the GPU reach across the network and directly inspect the developer repo would blur boundaries, create hidden dependencies, and weaken auditability. Keeping retrieval local means the system always knows where context came from.

**93. What exactly runs on the GPU side of the deployment?**  
The GPU side hosts the governed reasoning stack: Plan-Gate and model serving, typically through vLLM. This is the part of the system responsible for validating requests, enforcing runtime posture, and invoking the model only after the correct context has already been packaged and sent.

**94. What role does vLLM play in this architecture?**  
vLLM is the serving layer for the model. Its job is not governance, not retrieval, and not policy. Its job is to serve the model efficiently—handling batching, memory usage, and inference throughput—while the rest of the system ensures the model sees only validated evidence and produces output that is checked again afterward.

**95. How does this architecture scale as more engineers use the system?**  
It scales by keeping context work near each workspace while centralizing model serving and governance. More users may require more inference capacity or better request scheduling on the GPU side, but the retrieval pattern remains local and controlled. This is much cleaner than copying entire repositories to a central inference server or trying to make one node understand every workspace directly.

**96. How are environment differences handled across Windows, WSL, Linux, and GPU hosts?**  
Through explicit configuration, versioned contracts, and validated deployment profiles. Ports, URLs, workspace roots, and service roles are treated as declared configuration, not hidden assumptions. That makes it possible to support multiple host profiles while keeping the runtime behavior consistent.

**97. Why is “no direct repo access from GPU” more than just a deployment preference?**  
Because it is part of the system’s truth model. If the GPU could read the repo directly, then the evidence bundle would stop being the authoritative context boundary. The system would no longer be able to guarantee that the model only reasoned over curated evidence. So this is not just a networking choice; it is a correctness invariant.

**98. What kinds of deployment problems does this architecture avoid?**  
It avoids stale mirrored repos on the GPU, hidden path mismatches between developer machines and servers, uncontrolled file visibility, and subtle ambiguity about which copy of the code the model actually saw. All of those problems are common in naive AI coding systems and are exactly what m-coder is designed to avoid.

**99. Why does infrastructure design matter so much for an AI assistant?**  
Because an AI assistant is not just a UI talking to a model. Once it interacts with code, tools, and developer intent, infrastructure choices become behavior choices. Where retrieval runs, where the model runs, and how requests flow between them all shape whether the assistant remains trustworthy.

**100. What is the deeper deployment principle of m-coder?**  
Code should be retrieved where it lives, reasoning should happen where compute is strongest, and governance should remain where control is enforced. That is the architectural spine of the whole system.

---

## 🔐 Section 18 — Security & Compliance

**101. How does m-coder reduce the risk of data leakage to the model?**  
By never letting the model freely inspect the workspace or host environment. The model only receives curated evidence that passed through the Context Layer and runtime contracts. That means the system can control exactly what information is exposed, why it was exposed, and how it is traced afterward.

**102. What does zero-trust mean in the context of m-coder?**  
Zero-trust here means no component is assumed correct just because it is inside the system. The plugin should send valid payloads. The Context Layer should produce schema-valid evidence. Plan-Gate should validate intent explicitly. The model should still be checked after generation. Trust is always earned through contracts and enforcement, not granted by position.

**103. How are sensitive or high-risk actions protected?**  
They are protected through layers, not one magical switch. First, the request should classify into an allowed phase. Then authority should pass. Then irreversibility checks should pass. Then any execution should happen only through a governed sandbox. This layering makes it much harder for a single failure to create a serious incident.

**104. Why is explicit auditability such a major design goal?**  
Because enterprises do not just need systems that behave safely; they need systems that can later prove how and why they behaved that way. Auditability means that when a question arises—who asked what, what evidence was used, why an action was blocked, why an answer was refused—the system can answer with records instead of stories.

**105. How do traceability and compliance reinforce each other?**  
Compliance becomes much easier when every important decision has an identifier, an artifact trail, and a clear runtime path. Instead of reverse-engineering behavior after the fact, teams can reconstruct it directly. This reduces operational risk and supports internal audit, security review, and production incident analysis.

**106. Why is blocking arbitrary filesystem or network access important?**  
Because once arbitrary access exists, the model becomes a general exploration engine over potentially sensitive environments. That is incompatible with controlled enterprise deployment. m-coder deliberately narrows the model’s visibility and capabilities so that even a very fluent model cannot (by design) wander into protected territory.

**107. How does m-coder handle the fact that the model itself may generate risky suggestions?**  
It assumes that will happen. The model is not expected to be perfectly safe on its own. Instead, the rest of the system is designed to catch, constrain, or refuse those suggestions before they become actions. That is why safety is implemented as infrastructure, not as optimism.

**108. Why is this architecture easier to defend during security review?**  
Because the boundaries are concrete and explainable. Reviewers can inspect the evidence bundle contract, the Plan-Gate rules, the sandbox path, and the logging model. They do not have to accept vague claims that the prompt is “careful enough.”

**109. What is the difference between being secure and appearing secure?**  
Appearing secure means telling users the assistant is safe because it usually behaves well. Being secure means the architecture makes bad behavior difficult, visible, and preventable. m-coder aims for the second, not the first.

**110. What is the deeper security philosophy of m-coder?**  
The system does not try to guess what safety might mean in each moment. It encodes safety as explicit boundaries, validated requests, limited visibility, and auditable consequences.

---

## 🔌 Section 19 — Integration & IDE Experience

**111. What role does the IDE plugin actually play in the system?**  
The plugin is the user-facing entry point, not the decision-maker. It captures user intent, active-file context, and selections, sends requests to the governed backend, and renders the returned results. This keeps the developer experience smooth without moving system truth into the UI.

**112. Why is a thin plugin better than a “smart” plugin?**  
A smart plugin usually ends up growing hidden logic: fallback behavior, partial retrieval, local heuristics, or UI-side interpretation of truth. That creates drift between what the user sees and what the backend actually decided. A thin plugin avoids this by staying mostly as a transport and rendering layer.

**113. What does evidence-first UX look like from a user’s point of view?**  
It means the user can see why the system answered the way it did. Instead of receiving a polished but unsupported explanation, the user sees the selected files, snippet anchors, and evidence quality indicators. This shifts trust from style to grounding.

**114. Why does routing visibility matter in the IDE?**  
Because users should know whether the system answered through the strong path or a compatibility path. If the evidence-first path failed and a weaker fallback was used, that should be visible. Otherwise the UI creates false confidence by hiding how the answer was produced.

**115. What is active-file intelligence and how should it be used carefully?**  
Active-file intelligence means the currently open file can bias retrieval and response shaping. This is useful because the active file often contains the user’s immediate working context. But it should remain a bias, not an override. The system should not assume the active file is automatically the most authoritative file.

**116. Why should the plugin avoid doing retrieval or reasoning locally?**  
Because local plugin logic is hard to keep consistent, hard to validate, and easy to let drift. Once retrieval or reasoning spreads into the plugin, the governed backend stops being the single source of truth. That is exactly the kind of silent architectural drift m-coder is built to resist.

**117. How does the plugin support truthful execution outcomes?**  
By rendering the exact backend outcome instead of inventing softer language. If something was refused, it should look refused. If it was blocked, it should look blocked. If it executed, it should be clear that execution actually happened. This honesty is part of the product, not just a UI detail.

**118. Why is plugin simplicity also a maintenance advantage?**  
Because the more logic the plugin contains, the more places behavior can diverge when the backend evolves. A thin plugin is easier to upgrade, easier to reason about, and easier to keep aligned with versioned contracts.

**119. What is the right mental model for IDE integration in m-coder?**  
The IDE is where the system meets the user, but not where the system becomes true. Truth is produced in the backend and projected into the IDE.

**120. What is the deeper UX principle here?**  
The UI should reduce friction without hiding reality. A trustworthy assistant interface makes the governed path understandable, not invisible.

---

## 🔄 Section 20 — Evolution & Migration

**121. How can m-coder change models without changing its behavior contract?**  
Because the model is treated as a replaceable worker behind strict boundaries. Inputs are structured through evidence bundles and versioned requests. Outputs are validated through schemas, guards, and runtime rules. As long as those contracts remain stable, the model can change while the system behavior stays governed.

**122. What actually changes when the base model is upgraded?**  
Usually fluency, depth of reasoning, and code quality improve or shift. What should not change is the runtime posture: refusal logic, evidence requirements, routing transparency, and execution safety. That distinction is essential. Model upgrades are allowed to improve capability, but not to rewrite system truth.

**123. Why is model-agnosticism strategically important for this project?**  
Because the model landscape changes quickly. If the whole system depends on one specific model family or provider behavior, the project becomes fragile. By anchoring behavior in contracts and governance instead of raw model personality, m-coder stays adaptable.

**124. How should new features be introduced without destabilizing the system?**  
New features should enter through versioned contracts, bounded scope, feature flags when necessary, and validation against the existing behavior baseline. The system should not grow through ad hoc shortcuts that bypass its own enforcement layers.

**125. When does a new capability require new exemplars or new validation?**  
When it introduces a new risk surface, new authority boundary, new irreversible action path, or new behavioral expectation. In that case, existing validation is not enough; the system needs fresh behavioral coverage so the new capability does not quietly dilute the old guarantees.

**126. Why is backward compatibility not enough on its own?**  
Because a system can remain API-compatible while still behaviorally drifting. m-coder cares about both: contract compatibility and behavioral stability. That is why Golden Exemplars and regression gates matter alongside schema versions.

**127. What should never change even as the system evolves?**  
The non-negotiables: evidence-first reasoning, fail-closed posture, explicit observability, separation of reasoning from execution, and refusal under insufficient grounding. If those are weakened, the system may still function, but it will stop being m-coder in the meaningful sense.

**128. How should the team think about future expansion?**  
As controlled widening from a closed baseline, not as open-ended feature accumulation. Every addition should preserve the spine of the system: governed inputs, bounded reasoning, validated actions, and auditable outcomes.

**129. What does “production-grade” really mean in this architecture?**  
It does not simply mean the assistant sometimes gives useful answers. It means the full system behaves predictably under real conditions: correct routing, explicit refusals, deterministic retrieval, validated execution, traceable logs, and stable contracts.

**130. What is the deeper migration philosophy of m-coder?**  
Capabilities may evolve, models may improve, and interfaces may change—but the system should continue to behave like a disciplined engineering control plane, not a conversational toy that happens to know some code.

---

## 🎯 Section 21 — End-to-End Stories, Practice & Review (Questions 131–150)

**131. What does a complete end-to-end Ask flow look like in practice?**  
A developer highlights a function and asks a concrete question. The plugin captures query, active file, selection, and workspace metadata. The Context Layer performs deterministic retrieval, picks meaningful anchors, and builds a **versioned evidence bundle**. Plan-Gate validates the request and evidence quality. If quality suffices, the model explains the code **using only that bundle**. The runtime validates output and returns routing and evidence metadata. The plugin shows the answer **with** references and quality—not as a detached chat reply.

**132. What does the user gain from this flow compared with a normal chat assistant?**  
The answer is **inspectable**: sources, anchors, strength of evidence, and routing are visible. Trust shifts from tone to **grounding**.

**133. Why is this called “evidence-first” rather than “RAG”?**  
RAG often means “stuff more text into the prompt.” Here, evidence is a **governed, versioned artifact** passed through validation—so the path is enforceable and observable, not a best-effort retrieval hack.

**134. What does a *correct* refusal look like when evidence is too weak?**  
Example: a broad diagnosis is asked, but retrieval only surfaces generic references and little core implementation code. The system should **refuse** with a clear reason—not invent a detailed root cause.

**135. Why is refusal better than a plausible partial answer?**  
In engineering, a weak answer is often treated as truth. Refusal protects downstream decisions from **polished mistakes**.

**136. What should a useful refusal include?**  
What was missing (e.g. authoritative files, anchors, signal-to-noise), and what evidence would **unlock** a grounded answer next time.

**137. How does a “naïve AI coding” system typically behave instead?**  
It sends the question (plus loose files) straight to the model, answers even when retrieval is weak, hides fallbacks, and leans on the prompt to stay “safe.” That optimizes for fluency over **accountability**.

**138. Why does the naïve approach feel good at first?**  
It is fast and confident. That smoothness often comes from **borrowed** trust, not verified grounding.

**139. Why does m-coder accept more visible structure in the UX?**  
So users know **when** they can rely on an answer and **when** the system is refusing or weakening guarantees by design—not by accident.

**140. What is the one-line contrast between the two philosophies?**  
A typical assistant optimizes for **sounding helpful**; m-coder optimizes for **being right for traceable reasons**—or refusing when it cannot be.

**141. What should a new engineer verify first when learning this system?**  
That **evidence**, **Plan-Gate**, and **contracts** are real—not decorative—and that refusals are a **valid** success case.

**142. During an incident, how should a team treat a refusal or weak-evidence answer?**  
As a **signal** to gather better context or narrow the question—not as something to bypass by “asking louder.”

**143. What is a healthy rhythm for reviewing Golden Exemplars and regressions?**  
Often enough that behavior **drift** is caught before release—paired with schema and routing checks, not only model taste.

**144. Why is “give the model more context” an incomplete fix by itself?**  
More text often adds **noise**; judgment and selection matter as much as volume.

**145. How can you tell retrieval is noisy versus the model misunderstanding good evidence?**  
Noisy retrieval shows up as weak core signal, distractor-heavy paths, or quality reasons in metadata; good evidence with a bad answer points to **downstream** issues.

**146. What belongs in governance documents versus in runtime enforcement?**  
Doctrine and policy **intent** live in docs; **enforceable** guarantees live in schemas, guards, and services. Both must stay aligned.

**147. When is it acceptable to skip the governed path in production?**  
**Never**—shortcuts destroy the audit and safety story the system is built for.

**148. How does strict contracting reduce lock-in to one model vendor?**  
The **interfaces** stay stable; the model is replaceable behind them.

**149. If you could only watch one kind of signal for “trust health,” what would it be?**  
The balance of **grounded answers** versus **explicit refusals** under real queries—plus whether refusals are **informative**, not vague.

**150. Where should a skeptic start when auditing m-coder?**  
Trace one request end-to-end: **evidence origin → Plan-Gate → model → response metadata**—and confirm each step is **visible** and **validated**.

---

## Glossary

Short definitions for terms used across this guide. Implementation details live in engineering docs and the repository; this table is for **shared vocabulary** only.

| Term | Meaning |
|------|---------|
| **Anchor** | A specific line range or symbol in a file chosen to ground the model’s answer (not boilerplate). |
| **Ask** | The governed question-and-answer path: user query plus validated context; not a free-form chat bypass. |
| **Assist Layer** | Optional UX hints (e.g. active file, suggestions) that **advise** without replacing contracts or Plan-Gate. |
| **Canonical execution intent (concept)** | A single, stable description of what would run for a **command**—so guards, Plan-Gate, and audit agree on one intent. Distinct from Ask/evidence flows. |
| **Context Layer** | The component that assembles repo-local context: indexing, retrieval, and packaging into an evidence bundle. |
| **Contract** | A versioned agreement on request/response shape (fields, types, allowed values); mismatches fail at the boundary. |
| **Correlation id** | An id carried with a request so logs from different services can be joined (often aligned with a trace identifier). |
| **Deterministic guard** | Fixed rules on the execution path (before Plan-Gate) that block disallowed command classes; no LLM involved. |
| **Deterministic retrieval** | Same query + same workspace snapshot → same ranked results; based on explicit signals, not random or opaque similarity. |
| **Distractor** | A file that looks relevant by keywords but misleads ranking; authority rules may demote it. |
| **Evidence bundle** | Structured package of selected snippets, metadata, anchors, and quality signals—the curated input boundary for reasoning. |
| **Evidence-first** | Governance stance: answers must be justified by validated evidence, not by model fluency alone. |
| **Fail-closed** | If validation is uncertain or evidence is insufficient, the system **stops** rather than guessing. |
| **File class** | Category of a file for ranking (e.g. core code vs. test vs. noisy artifact). |
| **Golden Exemplars** | Curated scenarios with expected outcomes; used to catch behavioral regression. |
| **Governed execution** | Actions run only after policy, guards, and (where applicable) sandbox rules—not directly from raw model text. |
| **INSUFFICIENT** | Evidence quality label: something matched, but not enough to justify a strong grounded answer. |
| **Irreversibility** | Whether an action is hard to undo; drives stricter gates or refusal. |
| **LLM** | Large language model—the reasoning component, not the authority on safety or truth. |
| **LOW_CORE_RATIO** | Quality signal: too little “core” code in retrieved evidence relative to noise or breadth. |
| **NO_MATCH** | Evidence quality label: nothing relevant enough was found for the ask. |
| **Phase doctrine** | Vocabulary for how much freedom the system grants (e.g. refuse, bounded answer, design-only, execution)—see Q62. |
| **p50 / p95** | Latency percentiles: median vs tail; used to discuss responsive common paths and heavy or slow outliers. |
| **Plan-Gate** | Control layer that validates requests, evidence, and posture before expensive or risky work. |
| **Product Authority** | Curated mapping from concepts to implementation owners to steer retrieval toward real logic. |
| **RAG** | Retrieval-augmented generation (generic industry term). m-coder adds **governance** on top of retrieval. |
| **RBAC** | Role-based access control; organizational permissions may extend what the runtime enforces as policy matures. |
| **Routing mode** | How a response was produced (e.g. plan-only vs deeper reasoning); should be visible to users when relevant. |
| **Sandbox** | Bounded execution environment for approved actions— not an unconstrained shell for the model. |
| **Schema** | Machine-readable structure for payloads; invalid data is rejected rather than silently coerced. |
| **STRONG / WEAK** | Evidence quality labels along the spectrum before INSUFFICIENT or NO_MATCH. |
| **Trace identifier** | End-to-end id for a user request, used in logs and ops correlation. |
| **vLLM** | A model **serving** stack for efficient inference; not where governance or retrieval logic should live. |
| **Workspace intelligence** | The slice of the system concerned with finding code, ranking, and building evidence for the runtime. |
| **WSL** | Windows Subsystem for Linux; common host profile for workspace-side context in mixed-OS setups. |
| **Zero-trust (in this doc)** | No component is trusted by position alone—contracts and checks apply throughout. |

---

## 📎 Supplementary appendices (not part of the 150 questions)

These sections **summarize** themes from the main guide in narrative form for readers who want a **story-shaped** recap without working through the numbered list again.

### Supplementary A — Narrative: one Ask journey

Imagine a concrete debugging question flowing from the IDE through context export, evidence packaging, validation, bounded reasoning, and back to the UI with citations. The numbered answers in **Questions 131–133** are the authoritative breakdown; this appendix is a **parallel telling** for readability only.

### Supplementary B — Narrative: when refusal is the win

Weak evidence for a high-stakes question should end in a **clear stop**, not a speculative essay. The numbered answers in **Questions 134–136** define that behavior; this appendix restates the **human** reason teams should celebrate good refusals.

### Supplementary C — Narrative: naïve assistant vs m-coder

The contrast is not “more features” but **accountability**: governed retrieval, explicit boundaries, and honest limits. The numbered answers in **Questions 137–140** carry the precise distinctions; this appendix is a **shortcut summary** for stakeholders.

---

## 🧭 Closing thought

If a normal AI assistant tries to be *clever*,  
m-coder is designed to be *correct*.  
And in production systems, correctness always wins.

---

## 🧪 Validation Prompt (Cursor — Use Separately, Not Part of Doc)

Use this outside the document to generate and validate against repo truth:

""" You are reviewing the m-coder system against the repository.

Objectives:

1. Verify every major component described (layers from governance through workspace intelligence, Plan-Gate, evidence-first Ask, runtime loop, evidence bundle).
2. Map each concept to actual code paths/files.
3. Validate that behavior matches documentation (fail-closed, no silent fallback, evidence-first).
4. Identify any drift, gaps, or mismatches.

Output format:

- Section → Code Mapping
- Verified Behavior
- Deviations (if any)
- Risk Level (LOW/MEDIUM/HIGH)

Constraints:

- No assumptions
- Only repo-backed claims
- Explicit file references required """

