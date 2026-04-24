"""
Offline validation for code_reasoning_trace.v1 and patch_intent.v1.

Source of truth: docs/validation/CODE_REASONING_CONTRACT_DESIGN_V1.md
Plan handoff: docs/validation/PLAN_CONTRACT_FREEZE_V1.md (plan_contract.v1)
"""

from __future__ import annotations

from typing import Any

from runtime.plan_contract.v1_validate import validate_plan_contract_v1

TRACE_SCHEMA = "code_reasoning_trace.v1"
PATCH_INTENT_SCHEMA = "patch_intent.v1"

TRACE_TOP_LEVEL = frozenset(
    {"schema_version", "request_id", "plan_contract_ref", "bounds", "steps", "terminal", "ledger_preview"}
)

STEP_KINDS = (
    "LOCATE_TARGET",
    "INSPECT_CONTEXT",
    "CHANGE_STRATEGY",
    "BOUNDED_PATCH_INTENT",
    "FINAL_PROPOSAL",
)
STEP_KIND_ORDER = list(STEP_KINDS)

STEP_STATUSES = frozenset({"complete", "skipped", "blocked", "failed"})
TERMINAL_OUTCOMES = frozenset({"completed", "refused", "deferred", "failed"})

FILE_EDIT_ROLES = frozenset({"edit", "read", "verify"})


def _patch_line_total(pi: dict[str, Any]) -> int:
    files = pi.get("files") if isinstance(pi.get("files"), list) else []
    total = 0
    for row in files:
        if not isinstance(row, dict):
            continue
        hint = row.get("line_span_hint")
        if not isinstance(hint, dict):
            continue
        try:
            st = int(hint["start"])
            en = int(hint["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if en >= st:
            total += en - st + 1
    return total


def _patch_file_count(pi: dict[str, Any]) -> int:
    files = pi.get("files") if isinstance(pi.get("files"), list) else []
    return sum(1 for f in files if isinstance(f, dict))

CODE_REASONING_CATEGORIES = frozenset(
    {
        "completed_valid_trace",
        "deferred_insufficient_evidence",
        "refused_forbidden_action",
        "failed_patch_bounds_violation",
        "invalid_step_ordering",
    }
)


def validate_patch_intent_v1(pi: Any, plan_contract: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if not isinstance(pi, dict):
        return ["patch_intent must be an object"]
    if pi.get("schema_version") != PATCH_INTENT_SCHEMA:
        errs.append(f"patch_intent.schema_version must be {PATCH_INTENT_SCHEMA!r}")
    cb = plan_contract.get("change_boundaries") if isinstance(plan_contract.get("change_boundaries"), dict) else {}
    try:
        max_files = int(cb.get("max_files_touched", 0))
        max_lines = int(cb.get("max_diff_lines_hint", 0))
    except (TypeError, ValueError):
        return errs + ["plan_contract.change_boundaries must have integer max_files_touched and max_diff_lines_hint"]

    files = pi.get("files")
    if not isinstance(files, list):
        errs.append("patch_intent.files must be an array")
        return errs
    if len(files) > max_files:
        errs.append(f"patch_intent.files: len {len(files)} exceeds plan_contract max_files_touched {max_files}")

    total_lines = 0
    for i, row in enumerate(files):
        if not isinstance(row, dict):
            errs.append(f"patch_intent.files[{i}] must be an object")
            continue
        p = row.get("path")
        if not isinstance(p, str) or not p.strip():
            errs.append(f"patch_intent.files[{i}].path must be a non-empty string")
        role = row.get("role")
        if role not in FILE_EDIT_ROLES:
            errs.append(f"patch_intent.files[{i}].role must be one of {sorted(FILE_EDIT_ROLES)} got {role!r}")
        hint = row.get("line_span_hint")
        if hint is not None:
            if not isinstance(hint, dict):
                errs.append(f"patch_intent.files[{i}].line_span_hint must be an object or omitted")
            else:
                try:
                    st = int(hint["start"])
                    en = int(hint["end"])
                except (KeyError, TypeError, ValueError):
                    errs.append(f"patch_intent.files[{i}].line_span_hint needs integer start and end")
                else:
                    if en < st:
                        errs.append(f"patch_intent.files[{i}].line_span_hint end < start")
                    else:
                        total_lines += en - st + 1

    if total_lines > max_lines:
        errs.append(
            f"patch_intent line_span_hint total lines {total_lines} exceeds plan_contract max_diff_lines_hint {max_lines}"
        )

    # Caller may also compare against trace bounds in validate_code_reasoning_trace_v1

    for key in ("intent_description", "rollback_summary"):
        if not isinstance(pi.get(key), str):
            errs.append(f"patch_intent.{key} must be a string")

    tp = pi.get("test_plan")
    if not isinstance(tp, list) or not all(isinstance(x, str) for x in tp):
        errs.append("patch_intent.test_plan must be an array of strings")
    rn = pi.get("risk_notes")
    if not isinstance(rn, list) or not all(isinstance(x, str) for x in rn):
        errs.append("patch_intent.risk_notes must be an array of strings")

    unknown = set(pi.keys()) - {
        "schema_version",
        "files",
        "intent_description",
        "rollback_summary",
        "test_plan",
        "risk_notes",
    }
    if unknown:
        errs.append(f"patch_intent unknown keys: {sorted(unknown)}")
    return errs


def _validate_step_evidence_req(er: Any, label: str) -> list[str]:
    errs: list[str] = []
    if not isinstance(er, dict):
        return [f"{label}.evidence_requirements must be an object"]
    for key in ("must_have", "nice_to_have", "insufficient_without"):
        if key not in er:
            errs.append(f"{label}.evidence_requirements.{key} is required")
        elif not isinstance(er[key], list) or not all(isinstance(x, str) for x in er[key]):
            errs.append(f"{label}.evidence_requirements.{key} must be an array of strings")
    return errs


def _validate_refusal(ref: Any, label: str) -> list[str]:
    if ref is None:
        return []
    if not isinstance(ref, dict):
        return [f"{label}.refusal must be an object"]
    errs: list[str] = []
    for k in ("code", "detail", "recoverable"):
        if k not in ref:
            errs.append(f"{label}.refusal.{k} is required")
        elif k == "recoverable" and not isinstance(ref["recoverable"], bool):
            errs.append(f"{label}.refusal.recoverable must be a boolean")
        elif k != "recoverable" and not isinstance(ref[k], str):
            errs.append(f"{label}.refusal.{k} must be a string")
    return errs


def _first_step_index_for_kind(steps: list[dict[str, Any]], kind: str) -> int | None:
    best: int | None = None
    for st in steps:
        if not isinstance(st, dict) or st.get("step_kind") != kind:
            continue
        try:
            si = int(st["step_index"])
        except (KeyError, TypeError, ValueError):
            continue
        if best is None or si < best:
            best = si
    return best


def _ordering_errors_for_steps(steps: list[dict[str, Any]]) -> list[str]:
    errs: list[str] = []
    ordered: list[tuple[int, str]] = []
    for st in steps:
        if not isinstance(st, dict):
            continue
        sk = st.get("step_kind")
        si = st.get("step_index")
        if isinstance(si, int) and isinstance(sk, str) and sk in STEP_KINDS:
            ordered.append((si, sk))
    ordered.sort(key=lambda x: x[0])
    kinds_seen: dict[str, int] = {}
    for si, sk in ordered:
        kinds_seen[sk] = kinds_seen.get(sk, 0) + 1
        if kinds_seen[sk] > 1:
            errs.append(f"step_kind {sk} must not repeat in v1 trace (step_index {si})")

    for i, k_a in enumerate(STEP_KIND_ORDER):
        ia = _first_step_index_for_kind(steps, k_a)
        if ia is None:
            continue
        for k_b in STEP_KIND_ORDER[i + 1 :]:
            ib = _first_step_index_for_kind(steps, k_b)
            if ib is None:
                continue
            if ib < ia:
                errs.append(
                    f"step ordering: first occurrence of {k_b} (step_index {ib}) "
                    f"is before first occurrence of {k_a} (step_index {ia})"
                )
    return errs


def validate_code_reasoning_trace_v1(trace: Any, plan_contract: Any) -> list[str]:
    errs: list[str] = []
    errs.extend(validate_plan_contract_v1(plan_contract))
    if not isinstance(trace, dict):
        return errs + ["code_reasoning_trace must be a JSON object"]
    unknown = set(trace.keys()) - TRACE_TOP_LEVEL
    if unknown:
        errs.append(f"code_reasoning_trace unknown top-level keys: {sorted(unknown)}")
    if trace.get("schema_version") != TRACE_SCHEMA:
        errs.append(f"code_reasoning_trace.schema_version must be {TRACE_SCHEMA!r}")
    if not isinstance(trace.get("request_id"), str) or not str(trace.get("request_id")).strip():
        errs.append("code_reasoning_trace.request_id must be a non-empty string")
    if not isinstance(trace.get("plan_contract_ref"), str) or not str(trace.get("plan_contract_ref")).strip():
        errs.append("code_reasoning_trace.plan_contract_ref must be a non-empty string")

    bounds = trace.get("bounds")
    if not isinstance(bounds, dict):
        errs.append("code_reasoning_trace.bounds must be an object")
    else:
        try:
            mi = int(bounds["max_iterations"])
            mtc = int(bounds["max_tool_calls"])
            mer = int(bounds["max_evidence_refs_per_step"])
            mst = int(bounds["max_step_text_chars"])
            mpf = int(bounds["max_patch_intent_files"])
            mpl = int(bounds["max_patch_intent_lines_total"])
        except (KeyError, TypeError, ValueError):
            errs.append("bounds: max_iterations, max_tool_calls, max_evidence_refs_per_step, max_step_text_chars, max_patch_intent_files, max_patch_intent_lines_total must be integers")
        else:
            if not (1 <= mi <= 12):
                errs.append("bounds.max_iterations must be between 1 and 12")
            if not (0 <= mtc <= mi):
                errs.append("bounds.max_tool_calls must be between 0 and max_iterations")
            if not (1 <= mer <= 32):
                errs.append("bounds.max_evidence_refs_per_step must be between 1 and 32")
            if mst < 1:
                errs.append("bounds.max_step_text_chars must be >= 1")
            pcb = plan_contract.get("change_boundaries") if isinstance(plan_contract.get("change_boundaries"), dict) else {}
            try:
                pmaxf = int(pcb.get("max_files_touched", 0))
                pmaxl = int(pcb.get("max_diff_lines_hint", 0))
            except (TypeError, ValueError):
                pmaxf, pmaxl = 0, 0
            if mpf > pmaxf:
                errs.append("bounds.max_patch_intent_files must be <= plan_contract.change_boundaries.max_files_touched")
            if mpl > pmaxl:
                errs.append(
                    "bounds.max_patch_intent_lines_total must be <= plan_contract.change_boundaries.max_diff_lines_hint"
                )
        if "summarize_between_steps" not in bounds or not isinstance(bounds["summarize_between_steps"], bool):
            errs.append("bounds.summarize_between_steps must be a boolean")

    steps = trace.get("steps")
    if not isinstance(steps, list):
        errs.append("code_reasoning_trace.steps must be an array")
        return errs

    if isinstance(bounds, dict):
        try:
            mi = int(bounds["max_iterations"])
        except (TypeError, ValueError, KeyError):
            mi = 0
        if len(steps) > mi:
            errs.append(f"code_reasoning_trace.steps length {len(steps)} exceeds bounds.max_iterations {mi}")

    indices: list[int] = []
    for i, st in enumerate(steps):
        label = f"steps[{i}]"
        if not isinstance(st, dict):
            errs.append(f"{label} must be an object")
            continue
        if "step_index" not in st:
            errs.append(f"{label}.step_index is required")
        else:
            try:
                si = int(st["step_index"])
                indices.append(si)
            except (TypeError, ValueError):
                errs.append(f"{label}.step_index must be an integer")
        sk = st.get("step_kind")
        if sk not in STEP_KINDS:
            errs.append(f"{label}.step_kind must be one of {STEP_KINDS} got {sk!r}")
        stat = st.get("status")
        if stat not in STEP_STATUSES:
            errs.append(f"{label}.status must be one of {sorted(STEP_STATUSES)} got {stat!r}")
        errs.extend(_validate_step_evidence_req(st.get("evidence_requirements"), label))
        refs = st.get("evidence_refs_used")
        if not isinstance(refs, list) or not all(isinstance(x, str) for x in refs):
            errs.append(f"{label}.evidence_refs_used must be an array of strings")
        elif len(refs) == 0 and stat not in ("skipped", "blocked", "failed"):
            errs.append(f"{label}.evidence_refs_used may be empty only when status is skipped, blocked, or failed")
        rat = st.get("rationale")
        if not isinstance(rat, str):
            errs.append(f"{label}.rationale must be a string")
        elif not rat.strip() and stat != "skipped":
            errs.append(f"{label}.rationale must be non-empty unless status is skipped")
        if not isinstance(st.get("summary"), str) or not str(st.get("summary")).strip():
            errs.append(f"{label}.summary must be a non-empty string")

        pi = st.get("patch_intent")
        if pi is not None:
            if sk not in ("BOUNDED_PATCH_INTENT", "FINAL_PROPOSAL"):
                errs.append(f"{label}.patch_intent may appear only for BOUNDED_PATCH_INTENT or FINAL_PROPOSAL")
            else:
                errs.extend(validate_patch_intent_v1(pi, plan_contract))
        if stat in ("blocked", "failed"):
            errs.extend(_validate_refusal(st.get("refusal"), label))

    if indices:
        uniq = set(indices)
        n = len(steps)
        if uniq != set(range(n)):
            errs.append(f"step_index set must be exactly {{0..{n - 1}}}; got {sorted(uniq)}")

    terminal = trace.get("terminal")
    if not isinstance(terminal, dict):
        errs.append("code_reasoning_trace.terminal must be an object")
    else:
        oc = terminal.get("outcome")
        if oc not in TERMINAL_OUTCOMES:
            errs.append(f"terminal.outcome must be one of {sorted(TERMINAL_OUTCOMES)} got {oc!r}")
        for k in ("reason_code", "human_message"):
            if not isinstance(terminal.get(k), str) or not str(terminal.get(k)).strip():
                errs.append(f"terminal.{k} must be a non-empty string")
        if "execution_requested" not in terminal or not isinstance(terminal["execution_requested"], bool):
            errs.append("terminal.execution_requested must be a boolean")
        elif terminal["execution_requested"] is True and terminal.get("outcome") != "refused":
            errs.append("terminal.execution_requested may be true only when terminal.outcome is refused (Lane 4)")

    lp = trace.get("ledger_preview")
    if lp is not None:
        if not isinstance(lp, list):
            errs.append("ledger_preview must be an array when present")
        else:
            for j, row in enumerate(lp):
                if not isinstance(row, dict) or not isinstance(row.get("event_type"), str):
                    errs.append(f"ledger_preview[{j}] must be an object with event_type string")

    if isinstance(steps, list):
        errs.extend(_ordering_errors_for_steps(steps))

    if isinstance(bounds, dict) and isinstance(steps, list):
        try:
            cap_lines = int(bounds["max_patch_intent_lines_total"])
            cap_files = int(bounds["max_patch_intent_files"])
        except (KeyError, TypeError, ValueError):
            pass
        else:
            for i, st in enumerate(steps):
                if not isinstance(st, dict):
                    continue
                pi = st.get("patch_intent")
                if not isinstance(pi, dict):
                    continue
                fc = _patch_file_count(pi)
                if fc > cap_files:
                    errs.append(
                        f"steps[{i}].patch_intent file count {fc} exceeds bounds.max_patch_intent_files {cap_files}"
                    )
                tl = _patch_line_total(pi)
                if tl > cap_lines:
                    errs.append(
                        f"steps[{i}].patch_intent line total {tl} exceeds bounds.max_patch_intent_lines_total {cap_lines}"
                    )

    # Handoff G2–G5 (after structural)
    posture = plan_contract.get("approval_posture")
    forbidden = set(plan_contract.get("forbidden_actions") or []) if isinstance(plan_contract.get("forbidden_actions"), list) else set()
    allowed = set(plan_contract.get("allowed_actions") or []) if isinstance(plan_contract.get("allowed_actions"), list) else set()

    has_patch = any(
        isinstance(s, dict) and isinstance(s.get("patch_intent"), dict) for s in steps if isinstance(s, dict)
    )
    if has_patch and posture == "refuse":
        errs.append("handoff G2: plan_contract.approval_posture must not be refuse when patch_intent is present")
    if has_patch and "propose_patch_text" not in allowed:
        errs.append("handoff G3: plan_contract.allowed_actions must include propose_patch_text when patch_intent is present")
    if has_patch and bool(forbidden & {"propose_patch_text"}):
        errs.append("handoff G4: propose_patch_text must not be in forbidden_actions when patch_intent is present")

    return errs


def validate_code_reasoning_category(
    trace: dict[str, Any],
    plan_contract: dict[str, Any],
    category: str,
) -> list[str]:
    errs: list[str] = []
    if category not in CODE_REASONING_CATEGORIES:
        return [f"unknown code_reasoning_category: {category!r}"]

    structural = validate_code_reasoning_trace_v1(trace, plan_contract)
    term = trace.get("terminal") if isinstance(trace.get("terminal"), dict) else {}
    outcome = term.get("outcome")
    reason = str(term.get("reason_code") or "")

    if category == "invalid_step_ordering":
        if not structural:
            errs.append("invalid_step_ordering: expected structural/ordering validation errors on fixture")
        elif not any("ordering" in e.lower() or "before first" in e.lower() for e in structural):
            errs.append("invalid_step_ordering: expected ordering-related structural errors")
        return errs

    if structural:
        errs.extend(structural)
        return errs

    steps = trace.get("steps") if isinstance(trace.get("steps"), list) else []

    if category == "completed_valid_trace":
        if outcome != "completed":
            errs.append("completed_valid_trace: terminal.outcome must be completed")
        if not any(isinstance(s, dict) and s.get("step_kind") == "BOUNDED_PATCH_INTENT" for s in steps):
            errs.append("completed_valid_trace: must include a BOUNDED_PATCH_INTENT step")
        if term.get("execution_requested") is True:
            errs.append("completed_valid_trace: execution_requested must be false")

    elif category == "deferred_insufficient_evidence":
        if outcome != "deferred":
            errs.append("deferred_insufficient_evidence: terminal.outcome must be deferred")
        if "insufficient" not in reason.lower() and reason != "insufficient_evidence":
            errs.append("deferred_insufficient_evidence: reason_code should indicate insufficient evidence")

    elif category == "refused_forbidden_action":
        if outcome != "refused":
            errs.append("refused_forbidden_action: terminal.outcome must be refused")
        if "forbidden" not in reason.lower() and reason != "plan_contract_forbidden_action":
            errs.append("refused_forbidden_action: reason_code should indicate forbidden action")

    elif category == "failed_patch_bounds_violation":
        if outcome != "failed":
            errs.append("failed_patch_bounds_violation: terminal.outcome must be failed")
        if "patch" not in reason.lower() and "bound" not in reason.lower() and reason != "patch_intent_over_bound":
            errs.append("failed_patch_bounds_violation: reason_code should reference patch bounds")

    return errs
