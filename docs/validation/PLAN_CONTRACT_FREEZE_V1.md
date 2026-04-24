# Plan Contract Freeze v1

Date: 2026-04-24  
Status: **specified — documentation freeze only** (no `plan_only_response` version bump in this lane; no runtime or schema file changes)  
Applies to: future **additive** Plan artifact on **`POST /v1/ask`** responses that already carry `plan_only_response.v0.1` (and existing `plan_summary`)  
Related discovery: `docs/validation/PLAN_CODE_REASONING_SOLIDIFICATION_DISCOVERY.md`

## 1) Scope and intent

This document freezes the **v1 vocabulary and shape** of a governed **Plan contract** object so that downstream work (Plan validation pack, HTTP gates, optional ingest) can proceed without ambiguity.

**Lane 1 delivers specification only:** no JSON Schema edits, no Plan-Gate HTTP behavior changes, no execute-path changes, no Stage 3 loop changes.

**Program intent:** “Plan first” — structured intent, scope, risk, evidence, and approval posture **before** any multi-step code reasoning or execution proposals are activated in product paths.

## 2) Additive-first compatibility (frozen policy)

### 2.1 What stays unchanged (v1 Ask / Plan-Only)

- Response continues to conform to **`plan_only_response.v0.1`** as today: required top-level fields including **`plan_summary`** with **`steps`** (and optional **`notes`**) remain the **canonical human-readable plan strip** for clients that already consume them.
- **`governance_posture`** remains **`PLAN_ONLY`** for this surface.
- **`execution`** remains **`false`** for this surface. This contract does **not** authorize execution; it describes planning posture and bounds only.

### 2.2 New material (specified, not yet wired)

- A single optional top-level object key: **`plan_contract`** (name frozen for v1 spec).
- When present, **`plan_contract`** MUST conform to **§4** below.
- Clients and validators that do not yet understand **`plan_contract`** MUST ignore unknown top-level keys **or** treat **`plan_contract`** as optional diagnostics — per JSON usual practice and existing additive patterns (e.g. Assist v2 under `assist_layer`).

### 2.3 Why not bump `plan_only_response` in Lane 1

- Bumping **`plan_only_response`** revision forces coordinated plugin + schema + validation churn.
- **Additive-first** allows a **documentation freeze** and **Lane 2 scenario design** before proving whether the existing schema’s `additionalProperties: false` blocks safe carriage of **`plan_contract`** in practice.

### 2.4 Criteria for when a **`plan_only_response` schema bump** becomes **required**

A schema revision (e.g. `plan_only_response.v0.2`) is **required** only when **Lane 1 follow-up discovery** (or implementers) establish at least one of the following:

1. **Hard rejection:** The authoritative `plan_only_response` JSON Schema (or equivalent validator) **cannot** be relaxed to allow **`plan_contract`** under the repo’s compatibility rules (e.g. `additionalProperties: false` at the response root with no allowance for the new key).
2. **Contract collision:** A field name or nesting choice for **`plan_contract`** would **conflict** with an existing required or optional property in `v0.1`, making additive placement impossible without rename.
3. **Size or typing limits:** `v0.1` constraints (e.g. string length, array caps) **prevent** encoding minimally valid **`plan_contract`** instances for the scenarios in **§6**.
4. **Consumer mandate:** A **documented** consumer (plugin, gateway, CI) **requires** schema-id equality to a single `schema_version` const and cannot accept optional extensions until the const is bumped.
5. **Security or audit bar:** Legal/compliance or internal audit requires **schema-enforced** presence of Plan bounds fields (not only documentation + server-side checks).

Until one of the above is **true**, the project stance remains: **additive `plan_contract` + keep `plan_only_response.v0.1` const** once schema files are updated in a later lane; if (1) blocks that, bump schema in that same lane.

## 3) Non-goals (this document)

- Does not define multi-step **code reasoning** trace shapes (separate contract, later lane).
- Does not change **Assist v2** (`assist_layer.assist_v2`) freeze semantics.
- Does not redefine **`/v0/plan`** `decision_response.v0.1` — that remains the **command/plan-request governance** surface; **`plan_contract`** here is the **Ask-time governed planning artifact** aligned with repo Ask path.

## 4) `plan_contract` object — frozen field set (v1)

When **`plan_contract`** is emitted (future lane), it MUST be an object with:

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `schema_version` | string | yes | Const: **`plan_contract.v1`** |
| `task_intent` | object | yes | **What** the user is trying to achieve in bounded language (see §4.1). |
| `affected_files` | array | yes | **Where** the plan may touch (see §4.2); may be empty only when §4.5 documents why (e.g. insufficient evidence). |
| `evidence_requirements` | object | yes | **What evidence** must exist or be gathered before proceeding (see §4.3). |
| `change_boundaries` | object | yes | **Scope limits** of allowed change (see §4.4). |
| `risk_class` | string | yes | **Risk tier** for the proposed work (see §4.5). |
| `allowed_actions` | array | yes | **Allowlist** of action categories permitted under this plan (see §4.6); may be empty when plan is refuse-only. |
| `forbidden_actions` | array | yes | **Denylist** of action categories that must not be proposed or executed under this plan (see §4.7). |
| `approval_posture` | string | yes | **Human/governance posture** for proceeding (see §4.8). |
| `confidence_limits` | object | yes | **What is known vs not known** about the plan itself (see §4.9). |

No other keys are **normative** in v1; optional keys may be added in **v2** only under additive policy.

### 4.1 `task_intent` (required object)

| Subfield | Type | Required | Meaning |
|----------|------|----------|---------|
| `summary` | string | yes | One short paragraph: user-visible intent, no code. |
| `kind` | string | yes | One of: **`explore`**, **`document`**, **`refactor`**, **`fix`**, **`config`**, **`test`**, **`other`** (closed enum for v1). |

### 4.2 `affected_files` (required array)

Items are objects:

| Subfield | Type | Required | Meaning |
|----------|------|----------|---------|
| `path` | string | yes | Repo-relative path using `/`. |
| `role` | string | yes | One of: **`primary`**, **`secondary`**, **`reference_only`** |

Empty array is allowed **only** when paired with **`risk_class: insufficient_evidence`** (see §4.5) or **`approval_posture: refuse`** with documented blocker in **`confidence_limits.requires_resolution`** (see §4.9).

### 4.3 `evidence_requirements` (required object)

| Subfield | Type | Required | Meaning |
|----------|------|----------|---------|
| `must_have` | array[string] | yes | Evidence types or artifacts that must be present (e.g. `owner_method_visible`, `graph_route_anchor`, `test_failure_log`). |
| `nice_to_have` | array[string] | yes | Optional; may be empty. |
| `insufficient_without` | array[string] | yes | If any of these are missing, plan must not proceed beyond advisory — often drives **`approval_posture`** / refusal. |

### 4.4 `change_boundaries` (required object)

| Subfield | Type | Required | Meaning |
|----------|------|----------|---------|
| `in_scope` | array[string] | yes | Bullet strings describing what may change. |
| `out_of_scope` | array[string] | yes | Bullet strings explicitly excluded. |
| `max_files_touched` | integer | yes | Upper bound of files the plan authorizes for a follow-on change proposal (≥ 0). `0` means no file changes authorized. |
| `max_diff_lines_hint` | integer | yes | Soft cap signal for reviewers/gates (≥ 0). |

### 4.5 `risk_class` (required string)

Closed enum for v1:

| Value | Use |
|-------|-----|
| `low` | Docs, comments, trivial renames with no behavior change. |
| `medium` | Small localized code or config changes with tests available. |
| `high` | Behavior-changing logic, security-sensitive paths, or broad refactors. |
| `critical` | Data loss, privilege, production infra, or irreversible operations. |
| `insufficient_evidence` | Plan cannot responsibly bound change — **must** pair with refusal or defer posture and explicit limits in **`confidence_limits`**. |

### 4.6 `allowed_actions` (required array of strings)

Closed vocabulary tokens (v1); each element MUST be one of:

- `read_repo`
- `propose_patch_text`
- `run_tests_local`
- `run_linter`
- `update_docs_only`
- `execute_shell`
- `privileged_write`
- `none`

**`forbidden_actions`** MUST use the same token universe (so reviewers can require “no `execute_shell` / no `privileged_write`” explicitly). Extending the vocabulary requires **`plan_contract.v2`** (separate freeze).

### 4.7 `forbidden_actions` (required array of strings)

Uses the **same closed token list** as **`allowed_actions`** (§4.6). Typical patterns: forbid `execute_shell` and `privileged_write` for advisory-only plans; forbid `propose_patch_text` when only exploration is allowed; forbid `run_tests_local` when no sandbox is available. Duplicates discouraged; validators may normalize.

### 4.8 `approval_posture` (required string)

Closed enum for v1 (Ask-time planning semantics, not a substitute for **`PlanGateService`** execute postures):

| Value | Meaning |
|-------|---------|
| `advisory_only` | Informational plan; no automatic follow-on. |
| `requires_human_approval` | Bounded change may be proposed only after explicit human sign-off (product workflow). |
| `defer` | More evidence or narrower scope needed before any change proposal. |
| `refuse` | No safe plan; do not propose changes. |

These values **describe the plan artifact**. **`POST /v0/execute`** and **`PlanGateService`** remain authoritative for **execution** gating.

### 4.9 `confidence_limits` (required object)

| Subfield | Type | Required | Meaning |
|----------|------|----------|---------|
| `known` | array[string] | yes | What the plan asserts with adequate support. |
| `unknown` | array[string] | yes | What remains uncertain. |
| `requires_resolution` | array[string] | yes | Blockers that must be cleared (evidence, scope, or policy); may be empty. |

## 5) Relationship to existing `plan_summary`

- **`plan_summary.steps`**: ordered human-readable steps; **retained**; not replaced by **`plan_contract`**.
- **`plan_summary.notes`**: optional caveats; **retained**.
- **`plan_contract`**: machine- and reviewer-friendly **governed** view (intent, files, risk, bounds, allow/deny, approval, confidence). Future ingest may **derive** `plan_contract` from internal evidence and governance state; v1 freeze does not mandate a single producer.

## 6) Validation expectations (Lane 2 — implemented as offline fixtures)

The **Plan validation pack** proves the contract **without** wiring `plan_contract` into **`POST /v1/ask`** yet:

| Scenario class | Expectation (informal) |
|----------------|-------------------------|
| **Safe plan** | `risk_class` in `{low, medium}` with narrow `change_boundaries`, `allowed_actions` consistent with intent, `forbidden_actions` includes destructive tokens as appropriate, `approval_posture` not `refuse`. |
| **Risky plan** | `risk_class` `high` or `critical` with explicit `requires_human_approval` or `defer`, and `forbidden_actions` excluding unsafe acts until approval. |
| **Insufficient evidence** | `risk_class: insufficient_evidence` and/or non-empty **`confidence_limits.requires_resolution`**, `affected_files` empty or reference-only, **`allowed_actions`** typically `none` or `read_repo` only. |
| **Privileged / destructive refusal** | `approval_posture: refuse` with explicit **`requires_resolution`** and **`forbidden_actions`** covering patch/execution tokens; `max_files_touched: 0`. |

**Mechanism:**

- Scenarios in `docs/validation/motadata_aiops_behavior_scenarios.v1.json` use capability **`plan_contract_validate`**, embedded **`plan_contract_fixture`**, and **`expect.plan_contract_category`** (`safe_plan` \| `risky_plan` \| `insufficient_evidence` \| `destructive_refusal`).
- `runtime/plan_contract/v1_validate.py` implements **`validate_plan_contract_v1`** (structural) and **`validate_plan_contract_category`** (semantic).
- `runtime/scripts/motadata_behavior_verify.py` runs these rows **without HTTP**; when **all** selected scenarios are `plan_contract_validate`, **graph preflight UNREACHABLE does not abort** the suite (offline-only runs).

**Example (graph optional):**

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --scenarios-only \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --scenario-id plan_contract_v1_safe_documentation \
  --scenario-id plan_contract_v1_risky_behavior_change \
  --scenario-id plan_contract_v1_insufficient_evidence \
  --scenario-id plan_contract_v1_privileged_destructive_refusal \
  --workspace-root /abs/path/to/Motadata \
  --print concise
```

Exact JSON fixtures and verifier assertions are **in scope** for Lane 2 as above; **`/v1/ask` emission** of `plan_contract` remains a later lane gated by schema/additive policy.

## 7) Explicit execution semantics (unchanged)

- **`plan_contract`** does not set **`execution`** to true and does not imply **`safe_execute`** from Plan-Gate.
- Any future code proposal or execute request MUST remain subject to existing **Plan-Gate**, **execute handler**, and **ledger** rules.

## 8) Next slice (after Lane 1)

Per program sequencing: **Plan validation pack** (scenarios + verifier expectations wired to **`motadata_behavior_verify`** or dedicated tests) — **not** multi-step code reasoning contract or HTTP Code gate until Plan contract validation is in motion.
