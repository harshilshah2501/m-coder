## Repository Constitution

This document defines the **structural governance** of this repository. It is intentionally concise and focuses on boundaries, not implementation details.

### 1. Structural Layers

- **Governance**: `governance/**`  
  - Golden Exemplars (Phases, schemas, validation ledgers, reachability/surfaces, closure declarations).  
  - Review packages and formal decision records.

- **Platform**: `ml/**` and `runtime/**`  
  - `ml/**` – model training, datasets, evaluation, and supporting scripts.  
  - `runtime/**` – RAG API, orchestrator, deployment/runtime configuration.

- **Documentation**: `docs/**`  
  - Narrative documentation, guides, architecture, status.  
  - **No governance YAML** is stored under `docs/`.

- **Archive**: `archive/**`  
  - Historical material (docs, evaluations, training artifacts, OKRs, sessions).  
  - Append-only, not used by production/runtime or training logic.

### 2. Golden Exemplars Sovereignty

- Single source of truth for Golden Exemplars:  
  - `governance/golden-exemplars/**`
- No canonical exemplar content may live outside `governance/golden-exemplars/**`.
- Derived/consumed views (e.g. for training or evaluation) are treated as **build artifacts**, never as authoring locations.

### 3. Exemplar Consumption Contract

- Training and evaluation **must not** read exemplars directly from governance paths at runtime.  
- Instead, they consume a **mirror** under:

  - `ml/training/_build/exemplars/**`

- The mirror is:
  - **Regenerated** via a dedicated script (see `ml/scripts/prepare_exemplars.sh`).  
  - **Git-ignored** (except for optional manifest/checksum files).  
  - Treated as **read-only** by training and evaluation code.

### 4. Documentation Boundaries

- `docs/**` contains:
  - Architecture overviews.  
  - How-to guides and quick references.  
  - Status and progress reports.
- `docs/**` must **not** contain governance YAML files (schemas, validation ledgers, reachability/surface definitions, closure declarations).
- Documentation may link to governance and archive locations but must not duplicate governance artifacts.

### 5. Archive Policy

- Single canonical historical root:

  - `archive/`

- Recommended substructure:
  - `archive/docs/` – archived documentation.  
  - `archive/evaluation/` – archived evaluation reports and runs.  
  - `archive/training/` – archived training artifacts and logs.  
  - `archive/okr/` – OKR and tracking material.  
  - `archive/sessions/` – session summaries and progress logs.

- Archive behavior:
  - Archive contents are **not** read by production/runtime or training pipelines.  
  - Archive is excluded from CI checks except for integrity/structure (e.g. no nested `archive/` inside `archive/`).  
  - Archive is append-only; edits and deletions are exceptional and should be documented.

### 6. Change Control

- Structural changes (moving directories across layers, introducing new top-level namespaces, or changing exemplar consumption paths) must:
  - Update this constitution when boundaries or invariants change.  
  - Pass CI guardrails:
    - No governance YAML under `docs/`.  
    - No authored exemplar Phases tree under `ml/training/sft/exemplars/Phases/**`.  
    - No nested `archive/` directories under `archive/`.
- Golden Exemplars and governance schemas are treated as **constitutional artifacts**; changes to them require careful review.

