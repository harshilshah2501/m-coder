"""
Post-process Explain/Debug prose for product-facing brevity (PLAN_ONLY Debug).

Strips common speculative / consulting-padding phrasing and collapses logic_flow
into up to three imperative inspection lines. Does not touch retrieval, graph, or synthesis.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from .reasoner import ExplainDebugResult


_SPECULATIVE_SENTENCE_PATTERNS = re.compile(
    r"|".join(
        [
            r"\bif\s+the\s+update\s+is\s+(asynchronous|async)\b",
            r"\bmight\s+be\s+asynchronous\b",
            r"\bcould\s+involve\s+several\s+steps\b",
            r"\bcould\s+involve\b",
            r"\bseveral\s+steps\b",
            r"\bwithout\s+knowing\s+the\s+specifics\b",
            r"\bit\s+is\s+unclear\s+whether\b",
            r"\bwhether\s+the\s+update\s+is\b",
            r"\bpossibly\s+because\b",
            r"\bmight\s+be\s+due\s+to\b",
            r"\btherefore\s*,\s*possibly\b",
        ]
    ),
    flags=re.IGNORECASE,
)

_CONCRETE_LIKELY_HINTS = re.compile(
    r"|".join(
        [
            r"\bnull\b",
            r"\bearly-?return\b",
            r"\bexception\b",
            r"\bthrow\b",
            r"\bmissing\s+registration\b",
            r"\bregistration\s+mismatch\b",
            r"\broute\s+",
            r"\bpersist",
            r"\bwrite\s+path\b",
            r"\bread\s+.*\bfail",
            r"\bdecrypt\b",
            r"\bskip",
            r"\bdispatch\b",
        ]
    ),
    flags=re.IGNORECASE,
)

_IMP_START = re.compile(
    r"^(trace|inspect|verify|check|confirm|validate|open|read|map|enumerate)\b",
    flags=re.IGNORECASE,
)


def _split_sentences(text: str) -> List[str]:
    t = str(text or "").strip()
    if not t:
        return []
    parts = re.split(r"(?<=[.!?])\s+", t)
    return [p.strip() for p in parts if p.strip()]


def _sentence_is_speculative(s: str) -> bool:
    sl = f" {str(s).lower()} "
    if _SPECULATIVE_SENTENCE_PATTERNS.search(s):
        return True
    # Soft hedges that often pad debug prose without anchored claims
    if any(
        tok in sl
        for tok in (
            " might ",
            " could ",
            " may ",
            " possibly ",
            " perhaps ",
            " suggests that ",
            " it seems ",
            " unclear if ",
        )
    ):
        return True
    return False


def _strip_speculative_sentences(text: str) -> str:
    kept: List[str] = []
    for s in _split_sentences(text):
        if _sentence_is_speculative(s):
            continue
        kept.append(s.rstrip())
    return " ".join(kept).strip()


def _finalize_likely(likely: str, *, selected_file: str) -> str:
    base = Path(str(selected_file).replace("\\", "/")).name
    likely = _strip_speculative_sentences(likely)
    likely = " ".join(likely.split()).strip()
    ll = likely.lower()
    if ll.startswith("unknown based") or "does not yet prove" in ll:
        return likely
    if likely and _CONCRETE_LIKELY_HINTS.search(likely) and len(likely) >= 30:
        return likely
    # Tight, non-fantasy default tied to observable engineering checks
    return (
        f"Tie failure to a concrete branch in `{base}`: null guard, early return, exception path, "
        f"or missing registration/persistence call — confirm in the full method body, not from this snippet alone."
    )


def _line_candidates(logic_flow: str) -> List[str]:
    """Prefer explicit newlines, then clause splits."""
    raw = str(logic_flow or "").strip()
    if not raw:
        return []
    if "\n" in raw:
        return [ln.strip() for ln in raw.splitlines() if ln.strip()]
    if ";" in raw and len(raw) > 200:
        return [c.strip() for c in raw.split(";") if c.strip()]
    return _split_sentences(raw)


def _to_imperative_line(line: str) -> str:
    s = " ".join(line.split()).strip().rstrip(".")
    if not s:
        return ""
    low = s.lower()
    if _IMP_START.match(low):
        return s[0].upper() + s[1:] if s else s
    if low.startswith("use "):
        return s[0].upper() + s[1:]
    if low.startswith("the code "):
        inner = s[9:].strip()
        return f"Inspect {inner[0].lower() + inner[1:]}" if inner else s
    return f"Inspect: {s[0].lower() + s[1:]}" if s else ""


def _finalize_logic_flow(logic_flow: str, *, selected_file: str) -> str:
    stripped = _strip_speculative_sentences(logic_flow.replace("\n", " "))
    candidates: List[str] = []
    # Recover structure from original newlines before squashing
    for chunk in _line_candidates(logic_flow):
        chunk = _strip_speculative_sentences(chunk)
        if not chunk or _sentence_is_speculative(chunk):
            continue
        imper = _to_imperative_line(chunk)
        if imper and imper not in candidates:
            candidates.append(imper[:220])
    base = Path(str(selected_file).replace("\\", "/")).name
    cls = base.replace(".java", "").replace(".py", "")
    # Backfill up to 3 concrete inspection hints
    fillers = [
        f"Open `{base}` and confirm which method owns the failure path you care about.",
        f"Verify return/throw branches and null guards in the hottest method on that path.",
        f"Trace one callee from the selected snippet and confirm its preconditions.",
    ]
    for f in fillers:
        if len(candidates) >= 3:
            break
        if cls and cls not in f:
            pass
        if f not in candidates:
            candidates.append(f)
    out = candidates[:3]
    return "\n".join(out)


def _finalize_summary(summary: str, *, selected_file: str) -> str:
    base = Path(str(selected_file).replace("\\", "/")).name
    s = _strip_speculative_sentences(summary)
    s = " ".join(s.split()).strip()
    if not s:
        return f"Grounded on `{base}`; causal chain is not fully visible in the retrieved snippet."
    if _sentence_is_speculative(s):
        return f"Grounded on `{base}`; causal chain is not fully visible in the retrieved snippet."
    return s


def _is_api_route_wiring_query(query: str, selected_file: str) -> bool:
    q = str(query or "").lower()
    sf = str(selected_file or "").replace("\\", "/").lower()
    return any(t in q for t in ("route", "router", "apiserver", "runtime")) and sf.endswith("/apiserver.java")


def finalize_explain_debug_prose(
    result: ExplainDebugResult,
    *,
    query: str,
    selected_file: str,
) -> ExplainDebugResult:
    """
    Shape model/gate output into shorter, less speculative Debug copy.
    """
    if result.error:
        return result
    sf = str(selected_file or "").strip()
    summary = _finalize_summary(result.summary, selected_file=sf)
    logic_flow = _finalize_logic_flow(result.logic_flow, selected_file=sf)
    likely = _finalize_likely(result.likely_bug_risk, selected_file=sf)

    # Reasoner emits deterministic route-wiring text — keep it, only tighten whitespace and cap steps.
    if _is_api_route_wiring_query(query, sf):
        summary = " ".join(str(result.summary or "").split()).strip() or summary
        likely = " ".join(str(result.likely_bug_risk or "").split()).strip() or likely
        lf0 = str(result.logic_flow or "").strip()
        logic_flow = "\n".join(_finalize_logic_flow(lf0, selected_file=sf).splitlines()[:3]) if lf0 else logic_flow

    return ExplainDebugResult(
        summary=summary,
        logic_flow=logic_flow,
        likely_bug_risk=likely,
        evidence=list(result.evidence or []),
        confidence_limits=str(result.confidence_limits or "").strip(),
        error=None,
    )
