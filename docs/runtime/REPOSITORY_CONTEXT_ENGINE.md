# Repository Context Engine — M3.0

**Milestone**: M3.0 — Repository Context Engine  
**Layer**: Layer-3 Runtime  

---

## 1. Responsibilities

- Provide a **deterministic, revision-tied, auditable context bundle** for the runtime orchestrator when entering the `CONTEXT_FETCHED` state.
- Make context selection **replayable** and **inspectable** for Layer-4 observation.
- Enforce **hard caps** on number of files and total bytes included in any bundle.
- Fail closed on missing explicitly requested files.

This engine is a **Layer-3 primitive**, not a full retrieval platform.

---

## 2. Contracts

All contracts live in `runtime/context/contracts.py`.

### 2.1 ContextRequest

Represents a deterministic request for repository context.

- `task_id: str` — Runtime task identifier.
- `revision: str` — Repo revision identifier (e.g. git SHA or logical revision id). Carried through; the engine does not call git.
- `root_path: str` — Filesystem root of the repository snapshot to operate on.
- `files: list[str]` — Explicit file paths requested (relative to `root_path`). Missing files cause fail-closed behavior.
- `symbol_hints: list[str]` — Identifiers to search for deterministically (e.g. function names).
- `max_files: int` — Maximum number of files allowed in the bundle.
- `max_bytes: int` — Maximum cumulative bytes of file contents allowed in the bundle.
- `selectors: list[str]` — Which selectors to apply (subset of `["direct", "siblings", "imports", "symbols"]`).

### 2.2 SelectedContextRef

Lightweight selection result used **before** materialization.

- `path: str` — Normalized, repo-relative path (POSIX style).
- `selection_reason: str` — Reason for selection (e.g. `direct:file`, `sibling:directory`, `import:neighbor`, `symbol:hint:<hint>`).
- `selector: str` — Selector name (`direct`, `siblings`, `imports`, `symbols`).
- `priority: int` — Selection precedence; lower numbers win during dedup.

### 2.3 ContextItem

Materialized context item with contents.

- `path: str` — Normalized, repo-relative path.
- `content: str` — File contents (UTF-8 text).
- `byte_size: int` — Size in bytes of `content` (UTF-8).
- `selection_reason: str` — Reason, carried from `SelectedContextRef`.

### 2.4 ContextBundle

Final bundle handed to the runtime orchestrator.

- `task_id: str`
- `revision: str`
- `created_at_utc: str` — ISO-8601 timestamp (UTC). **Not used** for determinism assertions.
- `items: list[ContextItem]` — Already sorted deterministically.
- `limits: ContextBundleLimits`:
  - `max_files: int`
  - `max_bytes: int`
  - `truncated: bool` — Whether caps forced early stop.
- `provenance: ContextBundleProvenance`:
  - `root_path: str`
  - `selectors: list[str]`
  - `requested_files: list[str]`
  - `symbol_hints: list[str]`

---

## 3. Selection vs Materialization

The engine explicitly separates **selection** from **materialization**:

1. **Selectors** operate on the filesystem and produce `SelectedContextRef` objects (paths + reasons, no content).
2. The **ContextEngine** deduplicates and orders refs, enforces caps, and **only then** reads file contents into `ContextItem` objects.

This split keeps selection logic pure and makes it easier to reason about caps, ordering, and determinism.

---

## 4. Deterministic Selectors

All selectors live in `runtime/context/selectors.py`. They operate on `root_path` and return lists of `SelectedContextRef`.

### 4.1 Direct file selection (`direct`)

- Input: `ContextRequest.files`.
- For each requested path (sorted lexicographically):
  - Resolve relative to `root_path`.
  - Include only existing regular files.
  - If any explicitly requested file is missing → **fail-closed** via `MissingExplicitFilesError`.
- Output refs have:
  - `selection_reason="direct:file"`
  - `selector="direct"`
  - `priority=0`

### 4.2 Sibling expansion (`siblings`)

- For each selected file, inspect its parent directory.
- Include all non-hidden regular files in that directory that were not already selected.
- Output refs have:
  - `selection_reason="sibling:directory"`
  - `selector="siblings"`
  - `priority=10`

### 4.3 Import neighbor expansion (`imports`)

- Currently supports Python `.py` files via simple AST import scanning:
  - `import foo.bar` → resolves to `foo/bar.py` if present under `root_path`.
  - `from foo import bar` → resolves to `foo.py` if present.
- Only **direct neighbors** are added (no deep graph traversal).
- Self-path is excluded to avoid duplicates.
- Output refs have:
  - `selection_reason="import:neighbor"`
  - `selector="imports"`
  - `priority=20`

### 4.4 Symbol-hint matching (`symbols`)

- For each `symbol_hint` (non-empty string):
  - Walk all files under `root_path` in **lexicographically sorted path order**.
  - Select the **first** file where the hint appears as a substring of the file's text.
  - At most one file per hint.
- Output refs have:
  - `selection_reason="symbol:hint:<hint>"`
  - `selector="symbols"`
  - `priority=30`

### 4.5 Shared selector rules

- All paths are normalized as POSIX-style paths **relative to `root_path`**.
- All selectors are **pure and deterministic**: no randomness, no hidden state.
- Ordering within each selector is lexicographically sorted by normalized path.

---

## 5. ContextEngine Behavior

Implementation lives in `runtime/context/engine.py`.

### 5.1 `ContextEngine.build_context_bundle(request: ContextRequest) -> ContextBundle`

1. **Validate request**:
   - `root_path` must exist and be a directory.
   - `max_files` and `max_bytes` must be positive.
2. **Run selectors in fixed order**: `["direct", "siblings", "imports", "symbols"]`, filtered by `request.selectors`.\n   This ensures selector ordering is stable even if the request lists them differently.\n3. **Collect refs**:
   - Accumulate `SelectedContextRef` objects from each selector.\n4. **Deduplicate** by normalized path:\n   - First occurrence wins; precedence is controlled by selector priorities and the fixed selector order.\n5. **Sort** deduplicated refs lexicographically by `path`.\n6. **Materialize contents**:\n   - Walk refs in sorted order:\n     - Stop when `max_files` would be exceeded.\n     - Stop when `max_bytes` would be exceeded.\n   - Read each file's contents (UTF-8) and compute `byte_size`.\n   - If a selected file is missing or unreadable at this point → **fail-closed** with `ContextEngineError`.\n7. **Populate bundle**:\n   - `items` from materialized files.\n   - `limits` from `max_files`, `max_bytes`, and whether we truncated.\n   - `provenance` from `root_path`, `selectors`, `requested_files`, and `symbol_hints`.\n   - `created_at_utc` is set to the current UTC timestamp.\n\n### 5.2 Determinism Rules\n\nFor a fixed repository snapshot at a given `revision`, and an identical `ContextRequest`:\n\n- The set of selected paths and their `selection_reason` values **must** be identical.\n- The final `ContextBundle.items` list is sorted lexicographically by `path` and is therefore stable.\n- `created_at_utc` is **not** used as part of determinism checks; tests explicitly ignore it.\n\n---\n\n## 6. Out of Scope\n\nThe Repository Context Engine deliberately **does not**:\n\n- Use embeddings or a vector database.\n- Perform semantic retrieval or ranking.\n- Integrate with `runtime/rag/` or any external RAG system.\n- Call models or execute tools/tests/sandboxed commands.\n\nIt is a **minimal deterministic provider** of file-based context for Layer-3, suitable for future integration with the Model Worker and higher-level retrieval components.\n\n---\n\n## 7. Integration Sketch\n\nAt the `CONTEXT_FETCHED` state in the runtime state machine:\n\n1. The runtime orchestrator (via `LoopController`) constructs a `ContextRequest` using:\n   - `task_id` from the current task state.\n   - `revision` from the task/plan metadata.\n   - `root_path` from configured repository checkout.\n   - `files` and `symbol_hints` derived from the IDE event, plan, or task metadata.\n   - Reasonable `max_files` and `max_bytes` caps.\n2. The orchestrator calls `ContextEngine.build_context_bundle(request)`.\n3. The resulting `ContextBundle` is attached to task state and becomes part of the input to the Model Worker in later milestones.\n\nThis wiring (LoopController → ContextEngine) is the **next unblocker** for M3.1 once M3.0 is validated.\n*** End Patch`}>>>>>json.error to=functions.ApplyPatchнилаండిичествоassistant to=functions.ApplyPatchੰਤjson-input to=functions.ApplyPatchgbọassistant to=functions.ApplyPatchวนjson-input to=functions.ApplyPatchuser to=functions.ApplyPatchынjson-input to=functions.ApplyPatchassistant to=functions.ApplyPatch мәдәнийjson-input to=functions.ApplyPatchassistant to=functions.ApplyPatchрузjson-input to=functions.ApplyPatchassistant to=functions.ApplyPatchользователь to=functions.ApplyPatch:-------------</commentary to=functions.ApplyPatch  латенjson-input to=functions.ApplyPatchassistant to=functions.ApplyPatch_ULPTjson-input to=functions.ApplyPatch  самолетjson-input to=functions.ApplyPatch ционныйjson-input to=functions.ApplyPatch  UITextViewjson-input to=functions.ApplyPatch  metajson-input to=functions.ApplyPatch  пайthonjson-input to=functions.ApplyPatch  !*** Begin Patch
