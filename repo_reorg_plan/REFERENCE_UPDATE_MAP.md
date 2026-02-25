# Reference Update Map

**Source:** rg-based scan; repo_audit/DOC_INDEX.md, ORPHANS.md

Files that reference moved paths and proposed updates. Do NOT run sed/perl unless EXECUTE=1.

---

## motadata-coder-a-complete-guide_v1.7.md

If moved: motadata-coder-a-complete-guide_v1.7.md to governance/motadata-coder-a-complete-guide_v1.7.md

| file | proposed replacement |
|------|----------------------|
| repo_audit/* | governance/motadata-coder-a-complete-guide_v1.7.md |
| docs/status/COMPLETE_SESSION_SUMMARY_FEB6.md | governance/ path if path used |

**Commands (DO NOT RUN unless EXECUTE=1):**
```bash
rg -l "motadata-coder-a-complete-guide" --type-add 'scan:*.{md,txt,py,sh,json}' -t scan .
# sed -i 's|motadata-coder-a-complete-guide_v1\.7\.md|governance/motadata-coder-a-complete-guide_v1.7.md|g' <files>
```

---

## GREG_Pre-Review_Attack_Result.md

If moved: GREG_Pre-Review_Attack_Result.md to governance/GREG_Pre-Review_Attack_Result.md

| file | proposed replacement |
|------|----------------------|
| governance/golden-exemplars/GREG/GREG-Initiation-Ratification-v0.9.md | governance/GREG_Pre-Review_Attack_Result.md |

**Commands (DO NOT RUN unless EXECUTE=1):**
```bash
rg -l "GREG_Pre-Review_Attack_Result" --type-add 'scan:*.{md,txt,py,sh,json}' -t scan .
# sed -i 's|GREG_Pre-Review_Attack_Result\.md|governance/GREG_Pre-Review_Attack_Result.md|g' governance/golden-exemplars/GREG/GREG-Initiation-Ratification-v0.9.md
```

---

## Golden_Exemplars_Guide_v1.5.md

If moved: ml/training/sft/exemplars/guides/Golden_Exemplars_Guide_v1.5.md to archive/by_topic/governance_history/

| file | proposed replacement |
|------|----------------------|
| governance/review-packages/Phase-01_Review_Package/* | archive/by_topic/governance_history/Golden_Exemplars_Guide_v1.5.md |
| governance/golden-exemplars/Phases/Phase-01/PHASE_01_REVIEW_GUIDE.md | Same |
| ml/training/sft/exemplars/guides/README.md | v1.7 for authoring; archived v1.5 for historical |
| ml/training/sft/exemplars/guides/CLEANUP_SUMMARY.md | governance/motadata-coder-a-complete-guide_v1.7 |
| ml/training/sft/exemplars/guides/JUDGMENT_SYSTEM_README.md | Same |

**Commands (DO NOT RUN unless EXECUTE=1):**
```bash
rg -l "Golden_Exemplars_Guide_v1\.5" --type-add 'scan:*.{md,txt}' -t scan .
# perl -i -pe 's|guides/Golden_Exemplars_Guide_v1\.5\.md|archive/by_topic/governance_history/Golden_Exemplars_Guide_v1.5.md|g' <files>
```

---

## chat-*.txt

No known code references. Safe to move without reference updates.
