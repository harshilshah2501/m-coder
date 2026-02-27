# Move Plan (Advisory — No Execution)

Each entry proposes an action. No moves are performed.

---

## Schema

- source_path
- target_path
- action_type: keep | git_mv | archive/by_topic/<category> | needs_decision
- reason
- risk_level
- files_affected
- reference_update_required: yes | no

---

## Example Entries

### motadata-coder-a-complete-guide_v1.7.md

| field | value |
|-------|-------|
| source_path | motadata-coder-a-complete-guide_v1.7.md |
| target_path | governance/motadata-coder-a-complete-guide_v1.7.md |
| action_type | git_mv |
| reason | Canonical production guide; should live under governance |
| risk_level | high |
| files_affected | 1 |
| reference_update_required | yes |

### Golden_Exemplars_Guide_v1.5.md

| field | value |
|-------|-------|
| source_path | ml/training/sft/exemplars/guides/Golden_Exemplars_Guide_v1.5.md |
| target_path | archive/by_topic/governance_history/Golden_Exemplars_Guide_v1.5.md |
| action_type | archive/by_topic/governance_history |
| reason | Superseded by v1.7; preserve for history |
| risk_level | high |
| files_affected | 1 |
| reference_update_required | yes |

### GREG_Pre-Review_Attack_Result.md

| field | value |
|-------|-------|
| source_path | GREG_Pre-Review_Attack_Result.md |
| target_path | governance/GREG_Pre-Review_Attack_Result.md |
| action_type | git_mv |
| reason | Governance-related; co-locate with GREG |
| risk_level | medium |
| files_affected | 1 |
| reference_update_required | yes |

### PHASE6* specs in ml/training/src/sources/Motadata/

| field | value |
|-------|-------|
| source_path | ml/training/src/sources/Motadata/PHASE6_*.md, PHASE6B_*.md |
| target_path | ml/training/phase6/ or ml/training/phase6c/ as appropriate |
| action_type | needs_decision |
| reason | Co-locate Stage-6 specs with harness code; verify no broken imports |
| risk_level | high |
| files_affected | multiple |
| reference_update_required | yes |

### chat-*.txt (root)

| field | value |
|-------|-------|
| source_path | chat-*.txt |
| target_path | archive/by_topic/misc_orphans/ or delete |
| action_type | archive/by_topic/misc_orphans |
| reason | Session logs; not part of source tree |
| risk_level | low |
| files_affected | 1+ |
| reference_update_required | no |

---

## Special Rule

Any file affecting locked doctrine (GREG, phase semantics, dataset freeze rules, runtime gates) defaults to **needs_decision** unless the action is clearly **keep**.
