# Gating Checklist

**Source:** RISK_MAP.md, ARCHIVE_TAXONOMY.md, MOVESET_PLAN.jsonl

---

## Manual Review (Must Do)

- [ ] Approve `needs_decision` entries in MOVESET_PLAN.jsonl:
  - motadata-coder-a-complete-guide_v1.7.md → governance/
  - GREG_Pre-Review_Attack_Result.md → governance/
  - Golden_Exemplars_Guide_v1.5.md → archive/governance_history
- [ ] Decide canonical guide: v1.7 only vs v1.5 as reference.
- [ ] Confirm Phase-6 mutation spec locations (needs_decision items; do not auto-move).

---

## Required Checks Before Execution

- [ ] Run `repo_reorg_plan/tools/compute_duplicate_hashes.py` (only if EXECUTE=1) for smoke_traces.jsonl, EXEMPLAR_AUTHORING_GUIDE.
- [ ] Lint: `ruff check ml/ runtime/ observation/` (or project linter).
- [ ] Tests: Run phase6c, reporting, and harness tests as in tests_to_run.
- [ ] Grep: `rg -l "motadata-coder-a-complete-guide|GREG_Pre-Review_Attack_Result|Golden_Exemplars_Guide" .` and update REFERENCE_UPDATE_MAP if new refs found.

---

## Execution

- [ ] Set `EXECUTE=1` in `repo_reorg_plan/config`.
- [ ] Run `repo_reorg_plan/EXECUTION_SCRIPT_DRYRUN.sh`.
- [ ] Apply REFERENCE_UPDATE_MAP sed/perl commands (manually or via script).
- [ ] Re-run lint and tests.

---

## Rollback

```bash
git status
git diff
git reset --hard HEAD   # if nothing committed
git checkout -- <path>  # to restore specific files
git restore --staged <path>  # to unstage
```

If moves were committed:
```bash
git revert <commit>     # or
git reset --hard <prev_commit>
```
