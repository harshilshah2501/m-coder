"""
ExplainDebugReasoner — Real code reasoning for EXPLAIN_DEBUG task type.

Invoked only when task_type=EXPLAIN_DEBUG and selected_file + selection are present.
Calls a vLLM-compatible HTTP completion endpoint; does NOT use template planner.
If the service is unavailable or parsing fails, the caller must NOT substitute
template steps (return explain_debug.error instead).
"""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Dict, List

from runtime.context.contracts import ContextBundle


EXPLAIN_VLLM_URL_ENV = "MOTADATA_EXPLAIN_VLLM_URL"
DEFAULT_VLLM_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 60


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


def _build_prompt(
    query: str,
    selected_file: str,
    selection: str,
    bundle: ContextBundle,
) -> str:
    """Build a prompt for explain/debug from context bundle and selection."""
    lines = [
        "You are analyzing a code selection from a repository. Provide a structured analysis.",
        "",
        "## Selected file",
        selected_file,
        "",
        "## Selected code",
        "```",
        selection.strip() or "(no selection text)",
        "```",
        "",
        "## Repository context (relevant files)",
    ]
    for item in bundle.items[:10]:
        lines.append(f"### {item.path}")
        lines.append("```")
        lines.append(item.content[:8000] + ("..." if len(item.content) > 8000 else ""))
        lines.append("```")
        lines.append("")
    lines.append("## User question")
    lines.append(query)
    lines.append("")
    lines.append(
        "Respond with a single JSON object (no markdown fences) with these exact keys: "
        '"summary" (string), "logic_flow" (string), "likely_bug_risk" (string), '
        '"evidence" (array of strings, file/method references), "confidence_limits" (string).'
    )
    return "\n".join(lines)


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
) -> ExplainDebugResult:
    """
    Perform real explain/debug reasoning using a vLLM-compatible endpoint.

    Returns ExplainDebugResult with fields populated on success, or error set
    when the service is unavailable or response is invalid. Caller must NOT
    use PlanOnlyPlanner when error is set.
    """
    base_url = os.environ.get(EXPLAIN_VLLM_URL_ENV, DEFAULT_VLLM_URL).rstrip("/")
    url = f"{base_url}/v1/chat/completions"

    prompt = _build_prompt(query, selected_file, selection, bundle)
    payload = {
        "model": os.environ.get("MOTADATA_EXPLAIN_MODEL", "motadata-coder"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 1500,
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            if resp.status != 200:
                return ExplainDebugResult(
                    error=f"Reasoning service returned HTTP {resp.status}"
                )
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return ExplainDebugResult(
            error=f"Reasoning service unavailable: {e.reason or type(e).__name__}"
        )
    except TimeoutError:
        return ExplainDebugResult(error="Reasoning service timeout")
    except Exception as e:
        return ExplainDebugResult(error=f"Reasoning request failed: {e}")

    choices = body.get("choices") or []
    if not choices:
        return ExplainDebugResult(error="Reasoning service returned no choices")
    content = choices[0].get("message", {}).get("content") or ""
    return _parse_structured_response(content)
