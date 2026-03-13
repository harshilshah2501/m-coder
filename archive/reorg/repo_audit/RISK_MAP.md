# Risk Map

Classification of structural changes by potential impact.

---

## Low Risk

- Exact duplicates where canonical is obvious and copies live in archive/ or scratch dirs
- Unreferenced drafts and notes (*_draft.md, *_notes.txt)
- Logs and JSONL traces not referenced by code or docs
- Session logs (chat-*.txt)
- archive/ contents that are already segregated

**Typical actions:** archive/by_topic/draft_docs, archive/by_topic/misc_orphans, keep

---

## Medium Risk

- Near-duplicate docs with unclear canonical winner
- Training configs and experimental scripts that may still be used ad hoc
- Files in archive/ that touch doctrine but are clearly historical (e.g., old guides)
- GREG_Pre-Review_Attack_Result.md (governance-adjacent but not LOCKED)

**Typical actions:** archive/by_topic/legacy_training, archive/by_topic/deprecated_mutation, needs_decision

---

## High Risk

- **Phase semantics:** REF / CONF / DES / MIX / CODE / REACH; dominance hierarchy; D.N.A rules
- **Mutation harness:** PHASE6B_COLLAPSE_TAXONOMY, PHASE6C_* specs, Stage-6 pass criteria
- **Dataset compilation:** Deterministic rules, freeze checklists, boundary phrase equality
- **Runtime enforcement:** Plan/Judge/Authority/Irreversibility gates, ledger emission
- **Governance corpus:** GREG-Initiation-Ratification, golden-exemplars Phases, constitutional manifest
- **Primary guide:** motadata-coder-a-complete-guide_v1.7.md

**Typical actions:** keep in place; archive copies only with governance approval; always needs_decision before move/archive

---

## Usage

Use with MOVE_PLAN.md to review proposed moves. Escalate high-risk entries to governance review before execution.
