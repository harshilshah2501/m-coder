from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from runtime.context.contracts import ContextBundle

from .reasoner import ExplainDebugResult


GENERIC_PHRASES = (
    "does not provide enough context",
    "not enough context",
    "not directly visible",
    "without more context",
    "can infer some potential reasons",
    "might stem from",
    "could occur during",
)


@dataclass
class DebugNarrationGateResult:
    curated: ExplainDebugResult
    quality: str
    issues: List[str]


def _norm(path: str) -> str:
    return str(path or "").replace("\\", "/").strip().lower()


def _selected_item(bundle: ContextBundle, selected_file: str):
    sf = _norm(selected_file)
    if not sf:
        return None
    base = sf.split("/")[-1]
    for it in bundle.items:
        p = _norm(it.path)
        if p == sf or p.endswith("/" + base):
            return it
    return None


def _method_clues(text: str, cap: int = 3) -> List[str]:
    out: List[str] = []
    for line in str(text or "").splitlines():
        s = line.strip()
        if not s or s.startswith("//"):
            continue
        m = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", s)
        if not m:
            continue
        name = m.group(1)
        if name in {"if", "for", "while", "switch", "catch", "new", "return"}:
            continue
        if name not in out:
            out.append(name)
        if len(out) >= cap:
            break
    return out


def _has_branch_cues(text: str) -> bool:
    t = f" {str(text or '').lower()} "
    return any(tok in t for tok in (" if ", " else ", " return ", " catch", " throw", " null", " switch"))


def apply_debug_narration_gate(
    result: ExplainDebugResult,
    *,
    selected_file: str,
    bundle: ContextBundle,
) -> DebugNarrationGateResult:
    if result.error:
        return DebugNarrationGateResult(curated=result, quality="ERROR", issues=["debug_reasoner_error"])

    issues: List[str] = []
    item = _selected_item(bundle, selected_file)
    sf_norm = _norm(selected_file)
    sf_base = sf_norm.split("/")[-1] if sf_norm else ""
    methods = _method_clues(item.content if item else "")
    branchy = _has_branch_cues(item.content if item else "")

    summary = str(result.summary or "").strip()
    logic = str(result.logic_flow or "").strip()
    likely = str(result.likely_bug_risk or "").strip()
    confidence = str(result.confidence_limits or "").strip()
    evidence = [str(x).strip() for x in (result.evidence or []) if str(x).strip()]
    joined = f"{summary} {logic} {likely}".lower()

    if any(p in joined for p in GENERIC_PHRASES):
        issues.append("generic_phrasing_detected")
    if sf_base and sf_base.lower() not in joined and sf_norm not in joined:
        issues.append("selected_file_not_explicitly_referenced")
    if not methods:
        issues.append("no_method_anchor_in_selected_file")
    if not branchy:
        issues.append("no_branch_signal_in_selected_file")
    if not confidence:
        issues.append("missing_confidence_limits")

    if sf_norm and not any(sf_norm in e.lower() for e in evidence):
        anchor = f"{sf_norm}:{methods[0]}" if methods else f"{sf_norm}:analysis_anchor"
        evidence.insert(0, anchor)

    quality = "STRONG"
    if issues:
        quality = "CURATED"
        method_part = f" methods={', '.join(methods)};" if methods else " methods=not_visible;"
        branch_part = " branch_signals=visible;" if branchy else " branch_signals=limited;"
        original_summary = summary
        if not original_summary:
            original_summary = (
                "Selected snippet has limited direct trace context; grounding requires method/body and branch anchors "
                "from selected file evidence."
            )
        summary = (
            f"{original_summary} "
            f"(Governance curation: `{sf_base or selected_file}`;{method_part}{branch_part} grounded to selected-file evidence.)"
        )
        if not logic:
            logic = "Trace selected-file control flow around anchor methods and verify conditional/early-return paths."
        if not likely:
            likely = "Risk likely centers on branch conditions or early return/exception paths before downstream dispatch."
        if not confidence:
            confidence = "Curated due to weak narration quality; validate against full caller/callee chain."

    curated = ExplainDebugResult(
        summary=summary,
        logic_flow=logic,
        likely_bug_risk=likely,
        evidence=evidence,
        confidence_limits=confidence,
        error=None,
    )
    return DebugNarrationGateResult(curated=curated, quality=quality, issues=issues)

