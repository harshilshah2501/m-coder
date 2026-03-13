# Coding Implementation (CODE) Exemplars (Engineering-First)

**Category**: Phase-5 (Implementation Layer)  
**Exemplar IDs**: CODE-01 through CODE-07+ (CODE-08–10 optional depth)
**Context**: Engineering-first assistant generating safe, review-compliant code

## Purpose

These exemplars translate reasoning patterns into safe, policy-compliant code implementations. They focus on safe refactors, review workflows in code, ownership gates, staged implementations, safe defaults, error handling, and observability.

**Note**: Operates on engineering code (refactors, implementations, API changes) rather than ops automation (runbooks, remediation). Same safety DNA, development context.

## What It Teaches

- Safe refactor with validation hooks (CODE-01)
- API change workflow with reviews before breaking change (CODE-02)
- Staged refactor with rollout plan, tests, assumptions (CODE-04)
- Safe defaults: opt-in features with audit trails (CODE-05)
- Error handling: when code should refuse (e.g., validation failure) (CODE-06)
- Observability: logging constraints, approval chains, audit (CODE-07)
- Multi-source test synthesis (CODE-08, optional)
- Distributed approval chains (CODE-09, optional)
- Adaptive configurations (CODE-10, optional)

## Key Principle

**Code is constraint enforcement.** Generated code must encode review gates and ownership, not bypass them.

## Success Metrics

- 100% of refactor code includes incremental migration paths
- 100% of API changes generate review workflows
- Ownership checks explicitly present in changes
- Code freezes respected (no merges during freeze)
- Error handling: refuses gracefully on validation failure
- Audit trail complete: who, what, when, why documented

## Dependencies

- Phase-4 exemplars (MIX-01 through MIX-05) must pass mutation testing
- Phase-3 exemplars (DES-01 through DES-05) fully locked
- Phase-2 exemplars (CONF-01 through CONF-05) fully locked
- Reasoning patterns from Phase-1 must be internalized
- Each CODE exemplar builds on priors (CODE-01→02→03...)

## File Structure

```
Coding/
├── README.md (this file)
├── CODE-01.md (safe remediation)
├── CODE-02.md (policy workflows)
├── CODE-04.md (staged refactors)
├── CODE-05.md (safe defaults)
├── CODE-06.md (error handling & refusal)
└── CODE-07.md (observability & audit)
```

## Code Implementation Principles

1. **Review-first**: PR workflows before direct changes
2. **Ownership-explicit**: No silent permission bypass
3. **Validation-first**: Check before modify
4. **Rollback-ready**: Reverse procedures included
5. **Audit-complete**: Logging at decision points
6. **Error-graceful**: Fail safely, never silently
7. **Constraint-aware**: Respect freezes, ownership, blast radius

## Example Pattern

```python
# ❌ WRONG (what base LLM generates)
def refactor_api():
    change_signature()  # Breaking change, no migration
    deploy()            # No review check
    return "done"

# ✅ RIGHT (what CODE exemplars teach)
def refactor_api(author_id, target_branch):
    # Validate constraints
    if is_code_freeze_active(target_branch):
        return Refusal("Code freeze active on: {}".format(target_branch))
    
    # Check ownership
    if not is_code_owner(author_id, "api/"):
        return Refusal("Not code owner for api/: {}".format(author_id))
    
    # Create audit trail
    audit_log("refactor_api", author_id, target_branch)
    
    # Propose staged migration (not breaking change)
    return ReviewWorkflow(
        action="add_new_signature",
        reason="Deprecate old API, support both during migration",
        migration_plan="Phase 1: Add new, Phase 2: Migrate callers, Phase 3: Remove old",
        review_required=["api-team", "platform"]
    )
```

## Related Guides

- [EXEMPLAR_AUTHORING_GUIDE.md](../../guides/EXEMPLAR_AUTHORING_GUIDE.md) — Code sequencing rationale
- [REVIEW_CHECKLIST.md](../../guides/REVIEW_CHECKLIST.md) — 9 comprehensive review criteria (includes 3 D.N.A gates)
- [REVIEWER_ENGINEER_GUIDE.md](../../guides/REVIEWER_ENGINEER_GUIDE.md) — Code review lens
