"""
Governed vLLM narration for general Ask (PLAN_ONLY).

Uses the same vLLM endpoint configuration as EXPLAIN_DEBUG (`MOTADATA_EXPLAIN_VLLM_URL`).
Only symbols grounded in `reasoning_context` + plan steps + bundle paths may appear;
responses are validated and rejected to deterministic fallback on any governance violation.

Enable with: MCODER_GOVERNED_ASK_NARRATOR=1
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Set

from runtime.context.contracts import ContextBundle

from runtime.ask_service.articulated_answer import (
    _SCHEMA,
    _evidence_limit_note,
    _supporting_bullets_from_steps,
)
from runtime.ask_service.debug_narration_gate import GENERIC_PHRASES
from runtime.ask_service.reasoning_context import render_reasoning_context_for_prompt

LOG = logging.getLogger(__name__)

GOVERNED_NARRATOR_ENV = "MCODER_GOVERNED_ASK_NARRATOR"
EXPLAIN_VLLM_URL_ENV = "MOTADATA_EXPLAIN_VLLM_URL"
DEFAULT_VLLM_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 55


def _truthy_env(name: str) -> bool:
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}


def governed_ask_narrator_enabled() -> bool:
    return _truthy_env(GOVERNED_NARRATOR_ENV)


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _bundle_path_stems(bundle: ContextBundle) -> Set[str]:
    out: Set[str] = set()
    for it in bundle.items:
        p = str(it.path or "").replace("\\", "/").strip()
        if not p:
            continue
        stem = p.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        if stem:
            out.add(stem)
    return out


def _build_symbol_allowlist(
    reasoning_context: Dict[str, Any],
    plan_steps: List[str],
    bundle: ContextBundle,
) -> Set[str]:
    allow: Set[str] = set()
    rc = _as_dict(reasoning_context)
    po = _as_dict(rc.get("primary_owner"))
    cls = str(po.get("class") or "").strip()
    meth = str(po.get("method") or "").strip()
    if cls:
        allow.add(cls)
    if cls and meth:
        allow.add(f"{cls}.{meth}")
    anchor = str(rc.get("anchor_method") or "").strip()
    if anchor:
        allow.add(anchor)
    typed = _as_dict(rc.get("typed_nodes"))
    for bucket in ("entrypoints", "abstractions", "handlers", "stores", "collaborators"):
        for node in _as_list(typed.get(bucket)):
            if not isinstance(node, dict):
                continue
            c = str(node.get("class") or "").strip()
            m = str(node.get("method") or "").strip()
            if c:
                allow.add(c)
            if c and m:
                allow.add(f"{c}.{m}")
    for ref in _as_list(rc.get("evidence_sources")):
        if not isinstance(ref, dict):
            continue
        inf = str(ref.get("inferred_class") or "").strip()
        if inf:
            allow.add(inf)
    allow |= _bundle_path_stems(bundle)
    text = " ".join(plan_steps)
    for m in re.finditer(r"`([A-Za-z][A-Za-z0-9_.]*)`", text):
        allow.add(m.group(1))
    for m in re.finditer(r"\b([A-Z][a-zA-Z0-9]*(?:\.[A-Z][a-zA-Z0-9]*)*)\b", text):
        tok = m.group(1)
        if "." in tok or len(tok) >= 4:
            allow.add(tok)
    return {x for x in allow if x}


def _backtick_spans(text: str) -> List[str]:
    return re.findall(r"`([^`]+)`", text)


def _token_allowed(tok: str, allow_lower: Set[str]) -> bool:
    t = tok.strip()
    if not t:
        return True
    tl = t.lower()
    if tl in allow_lower:
        return True
    head = t.split(".")[0].lower()
    if head in allow_lower:
        return True
    for a in allow_lower:
        if tl in a or a in tl:
            return True
    return False


def _validate_governed_prose(
    paragraphs: List[str],
    *,
    allowlist: Set[str],
    anchor_method: str,
) -> tuple[bool, List[str]]:
    issues: List[str] = []
    joined = " ".join(paragraphs)
    low = joined.lower()

    for p in GENERIC_PHRASES:
        if p in low:
            issues.append(f"generic_phrase:{p[:40]}")

    if anchor_method:
        am = anchor_method.lower()
        head = anchor_method.split(".", 1)[0].lower()
        if am not in low and head not in low:
            issues.append("primary_anchor_not_referenced")

    allow_lower = {a.lower() for a in allowlist}
    for raw in _backtick_spans(joined):
        raw = str(raw or "").strip()
        if not raw:
            continue
        for part in re.split(r"[,;]\s*", raw):
            c = part.strip()
            if not c:
                continue
            if "/" in c or c.endswith((".java", ".py", ".kt", ".ts", ".go", ".rs")):
                for seg in c.replace("\\", "/").split("/"):
                    st = seg.rsplit(".", 1)[0].strip()
                    if len(st) < 2:
                        continue
                    if not _token_allowed(st, allow_lower):
                        issues.append(f"ungrounded_path_segment:{st}")
            else:
                if not _token_allowed(c, allow_lower):
                    issues.append(f"ungrounded_symbol:{c}")

    for i, para in enumerate(paragraphs):
        if len(para) > 900:
            issues.append(f"paragraph_{i}_too_long")

    if len(paragraphs) < 1 or len(paragraphs) > 5:
        issues.append("paragraph_count_out_of_range")

    return (len(issues) == 0, issues)


def _parse_narration_json(text: str) -> Optional[Dict[str, Any]]:
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end <= start:
            return None
        data = json.loads(text[start:end])
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _build_governed_prompt(
    *,
    query: str,
    reasoning_context_block: str,
    plan_steps: List[str],
    bundle: ContextBundle,
    evidence_quality: str,
) -> str:
    lines = [
        "You write concise developer-facing explanations for Motadata Ask (read-only, PLAN_ONLY).",
        "Use ONLY classes, methods, and files that appear in the sections below. Do not invent types, APIs, or behavior.",
        "",
        "## Reasoning context (ground-truth roles and anchors)",
        reasoning_context_block or "Reasoning Context: unavailable",
        "",
        "## Plan steps (deterministic; treat as authoritative structure hints)",
    ]
    for s in plan_steps[:24]:
        lines.append(f"- {s}")
    lines.extend(
        [
            "",
            "## Repository excerpts (evidence; cite only what appears here)",
        ]
    )
    for item in bundle.items[:8]:
        body = (item.content or "")[:6000]
        lines.append(f"### {item.path}")
        lines.append("```")
        lines.append(body + ("..." if len(item.content or "") > 6000 else ""))
        lines.append("```")
        lines.append("")
    lines.extend(
        [
            "## User question",
            query,
            "",
            f"Evidence quality signal: {evidence_quality or 'unknown'}.",
            "",
            "## Output contract (must follow)",
            "- Write 2–4 short paragraphs (plain sentences, confident tone).",
            "- Use active verbs: handles, routes, delegates, coordinates, persists.",
            "- Name symbols with backticks (e.g. `ClassName.method`). Only names from sections above.",
            "- End with exactly ONE sentence stating what is not fully visible or proven from this snapshot (limits only).",
            "- Do not use diagnostic phrases like 'Flow evidence indicates', 'Graph path', or 'receives or initiates processing'.",
            '- Respond with a single JSON object (no markdown fences) with keys: '
            '"paragraphs" (array of strings, each a paragraph), '
            '"evidence_limit" (one short sentence echoing grounding limits).',
        ]
    )
    return "\n".join(lines)


def try_governed_ask_narration(
    *,
    query: str,
    bundle: ContextBundle,
    plan_steps: List[str],
    metadata: Dict[str, Any],
    request_id: str = "",
    trace_id: str = "",
) -> Optional[Dict[str, Any]]:
    """
    Returns an articulated_answer-shaped dict on success, or None to fall back to deterministic composer.
    """
    if not governed_ask_narrator_enabled():
        return None

    eq = str(metadata.get("evidence_quality") or "").upper()
    if eq == "NO_MATCH":
        return None

    rc = _as_dict(metadata.get("reasoning_context"))
    if not rc:
        return None

    allowlist = _build_symbol_allowlist(rc, plan_steps, bundle)
    if len(allowlist) < 2:
        return None

    anchor_method = str(rc.get("anchor_method") or "").strip()
    rc_block = render_reasoning_context_for_prompt(rc)
    prompt = _build_governed_prompt(
        query=query,
        reasoning_context_block=rc_block,
        plan_steps=plan_steps,
        bundle=bundle,
        evidence_quality=eq,
    )

    base_url = os.environ.get(EXPLAIN_VLLM_URL_ENV, DEFAULT_VLLM_URL).rstrip("/")
    url = f"{base_url}/v1/chat/completions"
    model_name = os.environ.get("MOTADATA_EXPLAIN_MODEL", "motadata-coder")
    rid = (request_id or "").strip() or "unknown"
    tid = (trace_id or "").strip()
    t0 = time.perf_counter()

    payload: Dict[str, Any] = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.25,
        "max_tokens": 900,
    }
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
                LOG.info(
                    "GOVERNED_ASK_NARRATOR request_id=%s http=%s duration_ms=%.1f",
                    rid,
                    resp.status,
                    (time.perf_counter() - t0) * 1000.0,
                )
                return None
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as e:
        LOG.info(
            "GOVERNED_ASK_NARRATOR request_id=%s failed=%s duration_ms=%.1f",
            rid,
            type(e).__name__,
            (time.perf_counter() - t0) * 1000.0,
        )
        return None

    choices = body.get("choices") or []
    if not choices:
        return None
    content = choices[0].get("message", {}).get("content") or ""
    data = _parse_narration_json(content)
    if not data:
        return None
    paras = data.get("paragraphs")
    if not isinstance(paras, list):
        return None
    paragraphs = [str(p).strip() for p in paras if str(p).strip()]
    if not paragraphs:
        return None

    ok, issues = _validate_governed_prose(
        paragraphs,
        allowlist=allowlist,
        anchor_method=anchor_method,
    )
    if not ok:
        LOG.info(
            "GOVERNED_ASK_NARRATOR request_id=%s rejected issues=%s",
            rid,
            issues[:8],
        )
        return None

    ev_limit = str(data.get("evidence_limit") or "").strip()
    if not ev_limit:
        ev_limit = _evidence_limit_note(metadata)

    out: Dict[str, Any] = {
        "schema_version": _SCHEMA,
        "paragraphs": paragraphs[:4],
        "supporting_plan_bullets": _supporting_bullets_from_steps(plan_steps)[:5],
        "evidence_limit": ev_limit,
        "shape": "governed_vllm_contract",
        "narration_source": "governed_vllm",
    }
    LOG.info(
        "GOVERNED_ASK_NARRATOR request_id=%s ok paragraphs=%s duration_ms=%.1f",
        rid,
        len(paragraphs),
        (time.perf_counter() - t0) * 1000.0,
    )
    return out
