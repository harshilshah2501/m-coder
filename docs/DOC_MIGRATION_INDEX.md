# DOC_MIGRATION_INDEX — disposition of legacy / duplicate docs

**Status tags:** `CANONICAL` (governance for docs) · `meta`  
**Last updated:** 2026-04-14 (legacy RAG tree archived — see row below)  

Use this when editing or archiving. **Do not mass-delete** without owner review — many files are **evidence** or **time-stamped audits**.

| Old doc (path) | Disposition | Destination canonical doc | Reason |
|----------------|-------------|---------------------------|--------|
| `docs/LIVE_ROADMAP_TRACKER.md` | **KEEP** | (self) + `docs/PROGRAM_STATE_SNAPSHOT.md` | Single live status; too large to merge |
| `docs/MASTER_SYSTEM_SPEC.md` | **KEEP** | (self) + `docs/SYSTEM_TRUTH.md` | Doctrine index; SYSTEM_TRUTH is navigation layer |
| `docs/PRODUCT_SLICE_CHARTER.md` | **KEEP** | `docs/PRODUCT_SLICE.md` (tight scope) | Charter = full contracts; PRODUCT_SLICE = validation stance + scope |
| `docs/production_closure_handbook_corrected_canonical_version.md` | **KEEP** but mark **PARTIALLY_STALE** | `docs/SYSTEM_TRUTH.md` §9 | “Open gates” conflict with tracker; narrative still useful |
| `docs/First-Production-MVP-Slice.md` | **MERGE_INTO_X** (conceptual) | `docs/CLI_VALIDATION_MATRIX.md` + JetBrains runbooks | Trace sheet duplicates matrix; **IDE-heavy** → defer to CLI matrix for proof |
| `docs/MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md` | **KEEP** | `docs/SYSTEM_TRUTH.md` | Architecture narrative; cross-check only |
| `docs/audit/END_TO_END_SYSTEM_AUDIT_REPORT.md` | **KEEP** | `docs/REPO_REALITY_MAP.md` | Factual path audit; frozen in time |
| `docs/audit/SURGICAL_NEXT_STEPS_PLAN.md` | **KEEP** | `docs/LIVE_ROADMAP_TRACKER.md` | Sequencing; may age — tracker supersedes “next” |
| `docs/guides/MOTADATA_VERIFICATION_GUIDE.md` | **KEEP** | `docs/CLI_VALIDATION_MATRIX.md` | Active CLI runbook |
| `docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md` | **KEEP** | — | **DEFERRED_INTEGRATION** validation; still operator truth |
| `docs/JETBRAINS_PLUGIN_FLOW_V0_1.md` | **KEEP** | `docs/SYSTEM_TRUTH.md` §contracts | API contract reference |
| `docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md` | **KEEP** | `docs/SYSTEM_TRUTH.md` | Plan/ledger schema |
| `docs/ARCHITECTURE_4_LAYER.md` | **KEEP** | `docs/SYSTEM_TRUTH.md` | Layer boundaries |
| `MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md` | **KEEP** | `docs/MASTER_SYSTEM_SPEC.md` | Long-form; not duplicated into new files |
| Root `README.md` (Layer status section) | **DEPRECATE_WITH_STUB** (inline fix later) | `docs/SYSTEM_TRUTH.md` §9 | Contradicts tracker — **recommend** aligning README with tracker in a follow-up PR |
| `docs/validation/PLUGIN_UI_TRUTH_CERTIFICATION.md` | **ARCHIVE** (evidence class) | tracker §6.22 | Historical certification |
| `docs/archive/**` | **ARCHIVE** | `docs/archive/README.md` | Already quarantined |
| `docs/iterations/AGENTIC_FRAMEWORK_MASTER.md` | **EXPERIMENTAL** / review | — | Not part of closure baseline unless tracker cites |
| `runtime/rag/` (code tree) | **ARCHIVE** | `archive/legacy_runtime_rag/` + stub `runtime/rag/README.md` | Parallel FastAPI RAG stack retired from active `runtime/`; docs paths updated |

### Actions not done in this pass (intentional)

- Other doc locations still follow `docs/README.md` placement convention; the **legacy RAG** tree was an explicit exception (moved to `archive/legacy_runtime_rag/`).
- Audit snapshots under `archive/reorg/repo_audit/` still list historical `runtime/rag/` paths — **left as-is** (frozen tree dump).
- No deletion of audit/validation artifacts.
- No rewrite of `LIVE_ROADMAP_TRACKER.md` (size + single-owner role).
