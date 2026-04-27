from __future__ import annotations

import re
from typing import Any


_OWNER_RE = re.compile(
    r"(?:Primary implementation owner|Execution owner anchor \(supporting context, not base-class answer\)):\s*`(?P<cls>[^`]+)`\s+in\s+`(?P<file>[^`]+)`(?:,\s*method\s*`(?P<method>[^`]+)`)?",
    re.IGNORECASE,
)


def _norm_query(q: str) -> str:
    return (q or "").strip().lower()


def _is_structural_query(q: str) -> bool:
    ql = _norm_query(q)
    return any(x in ql for x in ("base class", "parent class", "extends", "implements", "what is"))


def _is_discovery_query(q: str) -> bool:
    ql = _norm_query(q)
    return ("find" in ql or "list" in ql or "all" in ql) and ("class" in ql or "classes" in ql or "handle" in ql)


def _is_explain_query(q: str) -> bool:
    ql = _norm_query(q)
    return any(x in ql for x in ("how", "explain", "architecture", "work"))


def _is_debug_why_query(q: str) -> bool:
    ql = _norm_query(q)
    return "why" in ql or "debug" in ql


def _extract_owner(steps: list[str]) -> dict[str, str]:
    for s in steps:
        m = _OWNER_RE.search(str(s))
        if m:
            return {
                "cls": str(m.group("cls") or "").strip(),
                "file": str(m.group("file") or "").strip(),
                "method": str(m.group("method") or "").strip(),
            }
    return {"cls": "", "file": "", "method": ""}


def _is_raw_snippet_step(step: str) -> bool:
    low = step.lower()
    return (
        low.startswith("visible method-window evidence:")
        or "method-window excerpt:" in low
        or "evidence excerpt:" in low
    )


def _sanitize_step(step: str, owner: dict[str, str]) -> str:
    if not _is_raw_snippet_step(step):
        return step.strip()


def _is_status_preamble(step: str) -> bool:
    return step.lower().startswith("authority status:")


def _is_owner_line(step: str) -> bool:
    s = step.lower()
    return s.startswith("primary implementation owner:") or s.startswith(
        "execution owner anchor (supporting context, not base-class answer):"
    )


def _first_meaningful_step(steps: list[str]) -> str:
    for s in steps:
        if _is_status_preamble(s):
            continue
        return s
    return steps[0] if steps else ""
    cls = owner.get("cls") or "owner class"
    method = owner.get("method") or "target method"
    file = owner.get("file") or "selected file"
    return f"Inspect `{cls}.{method}` in `{file}` to validate control-flow and persistence behavior."


def _extract_classes_from_context(resp: dict[str, Any], query: str) -> list[str]:
    files = ((resp.get("context_bundle") or {}).get("files") or []) if isinstance(resp.get("context_bundle"), dict) else []
    ql = _norm_query(query)
    classes: list[str] = []
    for f in files:
        if not isinstance(f, dict):
            continue
        p = str(f.get("path") or "")
        if not p:
            continue
        base = p.replace("\\", "/").split("/")[-1]
        if "." in base:
            base = base.rsplit(".", 1)[0]
        if not base:
            continue
        if "notification" in ql:
            if "notification" not in p.lower() and "notification" not in base.lower():
                continue
        if base not in classes:
            classes.append(base)
    return classes[:5]


def shape_prompt_summary(query: str, resp: dict[str, Any]) -> dict[str, str]:
    steps = ((resp.get("plan_summary") or {}).get("steps") or []) if isinstance(resp.get("plan_summary"), dict) else []
    steps = [str(s).strip() for s in steps if str(s).strip()]
    if not steps:
        return {"answer_1": "", "next_step": "", "answer_shape": "none"}

    owner = _extract_owner(steps)
    first = _sanitize_step(_first_meaningful_step(steps), owner)
    second = _sanitize_step(steps[1], owner) if len(steps) > 1 else ""

    # Structural: keep direct answer and suppress owner context.
    if _is_structural_query(query):
        direct = next((s for s in steps if s.lower().startswith("direct answer (grounded):")), "")
        if direct:
            return {"answer_1": _sanitize_step(direct, owner), "next_step": "", "answer_shape": "structural"}
        return {
            "answer_1": "Based on current evidence, a definitive structural base-class answer is not fully confirmed.",
            "next_step": "",
            "answer_shape": "structural",
        }

    # Discovery/list: list classes first, avoid single-owner collapse.
    if _is_discovery_query(query):
        classes = _extract_classes_from_context(resp, query)
        if classes:
            answer = "Based on current evidence, relevant classes include: " + ", ".join(f"`{c}`" for c in classes) + "."
            next_step = ""
            if classes:
                next_step = f"Inspect `{classes[0]}` and related handlers to confirm responsibilities and call flow."
            return {"answer_1": answer, "next_step": next_step, "answer_shape": "discovery"}
        fallback_answer = "Based on current evidence, a complete class list could not be confidently enumerated yet."
        fallback_next = "" if _is_owner_line(second) else second
        return {"answer_1": fallback_answer, "next_step": fallback_next, "answer_shape": "discovery"}

    # Explain/how/architecture: concise explanation + anchors.
    if _is_explain_query(query):
        if owner.get("cls"):
            method_part = f".{owner['method']}" if owner.get("method") else ""
            answer = (
                f"Based on current evidence, `{owner['cls']}{method_part}` appears to be the main anchor for this behavior."
            )
            next_step = ""
            if owner.get("file"):
                next_step = (
                    f"Inspect `{owner['cls']}{method_part}` in `{owner['file']}` and verify collaborators/branch handling."
                )
            return {"answer_1": answer, "next_step": next_step, "answer_shape": "explain"}
        return {"answer_1": first, "next_step": second, "answer_shape": "explain"}

    # Why/debug phrasing in prompt path.
    if _is_debug_why_query(query):
        answer = f"Hypothesis (based on current evidence): {first}"
        next_step = second or (
            f"Next inspection target: `{owner.get('cls')}`"
            + (f".{owner.get('method')}" if owner.get("method") else "")
            + (f" in `{owner.get('file')}`." if owner.get("file") else ".")
        )
        return {"answer_1": answer, "next_step": next_step, "answer_shape": "debug"}

    return {"answer_1": first, "next_step": second, "answer_shape": "default"}

