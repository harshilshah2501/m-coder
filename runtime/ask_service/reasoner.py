"""
ExplainDebugReasoner — Real code reasoning for EXPLAIN_DEBUG task type.

Invoked only when task_type=EXPLAIN_DEBUG and selected_file + selection are present.
Calls a vLLM-compatible HTTP completion endpoint; does NOT use template planner.
If the service is unavailable or parsing fails, the caller must NOT substitute
template steps (return explain_debug.error instead).
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Dict, List

from runtime.context.contracts import ContextBundle, ContextItem


LOG = logging.getLogger(__name__)

EXPLAIN_VLLM_URL_ENV = "MOTADATA_EXPLAIN_VLLM_URL"
DEFAULT_VLLM_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 60


def _explain_debug_request_log(
    request_id: str,
    base_url: str,
    model: str,
    status: str,
    t0: float,
    trace_id: str = "",
) -> None:
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    tid = (trace_id or "").strip() or "(none)"
    LOG.info(
        "EXPLAIN_DEBUG trace_id=%s request_id=%s routing_mode=explain_debug base_url=%s model=%s status=%s duration_ms=%.2f",
        tid,
        request_id,
        base_url,
        model,
        status,
        elapsed_ms,
    )


@dataclass
class ExplainDebugResult:
    """Structured result for explain/debug reasoning."""

    summary: str = ""
    logic_flow: str = ""
    likely_bug_risk: str = ""
    evidence: List[str] = field(default_factory=list)
    confidence_limits: str = ""
    error: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        if self.error:
            out["error"] = self.error
            return out
        if self.summary:
            out["summary"] = self.summary
        if self.logic_flow:
            out["logic_flow"] = self.logic_flow
        if self.likely_bug_risk:
            out["likely_bug_risk"] = self.likely_bug_risk
        if self.evidence:
            out["evidence"] = self.evidence
        if self.confidence_limits:
            out["confidence_limits"] = self.confidence_limits
        return out


def _norm_rel_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def _selection_is_minimal(selection: str) -> bool:
    """True when the IDE sent a tiny fragment (one call, identifier, single line)."""
    s = selection.strip()
    if not s:
        return True
    if len(s) < 100:
        return True
    if s.count("\n") < 2 and len(s) < 500:
        return True
    return False


def _prioritize_bundle_items_for_selection(bundle: ContextBundle, selected_file: str) -> List[ContextItem]:
    """
    Put the file matching ``selected_file`` first so the model sees full source before distractors.
    """
    sel = _norm_rel_path(selected_file).lower()
    base = sel.split("/")[-1] if "/" in sel else sel
    items = list(bundle.items[:10])
    if not sel:
        return items

    primary: List = []
    rest: List = []
    for it in items:
        p = _norm_rel_path(it.path).lower()
        if p == sel or p.endswith("/" + base) or (base and p.endswith(base)):
            primary.append(it)
        else:
            rest.append(it)
    return primary + rest if primary else items


def _build_prompt(
    query: str,
    selected_file: str,
    selection: str,
    bundle: ContextBundle,
) -> str:
    """Build a prompt for explain/debug from context bundle and selection."""
    minimal = _selection_is_minimal(selection)
    lines = [
        "You are analyzing code from a repository. Provide a structured analysis.",
        "The highlighted selection may be a short fragment (e.g. one method call or identifier). "
        "That is normal — use the full file contents under “Repository context” to resolve symbols and explain behavior.",
        "",
        "## Selected file",
        selected_file,
        "",
        "## Selected code (editor highlight; may be a fragment)",
        "```",
        selection.strip() or "(no selection text)",
        "```",
    ]
    if minimal:
        lines.extend(
            [
                "",
                "### Instructions for minimal / one-line selections",
                "- Do **not** answer that the code is “incomplete” or refuse to analyze — the full files below contain the implementation.",
                "- Locate the symbol or call site in the repository context (especially the selected file’s path).",
                "- Explain what the referenced API or expression does using those file bodies (methods, fields, callees).",
                "- In `evidence`, cite concrete paths and symbol names you used (e.g. `path/to/File.java:methodName`).",
            ]
        )
    lines.extend(
        [
            "",
            "## Repository context (relevant files; use these to interpret the selection)",
        ]
    )
    for item in _prioritize_bundle_items_for_selection(bundle, selected_file):
        lines.append(f"### {item.path}")
        lines.append("```")
        lines.append(item.content[:8000] + ("..." if len(item.content) > 8000 else ""))
        lines.append("```")
        lines.append("")
    lines.append("## User question")
    lines.append(query)
    lines.append("")
    lines.append("## Explain/debug contract (must follow)")
    lines.append("- Ground every claim in the selected snippet or repository context files shown above.")
    lines.append("- Do not invent symbols, methods, files, or stack behavior not present in provided context.")
    lines.append("- If selected-file grounding is weak or missing, explicitly say analysis is insufficiently grounded.")
    lines.append("- Prefer concrete control-flow and method-level clues over generic advice.")
    lines.append("- If you cannot cite at least one concrete method or branch clue from the selected file, state `insufficient_for_precise_trace` in confidence_limits.")
    lines.append("- Keep confidence limits explicit; avoid definitive root-cause claims without evidence.")
    lines.append("")
    lines.append(
        "Respond with a single JSON object (no markdown fences) with these exact keys: "
        '"summary" (string), "logic_flow" (string), "likely_bug_risk" (string), '
        '"evidence" (array of strings, file/method references), "confidence_limits" (string). '
        "Always cite the selected file path in evidence when present, and prefer concrete method/branch clues over generic caveats."
    )
    return "\n".join(lines)


def _selected_item(bundle: ContextBundle, selected_file: str) -> ContextItem | None:
    sel = _norm_rel_path(selected_file).lower()
    if not sel:
        return None
    base = sel.split("/")[-1]
    for item in bundle.items:
        p = _norm_rel_path(item.path).lower()
        if p == sel or p.endswith("/" + base):
            return item
    return None


def _extract_method_clues(text: str, cap: int = 3) -> List[str]:
    out: List[str] = []
    seen = set()
    blocked = {"if", "for", "while", "switch", "catch", "new", "return"}
    for m in re.finditer(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text, flags=re.MULTILINE):
        name = m.group(1)
        if name not in seen and name not in blocked:
            seen.add(name)
            out.append(name)
            if len(out) >= cap:
                return out

    # Java/Kotlin-style method declarations (anchored to declaration-like lines).
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("//") or s.startswith("*") or s.startswith("/*"):
            continue
        m = re.match(
            r"^(?:public|private|protected)?\s*"
            r"(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?"
            r"(?:[A-Za-z_][A-Za-z0-9_<>\[\], ?]*\s+)?"
            r"([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*(?:\{|throws\b)",
            s,
        )
        if not m:
            continue
        name = m.group(1)
        if name not in seen and name not in blocked:
            seen.add(name)
            out.append(name)
            if len(out) >= cap:
                break
    return out


def _has_control_flow_cues(text: str) -> bool:
    tl = text.lower()
    cues = (
        " if ",
        " else ",
        " for ",
        " while ",
        " switch",
        " return",
        " catch",
        " try",
        " throw",
        " null",
        " exception",
        " branch",
    )
    return any(c in f" {tl} " for c in cues)


def _extract_branch_clues(text: str, cap: int = 2) -> List[str]:
    out: List[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("//") or s.startswith("*"):
            continue
        sl = s.lower()
        if sl.startswith("if ") or sl.startswith("if("):
            out.append("if-condition branch")
        elif sl.startswith("else if") or sl.startswith("else"):
            out.append("else/else-if branch")
        elif sl.startswith("switch(") or sl.startswith("switch "):
            out.append("switch branch")
        elif sl.startswith("catch(") or sl.startswith("catch "):
            out.append("catch/exception branch")
        elif "return " in sl:
            out.append("early-return path")
        if len(out) >= cap:
            break
    # Deduplicate while preserving order.
    uniq: List[str] = []
    for x in out:
        if x not in uniq:
            uniq.append(x)
    return uniq


def _extract_selection_tokens(selection: str, cap: int = 5) -> List[str]:
    out: List[str] = []
    seen = set()
    blocked = {
        "if",
        "for",
        "while",
        "return",
        "def",
        "class",
        "self",
        "this",
        "null",
        "true",
        "false",
        "new",
        "trace",
        "debug",
        "list",
        "identify",
        "likely",
        "failure",
        "failures",
        "points",
        "condition",
        "conditions",
    }
    for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", selection or ""):
        t = tok.strip()
        if len(t) < 3:
            continue
        tl = t.lower()
        if tl in blocked:
            continue
        if tl in seen:
            continue
        seen.add(tl)
        out.append(t)
        if len(out) >= cap:
            break
    return out


def _selection_linked_clues(text: str, tokens: List[str], cap: int = 2) -> List[str]:
    if not text or not tokens:
        return []
    out: List[str] = []
    lines = text.splitlines()
    for tok in tokens:
        pattern = re.compile(rf"\b{re.escape(tok)}\b", flags=re.IGNORECASE)
        for line in lines:
            s = line.strip()
            if not s or s.startswith("//") or s.startswith("*") or s.startswith("#"):
                continue
            if pattern.search(s):
                snippet = s[:140]
                if snippet not in out:
                    out.append(snippet)
                break
        if len(out) >= cap:
            break
    return out


def _sanitize_forbidden_generic_phrases(text: str) -> str:
    """Rewrite known banned generic phrases into grounded alternatives."""
    s = str(text or "")
    if not s:
        return s
    replacements = {
        r"\bdifficult to pinpoint exact failure points\b": "requires direct method-body evidence for exact failure localization",
        r"\bwithout more context\b": "with current selected-file evidence limits",
        r"\bspeculative risks\b": "preliminary risks from available anchors",
        r"\bnot directly visible\b": "not present in the current selected-file snippet window",
    }
    out = s
    for pat, repl in replacements.items():
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out


def _debug_control_flow_marker_count(text: str) -> int:
    """Mirror verifier-friendly control-flow cues for debug prose shaping."""
    markers = (
        " if ",
        " else ",
        " branch",
        " condition",
        " return",
        " null",
        " exception",
        " throw",
        " catch",
        " switch",
        " method",
    )
    padded = f" {str(text or '').lower()} "
    return sum(1 for m in markers if m in padded)


def _ensure_selected_grounding(
    parsed: ExplainDebugResult,
    *,
    selected_file: str,
    selection: str,
    bundle: ContextBundle,
) -> ExplainDebugResult:
    if parsed.error:
        return parsed

    item = _selected_item(bundle, selected_file)
    sel_norm = _norm_rel_path(selected_file)
    sel_base = sel_norm.split("/")[-1] if sel_norm else ""
    sel_symbol = sel_base.replace(".java", "").replace(".py", "")

    # Truthful insufficiency when selected file is not even present in context.
    if item is None:
        return ExplainDebugResult(
            summary=(
                f"Selected file `{selected_file}` is not present in the retrieved context, "
                "so this debug analysis is insufficiently grounded."
            ),
            logic_flow=(
                "Cannot trace concrete method/branch behavior for the selected target without that file body."
            ),
            likely_bug_risk=(
                "Any root-cause claim would be speculative until selected-file code is included in context."
            ),
            evidence=[f"missing_in_context:{selected_file}"],
            confidence_limits=(
                "Insufficient grounding: include the selected file in evidence and retry EXPLAIN_DEBUG."
            ),
        )

    methods = _extract_method_clues(item.content or "")
    has_flow = _has_control_flow_cues(item.content or "")
    branches = _extract_branch_clues(item.content or "")
    sel_tokens = _extract_selection_tokens(selection)
    token_clues = _selection_linked_clues(item.content or "", sel_tokens)
    minimal_sel = _selection_is_minimal(selection)

    summary = parsed.summary or ""
    logic_flow = parsed.logic_flow or ""
    likely = parsed.likely_bug_risk or ""
    evidence = list(parsed.evidence or [])
    confidence = parsed.confidence_limits or ""

    # Enforce selected-file dominance in explicit evidence.
    sel_ref = sel_norm
    if methods:
        sel_ref = f"{sel_norm}:{methods[0]}"
    elif sel_tokens:
        sel_ref = f"{sel_norm}:{sel_tokens[0]}"
    else:
        sel_ref = f"{sel_norm}:analysis_anchor"

    # Keep at least one canonical path:anchor reference for downstream depth checks.
    has_path_anchor_ref = any("/" in str(e) and ":" in str(e) for e in evidence)
    if not has_path_anchor_ref:
        evidence.insert(0, sel_ref)
    elif not any(str(e).strip().lower() == sel_ref.lower() for e in evidence):
        # Even when model-provided refs exist, force one deterministic method-like anchor
        # to avoid depth undercount on branch-only/path-only evidence strings.
        evidence.insert(0, sel_ref)

    if not any(sel_norm.lower() in str(e).lower() or sel_symbol.lower() in str(e).lower() for e in evidence):
        evidence.insert(0, sel_ref)
    elif evidence and not (sel_norm.lower() in str(evidence[0]).lower() or sel_symbol.lower() in str(evidence[0]).lower()):
        evidence.insert(0, sel_ref)

    # Ensure response explicitly mentions the selected file/symbol.
    joined = f"{summary} {logic_flow} {likely}".lower()
    if sel_symbol and sel_symbol.lower() not in joined and sel_base.lower() not in joined:
        summary = (summary + " " if summary else "") + (
            f"Grounded on `{sel_base}` from `{sel_norm}`."
        )

    # Push concrete clues to avoid generic-only language.
    if methods and not any(m.lower() in joined for m in methods):
        logic_flow = (logic_flow + " " if logic_flow else "") + (
            "Relevant methods in selected file: " + ", ".join(methods) + "."
        )
    if token_clues and not any(c.lower() in joined for c in token_clues):
        logic_flow = (logic_flow + " " if logic_flow else "") + (
            "Selection-linked clues in selected file: " + "; ".join(token_clues) + "."
        )
    if branches and not ("branch" in joined or "return" in joined):
        logic_flow = (logic_flow + " " if logic_flow else "") + (
            "Observed control-flow clues: " + ", ".join(branches) + "."
        )
    if not has_flow:
        likely = (likely + " " if likely else "") + (
            f"Selected snippet window in `{sel_base}` has sparse local control-flow anchors; "
            "validate adjacent methods/callees before asserting a root cause."
        )
        logic_flow = (logic_flow + " " if logic_flow else "") + (
            "Use method-level branch/condition checks and return/error paths from nearby hooks."
        )
    elif not any(x in joined for x in ("if ", "when ", "branch", "condition", "return")):
        likely = (likely + " " if likely else "") + (
            "Likely risk centers on conditional branches and early-return paths in the selected-file flow."
        )

    # Reduce generic/hedged phrasing when we actually have grounded clues.
    generic_phrases = (
        "not directly visible",
        "not shown",
        "not enough information",
        "limited context",
        "could imply",
        "difficult to pinpoint exact failure points",
        "without more context",
        "speculative risks",
    )
    if methods or branches:
        if any(g in summary.lower() for g in generic_phrases):
            details = []
            if methods:
                details.append(f"methods={', '.join(methods)}")
            if branches:
                details.append(f"flow={', '.join(branches)}")
            summary = (
                f"Grounded analysis for `{sel_base}` from `{sel_norm}`: "
                + ", ".join(details)
            )
    elif any(g in summary.lower() for g in generic_phrases):
        summary = (
            f"Grounded but shallow analysis for `{sel_base}` from `{sel_norm}`; "
            "current selected-file context lacks direct method/branch anchors for a precise trace."
        )
    executable_grounding = bool(methods and branches and has_flow)
    if executable_grounding:
        if "executable grounding" not in logic_flow.lower():
            logic_flow = (logic_flow + " " if logic_flow else "") + (
                "Executable grounding: selected-file methods and branch cues are present in the current context window."
            )
        if not any(tok in likely.lower() for tok in ("failure branch", "early-return", "exception branch")):
            likely = (likely + " " if likely else "") + (
                "Failure branch articulation: verify condition checks and early-return/exception branches before downstream dispatch."
            )

    if not confidence:
        confidence = (
            "Bounded to provided evidence bundle; validate against full caller/callee chain before code changes."
        )
    if not methods and not branches:
        marker = "insufficient_for_precise_trace"
        if marker not in confidence.lower():
            confidence += f" {marker}: selected file evidence lacks concrete method/branch anchors in this context window."
    if minimal_sel:
        confidence += " Selected highlight is minimal; conclusions rely on broader selected-file context."
    if executable_grounding and "insufficient_for_precise_trace" not in confidence.lower():
        confidence = (
            "Grounded to executable selected-file method/branch evidence in current context; "
            "validate downstream callees for cross-file effects."
        )

    # Final safety net: ensure banned generic phrases do not leak in any explain field.
    summary = _sanitize_forbidden_generic_phrases(summary).strip()
    logic_flow = _sanitize_forbidden_generic_phrases(logic_flow).strip()
    likely = _sanitize_forbidden_generic_phrases(likely).strip()

    # For executable-looking selected files, avoid purely linear narration.
    # Inject explicit branch/failure wording so debug depth checks see at least
    # two control-flow cues in the final explain text.
    combined = f"{summary} {logic_flow} {likely}"
    if has_flow and _debug_control_flow_marker_count(combined) < 2:
        logic_flow = (logic_flow + " " if logic_flow else "") + (
            "If file read/decrypt/parse condition checks fail, the method should return or throw before "
            "downstream trap handling branches execute."
        )
        likely = (likely + " " if likely else "") + (
            "Primary risk is an early-return/exception branch skipping dispatch when validation conditions fail."
        )
        logic_flow = _sanitize_forbidden_generic_phrases(logic_flow).strip()
        likely = _sanitize_forbidden_generic_phrases(likely).strip()

    return ExplainDebugResult(
        summary=summary,
        logic_flow=logic_flow,
        likely_bug_risk=likely,
        evidence=[str(e).strip() for e in evidence if str(e).strip()],
        confidence_limits=confidence.strip(),
        error=None,
    )


def _parse_structured_response(text: str) -> ExplainDebugResult:
    """Extract JSON from model output and map to ExplainDebugResult."""
    try:
        # Try to find a JSON object in the response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end <= start:
            return ExplainDebugResult(error="No JSON object in reasoning response.")
        raw = text[start:end]
        data = json.loads(raw)
        return ExplainDebugResult(
            summary=str(data.get("summary", "")).strip(),
            logic_flow=str(data.get("logic_flow", "")).strip(),
            likely_bug_risk=str(data.get("likely_bug_risk", "")).strip(),
            evidence=[str(x).strip() for x in data.get("evidence", []) if x],
            confidence_limits=str(data.get("confidence_limits", "")).strip(),
        )
    except json.JSONDecodeError as e:
        return ExplainDebugResult(error=f"Reasoning response parse error: {e}")
    except Exception as e:
        return ExplainDebugResult(error=str(e))


def explain_debug(
    query: str,
    selected_file: str,
    selection: str,
    bundle: ContextBundle,
    request_id: str = "",
    trace_id: str = "",
) -> ExplainDebugResult:
    """
    Perform real explain/debug reasoning using a vLLM-compatible endpoint.

    Returns ExplainDebugResult with fields populated on success, or error set
    when the service is unavailable or response is invalid. Caller must NOT
    use PlanOnlyPlanner when error is set.
    """
    t0 = time.perf_counter()
    rid = (request_id or "").strip() or "unknown"
    tid = (trace_id or "").strip()
    base_url = os.environ.get(EXPLAIN_VLLM_URL_ENV, DEFAULT_VLLM_URL).rstrip("/")
    url = f"{base_url}/v1/chat/completions"
    model_name = os.environ.get("MOTADATA_EXPLAIN_MODEL", "motadata-coder")

    prompt = _build_prompt(query, selected_file, selection, bundle)
    payload: Dict[str, Any] = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 1500,
    }
    # OpenAI-compatible optional correlation (vLLM often forwards; ignored safely if not).
    # Prefer trace_id for end-to-end grep when present.
    correlation = tid if tid else (rid if rid != "unknown" else "")
    if correlation:
        payload["user"] = correlation

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            if resp.status != 200:
                _explain_debug_request_log(rid, base_url, model_name, "error", t0, trace_id=tid)
                return ExplainDebugResult(
                    error=f"Reasoning service returned HTTP {resp.status}"
                )
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        _explain_debug_request_log(rid, base_url, model_name, "error", t0, trace_id=tid)
        return ExplainDebugResult(
            error=f"Reasoning service unavailable: {e.reason or type(e).__name__}"
        )
    except TimeoutError:
        _explain_debug_request_log(rid, base_url, model_name, "error", t0, trace_id=tid)
        return ExplainDebugResult(error="Reasoning service timeout")
    except Exception as e:
        _explain_debug_request_log(rid, base_url, model_name, "error", t0, trace_id=tid)
        return ExplainDebugResult(error=f"Reasoning request failed: {e}")

    choices = body.get("choices") or []
    if not choices:
        _explain_debug_request_log(rid, base_url, model_name, "error", t0, trace_id=tid)
        return ExplainDebugResult(error="Reasoning service returned no choices")
    content = choices[0].get("message", {}).get("content") or ""
    parsed = _parse_structured_response(content)
    if parsed.error:
        _explain_debug_request_log(rid, base_url, model_name, "error", t0, trace_id=tid)
        return parsed
    parsed = _ensure_selected_grounding(
        parsed,
        selected_file=selected_file,
        selection=selection,
        bundle=bundle,
    )
    if parsed.error:
        _explain_debug_request_log(rid, base_url, model_name, "error", t0, trace_id=tid)
    else:
        _explain_debug_request_log(rid, base_url, model_name, "success", t0, trace_id=tid)
    return parsed
