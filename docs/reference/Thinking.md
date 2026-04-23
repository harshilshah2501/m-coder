# Motadata Ask Deep Slice - Detailed Fix Analysis (All 5 Passing)

Date: 2026-04-22  
Latest verification artifact: `runtime/.run/motadata_behavior_validation.ask.deep.json`  
Executed scenarios:
- `ask_base_api_class`
- `ask_mail_server_configuration`
- `ask_config_store_organization`
- `ask_api_layer_architecture`
- `ask_notification_handlers`

Current status from latest run: **all_pass = True**.

---

## Human-First Snapshot

This section answers the most important manual-review questions first:
- What query was executed?
- What did we expect?
- What was the actual human-facing answer?
- Why did it pass?

| Scenario | Query | Expected (contract highlights) | Human-facing answer (first line) | Result |
|---|---|---|---|---|
| `ask_base_api_class` | `Which class is the base class for all APIs?` | Must contain `AbstractAPI` | `Direct answer ... strongest API base-class signal ... AbstractAPI` | PASS |
| `ask_mail_server_configuration` | `How does mail server configuration work?` | Text anchor + generic infra ratio `<= 0.6` | `Primary implementation owner: MailServerConfiguration ... beforeUpdate` | PASS |
| `ask_config_store_organization` | `How are config stores organized?` | Store anchors in answer | `Primary implementation owner: AbstractConfigStore ... getItem` | PASS |
| `ask_api_layer_architecture` | `Explain the API layer architecture.` | API/route anchors in answer | `Primary implementation owner: APIServer ... start` | PASS |
| `ask_notification_handlers` | `Find all classes that handle notifications.` | Notification handler anchors | `Primary implementation owner: NotificationEngine ... start` | PASS |

---

## Per-Query Detailed Analysis

### 1) `ask_base_api_class` (PASS)

- **Query**
  - `Which class is the base class for all APIs?`
- **Expected**
  - Ask path `v1_evidence`
  - `PLAN_ONLY`, execution false
  - answer contains `AbstractAPI`
- **Actual human answer**
  - `Direct answer (grounded): strongest API base-class signal in current evidence is AbstractAPI ...`
  - then authority owner context (`APIServer`)
- **Why this now passes**
  - Structural direct-answer line is now preserved and surfaced first for class-relationship asks.
  - Base-class text is explicitly present in answer steps.

### 2) `ask_mail_server_configuration` (PASS)

- **Query**
  - `How does mail server configuration work?`
- **Expected**
  - text includes one of `MailServerConfiguration`, `AbstractAPI`, `mail`
  - policy: `generic_infra_ratio_top_k <= 0.6`
- **Actual human answer**
  - owner + method-specific line: `MailServerConfiguration ... beforeUpdate`
  - grounded explanation line references `AbstractAPI` in evidence excerpt
- **Why this now passes**
  - Retrieval top-k purity improved (`generic_infra_ratio_top_k = 0.5`).
  - Human answer was already good; now policy gate also passes.

### 3) `ask_config_store_organization` (PASS)

- **Query**
  - `How are config stores organized?`
- **Expected**
  - answer includes `AbstractConfigStore` or `ProtocolMapperConfigStore` or `com.mindarray.store`
- **Actual human answer**
  - owner line anchored on `AbstractConfigStore`
  - collaborator line includes store-class context
- **Why this passes**
  - Strong owner anchoring + acceptable retrieval purity + expected text anchors.

### 4) `ask_api_layer_architecture` (PASS)

- **Query**
  - `Explain the API layer architecture.`
- **Expected**
  - answer includes one of `AbstractAPI`, `APIServer`, `route`
- **Actual human answer**
  - owner line anchored on `APIServer`
  - architecture/domain notes retained
- **Why this passes**
  - Stable authority path and policy metrics; answer anchors satisfy scenario contract.

### 5) `ask_notification_handlers` (PASS)

- **Query**
  - `Find all classes that handle notifications.`
- **Expected**
  - includes one of `NotificationEngine`, `EmailNotification`, `SMSNotification`
- **Actual human answer**
  - owner line anchored on `NotificationEngine`
  - collaborator line carries handler classes (`emailnotification`, `smsnotification`)
- **Why this passes**
  - Text anchors and policy thresholds both satisfied (`generic_infra_ratio_top_k = 0.25`).

---

## How Exactly We Fixed Each Query

This section tracks *what changed in code* and *which scenario(s) it unblocked*.

### Fix A - strict answer-text validation (not path/snippet spillover)

- **What changed**
  - In verifier (`runtime/scripts/motadata_behavior_verify.py`), `text_contains_any` now checks answer text only (`plan_summary.steps` + `notes`), not file paths/snippet haystack.
- **Why it mattered**
  - Prevented false positives where expected words appeared only in evidence paths/snippets, not in human-facing answer.
- **Impact**
  - Made `ask_base_api_class` fail correctly when answer text was wrong; gave a clean signal to fix synthesis.

### Fix B - authority matching + registry coverage expansion

- **What changed**
  - Added/expanded authority concepts and aliases (API layer, mail server config, config store organization, notification handlers).
  - Improved token normalization (plural handling) in authority matching.
- **Why it mattered**
  - Ensured owner injection and concept resolution reliably activate for these ask queries.
- **Impact**
  - Stabilized owner anchoring across scenarios 2, 3, 4, 5.

### Fix C - preserve hard caps during restoration

- **What changed**
  - In Stage-B hard caps (`runtime/layer5/retrieval/fusion.py`), min-floor restoration no longer reintroduces rows that violate generic/distractor caps.
- **Why it mattered**
  - Previously, filtered generic rows could return through restore step and break policy thresholds again.
- **Impact**
  - Reduced recurrent policy failures on generic-infra ratio in ask scenarios.

### Fix D - keep `general` ask retrieval in ASK mode

- **What changed**
  - `resolve_lexical_task_type` adjusted so authority-anchored general asks stay in `ASK` mode (instead of `CODE`).
- **Why it mattered**
  - `ASK` mode enables ask-broad generic cap behavior during fusion.
- **Impact**
  - Improved purity for scenario 2 and generally lowered generic infra passengers for ask slices.

### Fix E - preserve structural direct answer when authority exists

- **What changed**
  - In `merge_plan_with_authority` (`runtime/ask_service/authority_synthesis.py`), structural direct-answer step is preserved first for class-relationship asks, then authority steps are appended.
- **Why it mattered**
  - Authority-owner summary was overshadowing semantic class-relationship answer.
- **Impact**
  - Unblocked scenario 1 by making the base-class response explicit.

### Fix F - targeted broad-cap tuning by ask subtype

- **What changed**
  - In fusion:
    - owner-anchored broad asks now use stricter generic passenger cap,
    - class-relationship API asks skip this tightening to keep needed API declaration evidence.
- **Why it mattered**
  - Scenario 2 needed fewer generic passengers;
  - scenario 1 needed preserved API declaration context.
- **Impact**
  - Brought both scenario 1 and 2 to pass simultaneously.

---

## Final Outcomes by Scenario (Fix Mapping)

| Scenario | Primary blocker before | Primary fix(es) that resolved it |
|---|---|---|
| `ask_base_api_class` | Wrong human answer semantics (`AbstractVerticle`) | Fix E + Fix F (+ strict verifier from Fix A to expose issue) |
| `ask_mail_server_configuration` | Generic infra ratio too high | Fix C + Fix D + Fix F |
| `ask_config_store_organization` | Earlier drift/anchoring instability | Fix B + Fix C |
| `ask_api_layer_architecture` | Needed stable API anchoring with policy compliance | Fix B + Fix D |
| `ask_notification_handlers` | Earlier generic passenger pressure and handler anchoring gaps | Fix B + Fix C + Fix D |

---

## Important note for manual review

Even with all-pass status, manual reviewers should still prioritize:
- the actual `plan_summary.steps` as the end-user answer,
- and not just metric compliance.

This run now has both:
- contract pass across all 5 asks,
- and human-facing answer lines aligned with expected intent anchors.

---

## Combined Ask + Debug Scorecard (Latest Runs)

Purpose: one quick view of practical usefulness across the latest deep slices.

Legend:
- **Strong pass** = contract/depth pass and answer is concretely grounded.
- **Acceptable pass** = contract/depth pass but still partly neighborhood-level.
- **Still shallow** = pass with explicit insufficiency or limited direct method trace.

| Scenario | Capability | Latest status | Practical depth verdict | Why |
|---|---|---|---|---|
| `ask_base_api_class` | Ask | PASS | **Strong pass** | Direct structural answer preserved (`AbstractAPI`) and authority context appended without overriding core answer. |
| `ask_mail_server_configuration` | Ask | PASS | **Strong pass** | Owner + method-anchored narrative with policy gates green. |
| `ask_config_store_organization` | Ask | PASS | **Strong pass** | Store architecture answer remains symbol/file grounded. |
| `ask_api_layer_architecture` | Ask | PASS | **Strong pass** | API layer explanation anchored to `APIServer` / route architecture context. |
| `ask_notification_handlers` | Ask | PASS | **Strong pass** | Handler-class discovery answer remains domain-grounded and non-generic. |
| `debug_availability_correlation_flow` | Debug | PASS (contract + depth) | **Strong pass** | Branch-level behavior and selected-file cues are explicit and practically useful. |
| `debug_mail_config_update_path` | Debug | PASS (contract + depth) | **Acceptable pass** | Honest and anchored, but still indicates missing direct update-hook body in retrieved snippet. |
| `debug_config_store_null_path` | Debug | PASS (contract + depth) | **Acceptable pass** | Good null/branch framing, but relies partly on caller context rather than exact target body. |
| `debug_snmp_trap_processing` | Debug | PASS (contract + depth) | **Acceptable pass** | Correct subsystem anchoring with guarded language; still limited direct parse/dispatch body trace. |
| `debug_missing_selected_file` | Debug | PASS (contract + depth) | **Strong pass** | Ideal truthful insufficiency behavior (`missing_in_context`) with no fabricated root cause. |

### Operator reading

- Ask capability is currently in a healthy **strong-pass** state for this 5-scenario slice.
- Debug capability is now governance-strong and depth-checked, but method-body retrieval remains the key limiter for three scenarios.

---

## Ask v1 Proof Density Patch (Method-window + Path Stitch)

Status: implemented after Ask-path caveat review.

### What was added

- **Method-claim alignment guard**
  - Keep class/file owner anchors deterministic.
  - Only claim `method X` as visible when owner snippet content actually contains that method token/declaration.
  - Expose `method_claim_alignment_pass` metadata for verifier/dev snapshots.

- **Method-window enrichment**
  - For "how it works" asks, prefer a compact method-window excerpt around the owner method over generic class excerpt.
  - Expose `method_window_visible` metadata.

- **Execution-path stitching**
  - Build a deterministic path line from `entry_trace.path` + owner class/method + `control_flow`.
  - Output as: `Execution-path stitch: ...` (bounded hops).

### Why this matters

- Keeps Ask answers **owner-correct** while increasing **mechanistic proof density**.
- Reduces shallow class-level narration when method evidence is available.
- Gives operators explicit call/flow chains without requiring EXPLAIN_DEBUG mode.

### Remaining caveat

- If top snippets still do not expose method bodies, Ask remains intentionally conservative.
- Deep branch-level analysis remains a Debug-path strength; Ask is now "owner + stitched flow" rather than full branch tracer.

