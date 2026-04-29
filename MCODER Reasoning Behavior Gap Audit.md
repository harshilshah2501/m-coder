# MCODER Reasoning Behavior Gap Audit

Date: 2026-04-28

Scope: read-only engineering audit of the current Ask behavior path, with this report as the only produced artifact.

## Executive Diagnosis

**Key conclusion.** Reasoning is lost mainly *after* retrieval, along the plan-only response, composition, and CLI rendering path—not because anchors are missing. General `mcoder prompt` does not use the vLLM narrator; it chains deterministic `PlanOnlyPlanner` steps and thin CLI `answer_shaping`, while `graph_traversal` is optional, cache-dependent, and currently too narrow for full architectural narrative.

The Ask path still treats answers as **governed inspection plans** rather than **developer explanations**. Governance (`PLAN_ONLY`, `execution=false`, no tools) does not require thin or generic prose; the gap is the absence of a read-only **bounded narrator/composer** for normal Ask. The intended direction is: `evidence + authority + graph → structured answer → fluent human rendering`, without weakening posture, without schema-breaking removal of `plan_summary` initially, and without retrieval-ranking changes as a first lever.

The main reasoning loss is not in first-pass retrieval ranking. The current path usually has enough anchors to name owners and nearby files, and the new CIG / `graph_traversal` path can add structural context when artifacts are present. The loss happens later: the general `mcoder prompt` path is still a plan-only deterministic planner plus a thin CLI answer shaper. It does not invoke the vLLM narrator for general Ask, does not use the richer `assist_layer.assist_v2` blocks for CLI rendering, and only prints `answer_1` plus `next_step`.

The biggest root cause is a mismatch between response contract and desired product behavior:

- Backend contract remains `plan_only_response.v0.1` with `plan_summary.steps`.
- General Ask uses `PlanOnlyPlanner`, whose native output is inspection guidance, not fluent architectural explanation.
- CLI `shape_prompt_summary()` tries to reconstruct an answer from plan steps and optional graph fields.
- `graph_traversal` is optional, silently absent when GPU-side cache artifacts are missing, and currently omits several edge families that the graph builder already creates.

This means correct anchors can be retrieved but useful developer reasoning is compressed into one or two cautious lines.

## Ask Path Call Graph

```text
CLI
  runtime/mcoder_cli/cli.py
  _cmd_prompt()
    -> _run_ask_like(task_type="general")
      -> POST Context Layer /v1/export_evidence

Context Layer
  runtime/context_layer_service/app.py
  ContextLayerHandler.do_POST()
    -> export_evidence_bundle_dict()

Evidence Export
  runtime/context_layer_service/evidence_api.py
  export_evidence_bundle_dict()
    -> WorkspaceResolver.resolve()
    -> build_file_index()
    -> optionally build/create authority code index adapter
    -> build_authority_resolution()
    -> retrieve_lexical()
    -> fuse_and_filter() or hard_filter_only()
    -> assess_evidence_quality()
    -> build_evidence_bundle()
    -> returns layer5.evidence_bundle.v1

CLI
  _run_ask_like()
    -> POST Plan-Gate /v1/ask with evidence_bundle

Plan-Gate
  runtime/plan_gate_service/app.py
  PlanGateHandler.do_POST("/v1/ask")
    -> validate_ask_v1_request()
    -> _apply_assist_to_ask_payload()
    -> handle_ask_v1_request()

Ask v1
  runtime/ask_service/v1_ingest.py
  handle_ask_v1_request()
    -> validate_evidence_bundle_dict()
    -> context_bundle_from_evidence_dict()
    -> apply_dirty_buffer_overlay()
    -> apply_context_budget_for_surface()
    -> assess_evidence_quality()
    -> prioritize_owner_in_bundle()
    -> if EXPLAIN_DEBUG with selected file:
         explain_debug() via vLLM-compatible /v1/chat/completions
       else:
         PlanOnlyPlanner.plan()
           -> synthesize_authority_plan_steps()
           -> merge_plan_with_authority()
    -> build_graph_traversal_payload()
    -> _build_plan_only_response()

Graph traversal payload
  runtime/ask_service/graph_traversal_payload.py
  build_graph_traversal_payload()
    -> load_graph_artifacts(runtime/.cache/code_intelligence_graph)
    -> validate_graph_integrity()
    -> get_inheritance_chain()
    -> get_entrypoint_flow()
    -> get_call_chain()
    -> get_concept_owners()
    -> _expand_graph_context()

CLI human summary
  runtime/mcoder_cli/cli.py
  _run_ask_like()
    -> shape_prompt_summary(query, response)
       runtime/mcoder_cli/answer_shaping.py
       -> _compose_with_graph() if graph_traversal exists
       -> fallback plan_summary shaping
    -> print answer_1 and next_step
```

## Key Files And Functions

| Area | File | Functions |
|---|---|---|
| CLI command entry | `runtime/mcoder_cli/cli.py` | `_cmd_prompt`, `_run_ask_like`, `build_parser` |
| CLI summary rendering | `runtime/mcoder_cli/cli.py` | `_run_ask_like` printing block |
| CLI answer shaping | `runtime/mcoder_cli/answer_shaping.py` | `shape_prompt_summary`, `_compose_with_graph`, `_narrative_explain`, `_bounded_inference_explain`, `_extract_classes_from_context` |
| Context Layer HTTP | `runtime/context_layer_service/app.py` | `ContextLayerHandler.do_POST`, `_effective_export_workspace` |
| Evidence export | `runtime/context_layer_service/evidence_api.py` | `export_evidence_bundle_dict`, `detect_selected_method_grounding` |
| Ask v1 ingestion | `runtime/ask_service/v1_ingest.py` | `handle_ask_v1_request`, `validate_ask_v1_request` |
| Ask v0 legacy path | `runtime/ask_service/handlers.py` | `handle_ask_request`, `_build_plan_only_response` |
| Ask response construction | `runtime/ask_service/handlers.py` | `_build_plan_only_response` |
| Deterministic planner | `runtime/ask_service/planner.py` | `PlanOnlyPlanner.plan`, `_plan_generic`, `_class_relationship_answer_step` |
| Authority plan synthesis | `runtime/ask_service/authority_synthesis.py` | `synthesize_authority_plan_steps`, `merge_plan_with_authority`, `prioritize_owner_in_bundle` |
| Graph payload construction | `runtime/ask_service/graph_traversal_payload.py` | `build_graph_traversal_payload`, `_expand_graph_context`, `_select_concept_id` |
| Graph builder | `runtime/layer5/graph/builder.py` | `GraphBuilder.build`, `_add_config_store_edges`, `_extract_eventbus_edges`, `_apply_registry_overlay` |
| Graph traversal | `runtime/layer5/graph/traversal.py` | `get_inheritance_chain`, `get_call_chain`, `get_entrypoint_flow`, `get_concept_owners` |
| Graph storage | `runtime/layer5/graph/storage.py` | `load_graph_artifacts`, `write_graph_artifacts` |
| CIG build script | `runtime/scripts/build_code_intelligence_graph.py` | `main` |
| Plan-Gate HTTP | `runtime/plan_gate_service/app.py` | `PlanGateHandler.do_POST`, `_apply_assist_to_ask_payload` |
| Model reasoner | `runtime/ask_service/reasoner.py` | `explain_debug`, `_build_prompt`, `_ensure_selected_grounding` |
| Assist v2 structured shell | `runtime/assist_layer/v2_router.py` | `augment_assist_v2_with_response`, `_build_answer_block`, `_build_evidence_block`, `_build_gaps_block` |

## Intended Vs Actual Behavior

### "Explain the API layer architecture."

Intended:
- Explain API entrypoint responsibility, base abstraction, concrete API classes/handlers, and delegation flow.
- Separate server/route bootstrap from API base abstraction and concrete extensions.
- Avoid collapsing to only `APIServer.start`.

Actual source-inferred behavior:
- If CIG artifacts exist and `authority_resolution` resolves `APIServer.start`, `graph_traversal` may include `flow_paths`, inheritance, collaborators, and expanded nodes.
- If graph payload is missing or shallow, `answer_shaping` falls back to owner-centric wording like `APIServer.start` as the main anchor plus an inspection next step.
- The CLI prints only `answer_1` and `next_step`; it does not render evidence, gaps, role separation, or `assist_layer.assist_v2`.

Likely loss point:
- `graph_traversal` optionality and shallow `answer_shaping` composition, not retrieval ranking.

### "How does mail server configuration work?"

Intended:
- Explain `MailServerConfiguration.beforeUpdate` as update lifecycle.
- Include validation/persistence path and store/notification collaborators when evidence supports them.
- Preserve bounded confidence without becoming timid.

Actual source-inferred behavior:
- Authority synthesis can produce a strong primary owner line and a "How it works (grounded)" line.
- CLI strips raw method-window text and usually reports only the owner method plus an inspection step.
- Graph payload can help only if artifacts exist and route hint resolves; `call_paths` are only requested for debug/why, not general "how" asks.
- Store edges are created by `GraphBuilder`, but current traversal/payload/shaper paths do not directly exploit `READS_FROM` / `WRITES_TO`.

Likely loss point:
- Graph payload construction and composer do not turn available store/config edges into explanation for general Ask.

### "Find all classes that handle notifications."

Intended:
- Return a list of relevant classes.
- Separate primary owner from collaborators.
- Avoid treating collaborators as alternative owners.

Actual source-inferred behavior:
- Discovery intent can use concept ownership if `_select_concept_id()` resolves `notification_dispatch`.
- The graph composer returns `primary owners` and `collaborators` when `graph_traversal` is present.
- Without graph payload, fallback extracts class names from `context_bundle.files`, capped to five, and filters by path/name containing `notification`.
- This is better than single-owner collapse but may miss classes whose role is notification-adjacent without `notification` in path/name.

Likely loss point:
- Concept coverage and graph availability, with secondary loss in fallback class extraction.

### "How are config stores organized?"

Intended:
- Explain `AbstractConfigStore` as shared abstraction.
- Describe concrete stores, read/write relationships, lookup helpers, and organization by shared behavior vs domain-specific implementations.

Actual source-inferred behavior:
- Builder creates config-store relation edges from call edges (`READS_FROM`, `WRITES_TO`).
- Traversal payload does not request or expose these edge families.
- General "how" asks do not call `get_call_chain()` unless classified debug/why.
- The shaper can describe "shared abstraction" from owners/collaborators, but may invent a generic read/write line from sparse data rather than a real store-edge traversal.

Likely loss point:
- Graph traversal payload construction and answer composer, not CIG builder.

## Failure Analysis

### 1. Retrieval

Retrieval is not the first thing to change. Evidence export already builds lexical hits, authority resolution, fusion diagnostics, quality metadata, and evidence bundles. The prompt-specific symptoms are anchor-level rather than missing-evidence-only: the system often knows the owner but cannot articulate surrounding architecture.

Do not change retrieval ranking yet.

### 2. Evidence Bundle

The evidence bundle is useful but answer-limited:

- It carries entries, snippets, roles, authority resolution, structural context, and diagnostics.
- Ask v1 converts it into a `ContextBundle`.
- The human CLI rendering does not show most of this rich bundle unless `--json` is used.

Secondary issue: context budget and snippet selection may hide method bodies, but that is not the dominant architecture-answer problem for these four prompts.

### 3. Graph Payload Construction

This is a major loss point.

- `build_graph_traversal_payload()` reads only `runtime/.cache/code_intelligence_graph` on the Plan-Gate host.
- Missing or invalid graph artifacts return `None` silently.
- The current checkout has no `runtime/.cache/code_intelligence_graph` directory, so the default local behavior omits graph traversal.
- The split setup guide explicitly requires building CIG where Motadata is readable and syncing it to GPU runtime cache.
- Payload selection starts from authority owner / selected file, so broad architecture questions can become owner-local.
- `_select_concept_id()` handles notification/mail/api concepts, but concept owners are only fetched for discovery queries or notification queries. API/mail/config architecture asks do not consistently get concept overlay context.
- `_expand_graph_context()` ignores several useful edge types already emitted by `GraphBuilder`: `READS_FROM`, `WRITES_TO`, `PUBLISHES_TO`, `CONSUMES_FROM`, `AFFECTS`, `HANDLES`, `OVERRIDES`, `API_CLASS_EXTENDS`.

### 4. Traversal Depth And Edge Semantics

The traversal helpers are intentionally small:

- `get_call_chain()` follows only `CALLS` for three hops.
- `get_entrypoint_flow()` follows `ENTRYPOINT_INVOKES` or `REGISTERS_ROUTE`, not continued `CALLS`, store, event, or concept edges.
- `get_concept_owners()` returns owner/collaborator lists only, not why/how relationships.

This is safe but too thin for developer reasoning.

### 5. Answer Shaping Composer

This is the largest direct user-facing loss point.

- `shape_prompt_summary()` is a CLI-side adapter, not a full answer composer.
- It consumes `graph_traversal` if present, otherwise plan steps.
- It emits only `answer_1`, `next_step`, and `answer_shape`.
- It uses broad heuristic intent detection by substring.
- It overuses cautious phrases such as "appears", "current evidence", "partial graph coverage".
- It sometimes generates reasonable prose from labels, but not from a typed, evidence-cited explanation model.
- It does not render owner/collaborator/evidence/gap sections even though `assist_layer.assist_v2` builds some of them.

### 6. Plan-Gate Response Contract

The response is still shaped around plan-only governance:

- `_build_plan_only_response()` emits `plan_summary.steps`, `context_bundle`, `metadata`, `ui`, optional `graph_traversal`, optional extensions.
- It does not have a first-class `answer` block in the top-level response.
- `assist_layer.assist_v2` is attached by Plan-Gate, but marked diagnostics-only and not used by CLI rendering.

Governance posture is correct and should not be weakened. The issue is that governed Ask needs a richer read-only answer surface inside the safe response.

### 7. Model / vLLM Prompt

The vLLM reasoner is not invoked for normal `mcoder prompt` Ask. It is only used for `EXPLAIN_DEBUG` with selected file/selection.

For general architecture or flow questions, the model is not the current bottleneck because it is not in the path. Upgrading model or adding embeddings would not fix `mcoder prompt` until the response contract/composer actually asks for and renders richer explanations.

### 8. CLI Rendering

CLI rendering is a major final compression point:

- It prints request metadata and quality.
- For non-debug asks, it prints only `answer_1` and `next_step`.
- It ignores `plan_summary.notes`, `ui.message`, `assist_layer.assist_v2.answer`, `assist_layer.assist_v2.evidence`, `assist_layer.assist_v2.gaps`, raw `graph_traversal`, and evidence snippets.
- It can make a richer backend response look shallow.

## Root Cause

The system still treats Ask as "plan-only steps plus optional diagnostics" and relies on a thin CLI-side heuristic shaper to convert those steps into an answer. Correct retrieval anchors and optional graph facts are not being composed into a first-class answer object with role separation, causal flow, evidence citations, and confidence limits.

## Secondary Causes

- CIG artifacts are deploy-time side artifacts, not self-describing in the response when absent.
- `graph_traversal` silently disappears when artifacts are unavailable.
- Graph payload uses only a narrow subset of graph edge types.
- General Ask does not use the model narrator.
- The Assist v2 answer/evidence/gaps blocks are attached but diagnostics-only and ignored by the CLI.
- Tests check anti-collapse snippets, but do not yet assert the full desired four-prompt acceptance bar end-to-end through CLI rendering.
- The current environment could not run focused tests because no `python`/`py` executable was available on PATH.

## What Not To Change

- Do not change retrieval ranking as the first fix.
- Do not weaken `PLAN_ONLY` governance or execution=false invariants.
- Do not change schemas first unless a first-class answer block is explicitly approved.
- Do not add embeddings as a first fix.
- Do not upgrade the model as a first fix.
- Do not make graph truth authoritative over repository/evidence truth.
- Do not route general Ask into unbounded agent behavior or tool execution.
- Do not remove authority owner/collaborator separation.

## Minimal Next Changes

### Necessary Now

1. Make graph availability explicit.

Acceptance criteria:
- When `graph_traversal` is absent, metadata or UI says whether CIG artifacts were missing, invalid, or produced no relevant traversal.
- CLI `mcoder prompt` shows this only as a concise diagnostic line in verbose mode or JSON, not as alarming user-facing noise.
- No schema break required; can use existing metadata if acceptable.

Suggested tests:

```bash
PYTHONPATH=. pytest -q runtime/tests/test_graph_traversal_payload.py runtime/tests/test_ask_v1_ingest.py
```

2. Extend graph payload traversal for already-built edge families.

Acceptance criteria:
- Config-store asks can surface `READS_FROM` / `WRITES_TO` relationships when present.
- Notification/mail asks can surface `AFFECTS` / `HANDLES` and eventbus edges when present.
- API architecture asks can include `API_CLASS_EXTENDS`, `OVERRIDES`, and concrete API classes when graph evidence supports them.
- No retrieval ranking change.
- No governance posture change.

Suggested tests:

```bash
PYTHONPATH=. pytest -q runtime/tests/test_code_intelligence_graph_v1.py runtime/tests/test_graph_traversal_payload.py
```

3. Promote answer composition to backend-owned structured output while preserving existing response.

Minimal version:
- Add an additive metadata or assist-layer block that composes `direct_answer`, `owner_anchor`, `collaborators`, `flow`, `evidence_limits`, and `next_inspection_targets`.
- Reuse `assist_layer.assist_v2` or graduate it from diagnostics-only for CLI consumption.
- Keep `plan_summary.steps` unchanged for compatibility.

Acceptance criteria:
- `mcoder prompt "Explain the API layer architecture."` mentions `APIServer`, `AbstractAPI`, and concrete handlers/extensions when graph evidence exists.
- `mcoder prompt "How does mail server configuration work?"` mentions `MailServerConfiguration.beforeUpdate`, lifecycle/persistence, and collaborators when available.
- `mcoder prompt "Find all classes that handle notifications."` separates primary owner from collaborators.
- `mcoder prompt "How are config stores organized?"` explains `AbstractConfigStore` and read/write/concrete store organization when available.

Suggested tests:

```bash
PYTHONPATH=. pytest -q runtime/tests/test_answer_shaping_pass_a.py
PYTHONPATH=. pytest -q runtime/tests/test_ask_v1_ingest.py
```

4. Update CLI rendering to use structured answer blocks before fallback `answer_shaping`.

Acceptance criteria:
- CLI still works with older Plan-Gate responses.
- If structured answer exists, CLI renders direct answer, flow/roles, confidence limits, and next step.
- If absent, current `shape_prompt_summary()` fallback remains.
- `--json` remains unchanged.

Suggested tests:

```bash
PYTHONPATH=. pytest -q runtime/tests/test_answer_shaping_pass_a.py
mcoder prompt "Explain the API layer architecture."
mcoder prompt "How does mail server configuration work?"
mcoder prompt "Find all classes that handle notifications."
mcoder prompt "How are config stores organized?"
```

### Good To Have Later

1. Add a bounded general Ask narrator.

Use the model only after deterministic evidence and graph composition have produced typed facts. The prompt should ask for fluent articulation over evidence, not new facts.

Acceptance criteria:
- Model output is constrained to provided facts.
- Deterministic answer remains available if vLLM is down.
- Confidence limits cite missing graph/evidence edges.

2. Add end-to-end scenario snapshots for the four target prompts.

Acceptance criteria:
- Capture full Context Layer export, `/v1/ask` JSON, CLI human output, and graph artifact hash.
- Assertions check useful reasoning, not just anchor presence.

3. Improve graph concept coverage.

Acceptance criteria:
- API, mail, notification, config-store, eventbus, and scheduler concepts have explicit owners/collaborators in registry overlay.
- Broad architecture asks can seed concept traversal, not just owner-local traversal.

4. Add a deployment readiness check for CIG.

Acceptance criteria:
- `mcoder doctor` or `mcoder stack check --json` reports whether Plan-Gate has CIG artifacts.
- Split WSL/GPU topology can verify cache sync before prompt testing.

### Do Not Do / Likely Harmful

- Do not tune lexical ranking to compensate for weak composition.
- Do not stuff larger snippets into the prompt as the first fix.
- Do not replace deterministic authority with model inference.
- Do not make CIG required for all Ask responses; preserve graceful fallback.
- Do not introduce Neo4j as a source of truth; keep it only as an optional projection.
- Do not make normal Ask execute tools or cross governance boundaries.

## Recommended Agentic Task Sequence

### Task 1: CIG Presence And Diagnostics

Goal:
- Make graph artifact presence/absence observable in `/v1/ask` metadata and CLI diagnostics.

Files likely involved:
- `runtime/ask_service/graph_traversal_payload.py`
- `runtime/ask_service/v1_ingest.py`
- `runtime/ask_service/handlers.py`
- `runtime/mcoder_cli/cli.py`

Acceptance criteria:
- Missing graph cache is distinguishable from no relevant traversal.
- Existing response remains backward-compatible.
- Focused tests cover missing, invalid, and present graph artifacts.

### Task 2: Typed Graph Traversal Enrichment

Goal:
- Expose typed traversal facts for API, mail, notification, and config-store prompts using existing graph edges.

Files likely involved:
- `runtime/layer5/graph/traversal.py`
- `runtime/ask_service/graph_traversal_payload.py`
- `runtime/tests/test_graph_traversal_payload.py`

Acceptance criteria:
- Payload includes typed sections such as `store_edges`, `event_edges`, `lifecycle_methods`, or equivalent additive keys.
- Existing keys remain.
- The four prompts can receive enough graph facts for non-shallow composition.

### Task 3: Backend Answer Block

Goal:
- Build a first-class, additive answer block from evidence + authority + graph payload.

Files likely involved:
- `runtime/assist_layer/v2_router.py` or new ask-service composer module
- `runtime/ask_service/v1_ingest.py`
- `runtime/ask_service/handlers.py`

Acceptance criteria:
- Structured answer separates direct answer, primary owner, collaborators, flow, evidence limits, and next inspection target.
- No execution posture change.
- No schema-breaking removal of `plan_summary`.

### Task 4: CLI Renderer Upgrade

Goal:
- Render structured answer block before falling back to `shape_prompt_summary()`.

Files likely involved:
- `runtime/mcoder_cli/cli.py`
- `runtime/mcoder_cli/answer_shaping.py`
- `runtime/tests/test_answer_shaping_pass_a.py`

Acceptance criteria:
- Human CLI output has enough room for architecture/flow reasoning.
- Existing old responses still render.
- `--json` remains raw.

### Task 5: Four-Prompt E2E Acceptance Harness

Goal:
- Lock the desired behavior for the exact prompt set.

Files likely involved:
- `runtime/tests/` new or extended test
- `runtime/scripts/verify_ask_path.sh` or a new scenario runner
- `docs/guides/PASS_A_B_C_SETUP_VERIFICATION.md`

Acceptance criteria:
- Tests assert content-level requirements for all four prompts.
- Harness records whether graph traversal is present.
- Failure messages identify whether loss is retrieval, graph, composer, or CLI rendering.

## Suggested Test Commands

Focused unit tests:

```bash
PYTHONPATH=. pytest -q runtime/tests/test_answer_shaping_pass_a.py
PYTHONPATH=. pytest -q runtime/tests/test_graph_traversal_payload.py
PYTHONPATH=. pytest -q runtime/tests/test_ask_v1_ingest.py
```

CIG tests:

```bash
PYTHONPATH=. pytest -q runtime/tests/test_code_intelligence_graph_smoke.py runtime/tests/test_code_intelligence_graph_v1.py runtime/tests/test_build_code_intelligence_graph_script.py
```

Build graph artifacts:

```bash
python3 -m runtime.scripts.build_code_intelligence_graph \
  --workspace-root /root/Harshil-PoCs/Motadata \
  --out-dir runtime/.cache/code_intelligence_graph
```

Direct split-topology graph probe:

```bash
python3 - <<'PY'
import json, urllib.request, uuid, datetime
CTX="http://127.0.0.1:8091"
ASK="http://127.0.0.1:8089"
WS="/root/Harshil-PoCs/Motadata"
Q="How are config stores organized?"
def post(url, body):
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())
ev = post(f"{CTX}/v1/export_evidence", {"workspace_root":WS,"query":Q,"top_k":8,"task_type":"general"})
resp = post(f"{ASK}/v1/ask", {"schema_version":"ask_request.v1.0","request_id":str(uuid.uuid4()),"timestamp_utc":datetime.datetime.now(datetime.UTC).isoformat(),"query":Q,"task_type":"general","evidence_bundle":ev})
gt = resp.get("graph_traversal")
print("graph_traversal_present:", isinstance(gt, dict))
if isinstance(gt, dict):
    print("keys:", sorted(gt.keys()))
    print(json.dumps(gt, indent=2)[:4000])
PY
```

CLI acceptance prompts:

```bash
mcoder prompt "Explain the API layer architecture."
mcoder prompt "How does mail server configuration work?"
mcoder prompt "Find all classes that handle notifications."
mcoder prompt "How are config stores organized?"
```

Verification note for this audit:
- I attempted to run `python -m pytest runtime/tests/test_answer_shaping_pass_a.py runtime/tests/test_graph_traversal_payload.py -q`.
- On the machine used for this write-up, neither `python` nor `py` was available on `PATH` (the shell error varies by OS, e.g. command not found vs. “not recognized”).
- The diagnosis above is therefore source- and test-contract-based, not live-service-output-based.

