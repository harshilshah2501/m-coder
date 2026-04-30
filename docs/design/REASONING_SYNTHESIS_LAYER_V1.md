# Reasoning Synthesis Layer v1

**Status:** Design (not implemented)  
**Placement:** Between `build_reasoning_context` (`reasoning_context.d1`) and `build_articulated_answer` / Debug narration consumers  
**Non-goals:** Retrieval changes, Plan-Gate governance, EventBus extractor, model/vLLM swaps, larger prompts, random-context inflation  

---

## 1. Problem statement

The pipeline has strong **evidence depth** (retrieval, authority, graph traversal, wiring maps, EventBus topology, governance). The **final narration** still often behaves like:

```text
anchor → summarize anchor → add disclaimer
```

That produces answers that are technically grounded but **emotionally thin**: they read like a citation of one traffic signal instead of describing how traffic moves through the city.

The gap is not missing evidence; it is **missing structural synthesis between evidence and prose**.

**Desired distinction**

| Current implicit question | Desired implicit question |
|---------------------------|---------------------------|
| What is the most defensible statement about this anchor? | What subsystem behavior do **all** proven signals jointly support? |

---

## 2. Audit: where narration collapses to anchor-method stories

This section maps failure modes to **concrete code paths** (design audit only).

### 2.1 Reasoning context emphasizes the anchor first

`build_reasoning_context` computes `primary_owner`, `anchor_method`, `typed_nodes`, `flow_steps`, `coverage_gaps`, `api_route_mapping`, `eventbus_context`, etc. The prompt renderer leads with **Primary anchor** and lists role/description tied to that symbol (`render_reasoning_context_for_prompt` in `runtime/ask_service/reasoning_context.py`). That is appropriate for **models**, but downstream prose generators that mirror this ordering reproduce anchor-centrism.

### 2.2 Articulated answer treats anchor as default lede when expansion is weak

In `runtime/ask_service/articulated_answer.py`, `_unified_paragraphs`:

- Inserts `anchor` at the front of `all_components` when it is not already listed.
- When **fewer than two** grounded components are visible, returns a short paragraph centered on **the strongest grounded component** (`anchor`), optionally plus coverage-gap language — classic **method-collapse**.
- Intent branches such as **mail** and **notification** still lean on `anchor` / `anchor_cls` for the opening sentence when building `sentences`, even when collaborators exist.

### 2.3 Illustrative anchor-collapse examples (user-facing)

| Query flavor | Typical anchor | Why it reads method-centric |
|--------------|----------------|----------------------------|
| Mail / SMTP config | `MailServerConfiguration.beforeUpdate` | First sentence names the class hook instead of “mail settings flow through API lifecycle → validation → store → notification”. |
| Config stores | `AbstractConfigStore.getItem` | Answer stays at contract method instead of “typed stores behind shared abstraction + persistence boundary”. |
| Notifications | `NotificationEngine.start` | Orchestration role is buried under engine entrypoint naming. |
| Availability | `AvailabilityCorrelationEngine.start` | Same pattern: entrypoint symbol dominates subsystem story. |
| API architecture | `APIServer.start` | Ingress/bootstrap role competes with route-table evidence unless synthesis merges API route mapping + verticle chain deliberately. |

These are **symptoms**: the system stops narrative expansion at the **authority-selected symbol** unless explicit intent branches (API base class, EventBus lines) override.

---

## 3. Solution outline: Reasoning Synthesis Layer v1

Insert a **deterministic, bounded** transformation:

```text
reasoning_context (d1 + maps)
        ↓
reasoning_synthesis v1   ← NEW
        ↓
articulated_answer / explain_debug narration consumers
```

The synthesis layer answers, in structured form:

- **Which subsystem** is this (taxonomy label + confidence)?
- **What role** does each **visible** component play (entrypoint, abstraction, handler, store, async bridge)?
- **What sequence** is supported by **proven** edges (graph paths, route mapping, EventBus exact addresses)?
- **Where are async and storage boundaries** (from EventBus addresses vs stores list)?
- **What is explicitly unknown** (carry forward `coverage_gaps`, map unknowns)?

**No new facts:** only classify, merge, and reorder **already-present** evidence keys. Never invent classes, methods, routes, or bus addresses.

---

## 4. Schema: `reasoning_synthesis.v1`

Suggested JSON shape (extends your sketch with minimal typing for implementation clarity):

```json
{
  "schema_version": "reasoning_synthesis.v1",
  "query_intent": "architecture|how|debug|list|plan|notification|mail|config_store|correlation|unknown",
  "subsystem": {
    "label": "notification",
    "confidence": "high|medium|low",
    "signals": ["typed_nodes.handlers", "eventbus_context.match"]
  },
  "system_summary": "One paragraph max: subsystem behavior first; no leading method name unless inside evidence citation.",
  "entrypoints": [
    { "symbol": "APIServer.start", "role": "ingress_bootstrap", "source": "typed_nodes|authority|route_mapping" }
  ],
  "abstractions": [
    { "symbol": "AbstractAPI", "role": "rest_handler_base", "source": "inheritance|api_route_mapping" }
  ],
  "core_components": [
    { "symbol": "NotificationEngine", "role": "orchestrator", "source": "typed_nodes" }
  ],
  "collaborators": [],
  "storage_components": [
    { "symbol": "UserConfigStore", "role": "persistence", "source": "typed_nodes.stores" }
  ],
  "async_components": [
    {
      "kind": "eventbus",
      "address": "change.notification",
      "producers": ["X"],
      "consumers": ["Y"],
      "source": "eventbus_topology",
      "exact_match_only": true
    }
  ],
  "control_flow_steps": [
    { "step": "api_request", "support": "api_route_mapping" },
    { "step": "notification_dispatch", "support": "typed_nodes+eventbus" }
  ],
  "proven_facts": [
    "Route GET /api/v1/foo maps to FooAPI per api_route_mapping snapshot."
  ],
  "bounded_inferences": [
    {
      "statement": "beforeUpdate behaves as a lifecycle hook on configuration updates.",
      "rule_id": "pattern.beforeUpdate",
      "confidence": "medium"
    }
  ],
  "confidence_limits": [],
  "next_inspection_targets": [],
  "method_collapse_risk": {
    "detected": false,
    "reason": "≥2 distinct grounded components with roles assigned"
  }
}
```

**Field notes**

- **`system_summary`:** Produced **after** subsystem + roles; **must not** begin with `Class.method` as the grammatical subject (see narrative contract §6).
- **`async_components`:** EventBus producers/consumers **only** when topology proves **exact address match**; otherwise omit or list under `confidence_limits`.
- **`bounded_inferences`:** Small enumerated rule IDs (see §5) so outputs stay auditable.
- **`method_collapse_risk`:** Feeds evaluation rubric §8.

---

## 5. Synthesis rules (deterministic + bounded)

### 5.1 Lead with subsystem behavior

Order of reasoning:

1. Classify subsystem from query + signals (`typed_nodes`, maps, inheritance).
2. Attach **roles** to symbols already in `reasoning_context`.
3. Merge **multi-hop** stories only when **≥2 grounded components** participate **with distinct roles** (entrypoint ≠ store ≠ async boundary).
4. Attach **anchors** as **evidence bullets**, not as the thesis sentence.

### 5.2 Anchors as evidence, not as the answer

The primary_owner / `anchor_method` remains the **retrieval authority anchor** but must not automatically become the **rhetorical topic**. The synthesis summary sentence should read like architecture, e.g. “Mail configuration updates participate in the REST lifecycle and configuration persistence layers…” with anchor cited second.

### 5.3 Multi-hop requirement

If narration implies a **chain** (A→B→C), require:

- At least **two** distinct grounded components from evidence buckets **or**
- One component + one **proven** edge from graph paths / route mapping / EventBus **exact** pairing.

Otherwise: shorten to single-hop + explicit limit.

### 5.4 Bounded inference rules (whitelist)

| Pattern / signal | Allowed inference |
|------------------|-------------------|
| Class name `Abstract*` | Shared abstraction / contract layer |
| Method `beforeUpdate` | Lifecycle hook (not specific semantics) |
| `APIServer.start` | Ingress / bootstrap for HTTP/API surface |
| EventBus | Producer/consumer **only** on **exact** shared address in topology snapshot |
| `*Store`, `*Repository` | Persistence boundary candidate |
| `*Engine`, `*Handler` | Orchestration / handling (not arbitrary call order) |

### 5.5 Hard prohibition

- Do not emit symbols not present in `reasoning_context` evidence paths (including collaborators list, route mapping keys, EventBus nodes).
- Do not stitch causality across subsystems without a **proven** edge or explicit `bounded_inference` with medium/low confidence.

---

## 6. Narrative contract

### 6.1 Ask (PLAN_ONLY articulated answer)

Sections (conceptual; rendering can stay multi-paragraph):

| Block | Content |
|-------|---------|
| **Summary** | Subsystem-level **first sentence**; no `Class.method` as grammatical subject. |
| **Flow** | Ordered **roles** (ingress → abstraction → handler → store → async), each tied to a proven signal. |
| **Anchors** | Authority anchor + key citations (`evidence_citations`, route rows, EventBus pairs). |
| **Limits** | `coverage_gaps` + map unknowns; no governance-internal tokens in user-visible strings. |

### 6.2 Debug (`explain_debug`)

| Block | Content |
|-------|---------|
| **Hypothesis** | Evidence-bounded; ties subsystem + symptom class. |
| **Proven flow** | Only edges visible in snippet + route/bus proofs. |
| **Risk point** | Concrete branch / failure mode suggested by code shape, not speculative cascade. |
| **What is not proven** | Explicit negative knowledge. |
| **Next inspection** | Files/symbols/tests from synthesis `next_inspection_targets` + reasoning cues. |

Debug continues to use existing sanitization and grounding rules in `reasoner.py`; synthesis **feeds** structured targets rather than replacing the reasoner.

---

## 7. Before / after examples (illustrative)

### 7.1 API architecture

**Before:** “`APIServer.start` bootstraps the HTTP server…”  
**After:** “HTTP/API ingress boots through the Vert.x server stack; REST handlers mount under shared `AbstractAPI` patterns, with concrete routes reflected in the route-handler snapshot (`FooAPI` ↔ `/api/v1/...`). **Anchors:** `APIServer.start`, route mapping rows E1–E3.”

### 7.2 Mail server configuration

**Before:** “`MailServerConfiguration.beforeUpdate` validates…”  
**After:** “Mail settings changes run through the configuration API lifecycle: shared REST/base patterns validate and persist before downstream delivery paths react. **Anchors:** `MailServerConfiguration.beforeUpdate`, collaborating stores/handlers from evidence.”

### 7.3 Config stores

**Before:** “`AbstractConfigStore.getItem` reads configuration…”  
**After:** “Configuration reads are mediated through a shared store abstraction; concrete stores specialize persistence while callers depend on the contract. **Anchors:** `AbstractConfigStore`, concrete `*Store` classes in snapshot.”

### 7.4 Notifications

**Before:** “`NotificationEngine.start` coordinates…”  
**After:** “Notification orchestration fans out channel work while async handoffs use the EventBus where topology proves matching addresses. **Anchors:** orchestration class + EventBus producer/consumer pairs (exact address).”

### 7.5 Availability correlation debug

**Before:** “`AvailabilityCorrelationEngine.start` starts correlation…”  
**After:** “Hypothesis: correlation scheduling ties to engine bootstrap in snippet; proven flow stops at visible start/init; cross-service causality not proven in excerpt. **Next:** expand method body / callers.”

### 7.6 API route debug

**Before:** Summary drifts to unrelated stores.  
**After:** “Proven flow: route table maps `/api/v1/x` → `XAPI`; router initialization binds handlers during server start. **Not proven:** runtime authz/body validation off-snippet.”

---

## 8. Evaluation rubric

Use for offline regression on scenario JSON + golden checks:

| Metric | Scale | Meaning |
|--------|-------|---------|
| **depth_score** | 0–3 | 0 anchor-only; 1 subsystem named; 2 roles + boundary; 3 multi-hop with proven edges |
| **fluency_score** | 0–3 | 0 robotic list; 1 readable; 2 coherent mini-architecture story; 3 natural engineer explanation |
| **grounding_score** | 0–3 | 0 speculation; 1 tight to evidence; 2 maps + graph; 3 explicit proven vs inferred |
| **overclaim_risk** | 0–3 | 0 none; 3 severe (fabricated edges / wrong causality) |
| **method_collapse_detected** | bool | True if first sentence topic is `Class.method` or sole component story |

Target: **depth ≥ 2**, **grounding ≥ 2**, **overclaim_risk ≤ 1**, **method_collapse_detected = false** on STRONG evidence scenarios.

---

## 9. Governance and scope discipline

- **No retrieval changes:** synthesis reads existing `reasoning_context` only.
- **No Plan-Gate changes:** gates remain upstream; synthesis does not bypass quality blocks.
- **No extractor changes:** EventBus topology consumed as-is.
- **No model dependency:** synthesis is pure Python + deterministic rules (+ optional schema validation).
- **Ask freeze:** until design review, **do not** merge prose-only tweaks in `articulated_answer`; prefer implementing synthesis then wiring consumers.

---

## 10. Acceptance checklist

- [ ] Schema `reasoning_synthesis.v1` documented and versioned.
- [ ] Synthesis rules enumerated with inference whitelist.
- [ ] Narrative contracts for Ask and Debug aligned with existing sanitization.
- [ ] Before/after examples cover listed scenarios.
- [ ] Rubric defined with collapse detection.
- [ ] Implementation plan filed separately with phased rollout and tests.

---

## References (code)

- `runtime/ask_service/reasoning_context.py` — `build_reasoning_context`, `render_reasoning_context_for_prompt`
- `runtime/ask_service/articulated_answer.py` — `_unified_paragraphs`, `build_articulated_answer`
- `runtime/ask_service/reasoner.py` — `EXPLAIN_DEBUG` grounding and payload shaping
- `runtime/ask_service/v1_ingest.py` — orchestration of reasoning_context → articulated_answer
