# Reasoning Synthesis Layer v1 — Implementation Plan

**Status:** Plan (no implementation in this document)  
**Companion:** `REASONING_SYNTHESIS_LAYER_V1.md`  
**Constraints:** No retrieval, governance, EventBus extractor, or model changes in v1 implementation wave unless explicitly rescoped.

---

## 1. Goal

Implement `reasoning_synthesis.v1` as a **pure function** of existing `reasoning_context.d1` (+ optionally read-only passes over already-loaded map payloads embedded in context):

```text
reasoning_context → build_reasoning_synthesis(...) → reasoning_synthesis.v1
```

Then thread the result into:

- `build_articulated_answer` (Ask / PLAN_ONLY)
- Debug narration builders / CLI formatters that benefit from structured “proven vs next step” (without weakening `explain_debug` JSON contracts)

**Principle:** *Synthesize before prose.* Do not enlarge prompts or add stochastic context.

---

## 2. Non-goals (v1)

| Area | Reason |
|------|--------|
| Retrieval ranking / bundle expansion | User explicitly excluded |
| Plan-Gate policy | Unchanged |
| EventBus topology extraction | Unchanged |
| vLLM prompts size/content | No “bigger prompts” workaround |
| Replacing `explain_debug` JSON schema | Synthesis **augments** consumers; optional additive field under metadata |

---

## 3. Phased rollout

### Phase A — Library + schema only (low risk)

1. Add `runtime/ask_service/reasoning_synthesis.py` (name TBD) exporting:
   - `build_reasoning_synthesis(reasoning_context: dict, query: str, task_hints: dict | None) -> dict`
2. Validate output against a small JSON-schema dict or dataclass checks in tests.
3. **Wire nowhere** except unit tests and optional debug logging behind `MCODER_*` flag.

**Exit criteria:** Deterministic golden tests from fixture `reasoning_context` snapshots.

### Phase B — Metadata threading (medium risk)

1. In `v1_ingest.py`, after `build_reasoning_context`, call `build_reasoning_synthesis` and attach:
   - `metadata["reasoning_synthesis"] = {...}`
2. Ensure payload size caps (reuse reasoning_context-style truncation rules): max lengths on lists, max string length for `system_summary`.

**Exit criteria:** Snapshots show `reasoning_synthesis.v1` present on successful asks; blocked paths either omit or include minimal synthesis from partial context (explicitly documented).

### Phase C — Ask shadow mode (mandatory before production prose)

1. Do **not** change default Ask paragraphs yet. Run scenario suites with **`articulated_answer` unchanged** while recording parallel `metadata["reasoning_synthesis"]`.
2. Compare legacy answer vs synthesis + shadow rubric (`compute_shadow_rubric`): depth, fluency, grounding, overclaim risk, method collapse.
3. Emit `docs/validation/REASONING_SYNTHESIS_SHADOW_REPORT.md` via `runtime/scripts/gen_reasoning_synthesis_shadow_report.py`.

**Exit criteria:** Shadow report shows synthesis behavior is stable and rubric improves or stays neutral vs baseline; Ask scenario suite still passes unchanged.

### Phase D — Ask production (articulated answer consumption)

1. Refactor `articulated_answer.build_articulated_answer` to prefer **`system_summary` + ordered roles** from synthesis when enabled (flag).
2. Fallback: existing `_unified_paragraphs` if synthesis missing (backward compat).
3. Enforce narrative contract when `method_collapse_risk.detected`.

**Exit criteria:** Phase C shadow eval wins; Ask scenario suite (e.g. 9/9) still passes.

### Phase E — Debug / CLI alignment (later)

1. Map synthesis `next_inspection_targets` + `proven_facts` into existing debug cue helpers in `cli.py` **without** duplicating reasoner logic.
2. Keep `explain_debug` JSON generation in `reasoner.py` authoritative; synthesis supplies **structured hints** only.

---

## 4. API sketch

```python
def build_reasoning_synthesis(
    *,
    query: str,
    reasoning_context: Dict[str, Any],
    task_type: str = "general",
) -> Dict[str, Any]:
    ...
```

**Inputs**

- `reasoning_context` as produced today (`schema_version` `reasoning_context.d1`).
- `query` for intent classification (reuse / align with `_query_intent` in `articulated_answer` — consider shared module to avoid drift).

**Output**

- Dict matching `reasoning_synthesis.v1` in the design doc.

---

## 5. Implementation tasks (checklist)

### 5.1 Subsystem classification

- [ ] Map query keywords + dominant `typed_nodes` buckets → `subsystem.label`.
- [ ] Emit `subsystem.signals` as explicit keys (debuggability).

### 5.2 Role assignment

- [ ] Reuse `reasoning_context`’s `_classify_node` semantics where possible (import private helpers or duplicate minimal table — **avoid** divergence; prefer single module `component_roles.py` if needed).

### 5.3 Mandatory expansion (context reach)

When `task_type` in `architecture`, `general`, or broad Ask:

- [ ] Always attempt: parent abstraction (`inheritance.chain` tail / `abstractions`), downstream collaborator (handlers/stores), upstream entrypoint (entrypoints), EventBus pair if query touches async terms.
- [ ] If a dimension is missing, add to `confidence_limits` — do not invent.

### 5.4 Control flow steps

- [ ] Prefer `api_route_mapping` steps for API queries.
- [ ] Prefer `eventbus_context` for publish/consume queries (exact address match).
- [ ] Fall back to `flow_steps` strings only as **lowest** tier (they are already heuristic).

### 5.5 Method collapse detection

- [ ] Set `method_collapse_risk.detected` when grounded component count < 2 **or** when `system_summary` would start with anchor pattern `^[A-Za-z0-9_]+\.[a-z][A-Za-z0-9_]*` as topic.

### 5.6 Bounded inferences

- [ ] Implement small `RULE_IDS` map from design doc §5.4; attach confidence.

---

## 6. Testing strategy

| Layer | Tests |
|-------|-------|
| Unit | Golden `reasoning_context` fixtures → expected `reasoning_synthesis` snapshots (mail, notification, API route, config store, thin evidence). |
| Contract | Schema keys present; no unknown symbols vs allowlist from context dump. |
| Regression | Full `runtime/tests` for Ask ingest + articulated answer; reasoner tests untouched in Phase A–B. |
| Rubric | Optional script: compute depth/fluency/collapse flags from saved scenario JSON. |

---

## 7. Performance and budgets

- **CPU:** Single dict walk; O(n) in sizes already bounded by reasoning_context.
- **Payload:** Cap lists (e.g. 8 components per bucket, 5 flow steps, 500 chars `system_summary`).
- **Memory:** No duplicate copies of large snippets; synthesis references symbols only.

---

## 8. Risk register

| Risk | Mitigation |
|------|------------|
| Drift between `_query_intent` and synthesis intent | Shared classifier or single source of truth |
| Double-hedging (synthesis + articulated_answer) | Single “limits” merge point |
| Debug confusion if two sources of “next steps” | Keep reasoner authoritative; synthesis as hints only |
| Ask regression | Phase D production wiring behind flag until shadow + scenarios green |

---

## 9. Open decisions (pre-implement)

1. **Flag name** for Phase C (`MCODER_REASONING_SYNTHESIS_V1=1` suggested).
2. **Whether** `system_summary` is template-filled vs lightweight NLG templates (deterministic string patterns only in v1).
3. **Whether** to expose `reasoning_synthesis` in public API responses by default or only in verbose/debug metadata.

---

## 10. Definition of done (v1)

- [ ] `build_reasoning_synthesis` shipped and tested.
- [ ] Metadata threading documented for API consumers.
- [ ] Articulated answer uses synthesis when flag on; legacy path preserved.
- [ ] Design constraints (no retrieval/governance/extractor/model changes) verified in review checklist.
- [ ] Scenario rubric shows reduced `method_collapse_detected` on STRONG evidence cases.
