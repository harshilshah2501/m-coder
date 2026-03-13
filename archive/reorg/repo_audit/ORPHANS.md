# Orphan and Suspicious Files

Files that appear unreferenced, superseded, or outside canonical layer directories.

---

## Criteria

- `referenced_by_other_files` = no (from DOC_INDEX)
- Name contains: `draft`, `copy`, `old`, `backup`, `tmp`
- Outside: `governance/`, `ml/`, `runtime/`, `observation/`, `docs/`, `scripts/`, `artifacts/`
- Lower version when higher exists (e.g., v1.5 when v1.7 is canonical)

---

## Unreferenced / Low-Reference Docs

| path | orphan_reason | suggested_action | risk |
|------|---------------|------------------|------|
| archive/okr/supporting-docs/EXEMPLAR_AUTHORING_GUIDE.md | unreferenced, in archive | keep in archive | low |
| archive/docs/Introspection.md | unreferenced | keep in archive | low |
| archive/docs/EVALUATION_REPORT.txt | unreferenced | keep in archive | low |
| archive/docs/FUNCTIONAL_TEST_REPORT.txt | unreferenced | keep in archive | low |
| archive/docs/reorganization_plan.txt | unreferenced | keep in archive | low |
| chat-*.txt (root) | session log | misc_orphans or delete | low |
| Hardware-Profile.md | low refs | keep (misc) | low |
| GREG_Pre-Review_Attack_Result.md | low refs | keep (governance-related) | medium |

---

## Potentially Superseded Versions

| path | superseded_by | suggested_action | risk |
|------|---------------|------------------|------|
| ml/training/sft/exemplars/guides/Golden_Exemplars_Guide_v1.5.md | motadata-coder-a-complete-guide_v1.7.md | archive/by_topic/governance_history | high |
| ml/.../archives/legacy-v1.0-v1.4/GOLDEN_EXEMPLARS_GUIDE.md | v1.7 | already in archive | medium |

---

## Outside Canonical Layers

| path | note |
|------|------|
| motadata-coder-a-complete-guide_v1.7.md (root) | Consider moving to governance/ or docs/ |
| GREG_Pre-Review_Attack_Result.md (root) | Consider moving to governance/ |

---

## Naming Patterns (draft, backup, old)

- `archive/docs/debug/*` — debug artifacts
- `archive/docs/cleanup_20251231/` — cleanup batch
- No explicit `*draft*`, `*backup*` doc names in primary paths; some in archive.
