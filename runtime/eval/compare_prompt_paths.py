#!/usr/bin/env python3
"""
Diagnostic-only A/B prompt path comparison for Ask responses.

Compares three paths for the same query/evidence bundle:
A) Full mcoder path (Context Layer -> /v1/ask -> CLI-style answer shaping)
B) Raw Plan-Gate response (/v1/ask before CLI shaping)
C) Direct vLLM (Context evidence bundle + authority + structural graph)

Strictly diagnostic:
- No production path mutations
- No retrieval/graph/Plan-Gate/schema changes
- Read-only HTTP calls and local markdown report write
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

from runtime.ask_service.graph_traversal_payload import build_graph_traversal_payload
from runtime.ask_service.reasoning_context import (
    build_reasoning_context,
    citations_present,
    render_reasoning_context_for_prompt,
)
from runtime.mcoder_cli.answer_shaping import shape_prompt_summary

DEFAULT_QUERIES: List[str] = [
    "Explain the API layer architecture.",
    "How does mail server configuration work?",
    "Find all classes that handle notifications.",
    "How are config stores organized?",
]


def _now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _http_post_json(url: str, payload: Dict[str, Any], timeout_sec: int) -> Tuple[int, Dict[str, Any], float, str]:
    t0 = time.perf_counter()
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            body = json.loads(resp.read().decode("utf-8"))
            return int(resp.getcode()), body if isinstance(body, dict) else {}, latency_ms, ""
    except urllib.error.HTTPError as exc:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        raw = exc.read().decode("utf-8", errors="replace")
        err_body: Dict[str, Any] = {}
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                err_body = parsed
        except Exception:
            pass
        return int(exc.code), err_body, latency_ms, raw[:600]
    except Exception as exc:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return 0, {}, latency_ms, str(exc)


def _export_evidence(
    *,
    context_url: str,
    workspace_root: str,
    query: str,
    top_k: int,
    timeout_sec: int,
) -> Tuple[Dict[str, Any], float, str]:
    payload: Dict[str, Any] = {
        "workspace_root": workspace_root,
        "query": query,
        "top_k": top_k,
        "task_type": "general",
    }
    status, body, latency_ms, err = _http_post_json(
        f"{context_url.rstrip('/')}/v1/export_evidence", payload, timeout_sec
    )
    if status != 200:
        return {}, latency_ms, f"export_evidence http={status} {err}".strip()
    return body, latency_ms, ""


def _ask_v1(
    *,
    plan_gate_url: str,
    query: str,
    evidence: Dict[str, Any],
    timeout_sec: int,
) -> Tuple[Dict[str, Any], float, str]:
    req: Dict[str, Any] = {
        "schema_version": "ask_request.v1.0",
        "request_id": str(uuid.uuid4()),
        "timestamp_utc": _now_utc(),
        "query": query,
        "task_type": "general",
        "evidence_bundle": evidence,
    }
    ws_hash = evidence.get("workspace_identity_hash")
    if ws_hash:
        req["expected_workspace_identity_hash"] = ws_hash

    status, body, latency_ms, err = _http_post_json(
        f"{plan_gate_url.rstrip('/')}/v1/ask", req, timeout_sec
    )
    if status != 200:
        return {}, latency_ms, f"/v1/ask http={status} {err}".strip()
    return body, latency_ms, ""


def _extract_raw_answer_text(resp: Dict[str, Any]) -> str:
    art = resp.get("articulated_answer")
    if isinstance(art, dict):
        paras = art.get("paragraphs")
        if isinstance(paras, list):
            joined = "\n\n".join(str(p).strip() for p in paras if str(p).strip())
            if joined.strip():
                return joined.strip()

    ps = resp.get("plan_summary")
    if isinstance(ps, dict):
        steps = ps.get("steps")
        if isinstance(steps, list):
            lines = [str(s).strip() for s in steps if str(s).strip()]
            if lines:
                return "\n".join(f"- {line}" for line in lines)

    ed = resp.get("explain_debug")
    if isinstance(ed, dict) and str(ed.get("summary") or "").strip():
        return str(ed.get("summary") or "").strip()

    return ""


def _extract_shaped_answer_text(query: str, resp: Dict[str, Any]) -> str:
    shaped = shape_prompt_summary(query, resp)
    a1 = str(shaped.get("answer_1") or "").strip()
    n1 = str(shaped.get("next_step") or "").strip()
    if a1 and n1:
        return f"{a1}\n\n{n1}"
    return a1 or n1 or _extract_raw_answer_text(resp)


def _build_evidence_blocks(evidence: Dict[str, Any], max_entries: int = 10) -> Tuple[str, List[str]]:
    entries = evidence.get("entries") if isinstance(evidence.get("entries"), list) else []
    rows: List[str] = []
    anchor_ids: List[str] = []
    for i, ent in enumerate(entries[:max_entries], start=1):
        if not isinstance(ent, dict):
            continue
        rel = str(ent.get("relative_path") or "")
        score = ent.get("retrieval_score")
        snip = ent.get("snippet") if isinstance(ent.get("snippet"), dict) else {}
        start = snip.get("start_line")
        end = snip.get("end_line")
        text = str(snip.get("text") or "").strip()
        text = re.sub(r"\s+", " ", text)
        text = text[:420]
        anchor = f"E{i}"
        anchor_ids.append(anchor)
        line_span = ""
        if isinstance(start, int) and isinstance(end, int):
            line_span = f"#L{start}-L{end}"
        rows.append(
            f"[{anchor}] {rel}{line_span} score={score} excerpt=\"{text}\""
        )
    return "\n".join(rows), anchor_ids


def _direct_vllm_prompt(query: str, evidence: Dict[str, Any]) -> str:
    authority = evidence.get("authority_resolution") if isinstance(evidence.get("authority_resolution"), dict) else {}
    gt_payload = build_graph_traversal_payload(
        query=query,
        task_type="general",
        authority_resolution=authority if authority else None,
        selected_file="",
    )
    reasoning_context = build_reasoning_context(
        query=query,
        evidence_bundle=evidence,
        graph_traversal=gt_payload,
    )
    ev_text, _ = _build_evidence_blocks(evidence)
    rc_block = render_reasoning_context_for_prompt(reasoning_context)

    return (
        "You are a governed coding assistant.\n"
        "\n"
        "Answer the user's query using ONLY the provided reasoning context and evidence.\n"
        "\n"
        "---\n"
        "\n"
        f"QUERY:\n{query}\n"
        "\n"
        "---\n"
        "\n"
        f"REASONING CONTEXT:\n{rc_block}\n"
        "\n"
        f"EVIDENCE ANCHORS:\n{ev_text}\n"
        "\n"
        "---\n"
        "\n"
        "RULES (strict):\n"
        "\n"
        "1) Grounding\n"
        "- Use only anchors, nodes, and flows present in the reasoning context.\n"
        "- You may infer roles from names (e.g. Abstract*, beforeUpdate, *Store), but do NOT invent classes, methods, or unseen paths.\n"
        "\n"
        "2) Bounded inference\n"
        "- Allowed: infer roles (entrypoint, abstraction, lifecycle hook, store, collaborator).\n"
        "- Not allowed: invent facts, new relationships, or claim certainty without support.\n"
        "\n"
        "3) Structure (write naturally, not as bullets)\n"
        "- 2-4 concise sentences total.\n"
        "- Explain as a flow: entrypoint -> abstraction -> implementation -> collaborators (when available).\n"
        "\n"
        "4) Fluency\n"
        "- Write like a senior engineer explaining the system.\n"
        "- Avoid repetitive hedging (don't say appears/likely in every clause).\n"
        "- Keep it tight, readable, and confident where supported.\n"
        "\n"
        "5) Confidence limits\n"
        "- End with ONE short sentence stating what is not fully proven by the current context.\n"
        "\n"
        "6) No diagnostics\n"
        "- Do not mention 'graph', 'partial evidence', or internal system terms.\n"
        "- Do not dump chains or raw snippets.\n"
        "\n"
        "---\n"
        "\n"
        "ANSWER:"
    )


def _call_direct_vllm(
    *,
    vllm_url: str,
    model: str,
    query: str,
    evidence: Dict[str, Any],
    timeout_sec: int,
) -> Tuple[str, float, str]:
    prompt = _direct_vllm_prompt(query, evidence)
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 900,
        "user": f"compare_prompt_paths:{uuid.uuid4()}",
    }
    status, body, latency_ms, err = _http_post_json(
        f"{vllm_url.rstrip('/')}/v1/chat/completions", payload, timeout_sec
    )
    if status != 200:
        return "", latency_ms, f"direct_vllm http={status} {err}".strip()
    choices = body.get("choices") if isinstance(body.get("choices"), list) else []
    if not choices:
        return "", latency_ms, "direct_vllm no choices"
    first = choices[0] if isinstance(choices[0], dict) else {}
    msg = first.get("message") if isinstance(first.get("message"), dict) else {}
    content = str(msg.get("content") or "").strip()
    if not content:
        return "", latency_ms, "direct_vllm empty content"
    return content, latency_ms, ""


def _detect_hallucination_markers(answer_text: str, evidence: Dict[str, Any]) -> List[str]:
    markers: List[str] = []
    text = str(answer_text or "")
    if not text.strip():
        return ["empty_answer"]

    citation_hits = re.findall(r"\bE\d+\b|\bG\d+\b", text)
    path_hits = re.findall(r"[A-Za-z0-9_./\\-]+\.(?:java|kt|py|yml|yaml|xml|json)", text)
    # backtick-quoted class/method names count as grounded references
    backtick_ids = re.findall(r"`[A-Z][A-Za-z0-9_]+(?:\.[a-zA-Z][A-Za-z0-9_]*)?`", text)
    if not citation_hits and not path_hits and not backtick_ids:
        markers.append("missing_anchor_citations")

    entries = evidence.get("entries") if isinstance(evidence.get("entries"), list) else []
    allowed_paths = {
        str(ent.get("relative_path") or "").strip().lower()
        for ent in entries
        if isinstance(ent, dict)
    }
    mentioned_paths = {
        m.strip().lower()
        for m in re.findall(r"[A-Za-z0-9_./\\-]+\.(?:java|kt|py|yml|yaml|xml|json)", text)
    }
    unknown_paths = [p for p in sorted(mentioned_paths) if p and p not in allowed_paths]
    if unknown_paths:
        markers.append("mentions_paths_not_in_evidence")

    total_grounding = len(citation_hits) + len(path_hits) + len(backtick_ids)
    if "unknown based on provided evidence" not in text.lower() and total_grounding <= 1:
        markers.append("low_uncertainty_signaling")

    return markers


def _fluency_depth_notes(answer_text: str) -> str:
    txt = str(answer_text or "").strip()
    if not txt:
        return "stiff/shallow"

    words = re.findall(r"\b\w+\b", txt)
    word_count = len(words)
    sentence_count = max(1, len(re.findall(r"[.!?]", txt)))
    bullet_count = len(re.findall(r"^\s*[-*]", txt, flags=re.MULTILINE))

    fluency = "fluent" if sentence_count >= 3 and bullet_count <= 4 else "stiff"
    depth = "deep" if word_count >= 110 else "shallow"
    return f"{fluency}/{depth}"


def _graph_presence_for_evidence(evidence: Dict[str, Any]) -> bool:
    structural = evidence.get("structural_context")
    if isinstance(structural, dict) and structural:
        return True
    authority = evidence.get("authority_resolution")
    if isinstance(authority, dict) and authority:
        return True
    return False


def _truncate(text: str, limit: int = 1800) -> str:
    raw = str(text or "")
    return raw if len(raw) <= limit else (raw[: limit - 3] + "...")


def _render_report(
    *,
    workspace_root: str,
    context_url: str,
    plan_gate_url: str,
    vllm_url: str,
    model: str,
    top_k: int,
    timeout_sec: int,
    rows: List[Dict[str, Any]],
) -> str:
    out: List[str] = []
    out.append("# Prompt Path Diagnostic Report")
    out.append("")
    out.append(f"Generated: {_now_utc()}")
    out.append(f"Workspace: {workspace_root}")
    out.append(f"Context URL: {context_url}")
    out.append(f"Plan-Gate URL: {plan_gate_url}")
    out.append(f"vLLM URL: {vllm_url}")
    out.append(f"Model: {model}")
    out.append(f"top_k: {top_k}")
    out.append(f"timeout_sec: {timeout_sec}")
    out.append("")
    out.append("## Summary Table")
    out.append("")
    out.append("| Query | Path | graph_traversal_presence | latency_ms | hallucination_markers | notes |")
    out.append("|---|---|---:|---:|---|---|")

    for row in rows:
        markers = ", ".join(row.get("hallucination_markers", [])) if row.get("hallucination_markers") else "none"
        out.append(
            "| {q} | {p} | {g} | {l:.1f} | {m} | {n} |".format(
                q=row.get("query", "").replace("|", "\\|"),
                p=row.get("path", "").replace("|", "\\|"),
                g="yes" if row.get("graph_traversal_presence") else "no",
                l=float(row.get("latency_ms") or 0.0),
                m=markers.replace("|", "\\|"),
                n=str(row.get("notes") or "").replace("|", "\\|"),
            )
        )

    out.append("")
    out.append("## Per-Query Outputs")
    out.append("")

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("query") or ""), []).append(row)

    for query, qrows in grouped.items():
        out.append(f"### {query}")
        out.append("")
        for row in qrows:
            out.append(f"#### Path {row.get('path')}")
            out.append("")
            out.append(f"- latency_ms: {float(row.get('latency_ms') or 0.0):.1f}")
            out.append(f"- graph_traversal_presence: {'yes' if row.get('graph_traversal_presence') else 'no'}")
            marks = row.get("hallucination_markers") or []
            out.append(f"- hallucination_markers: {', '.join(marks) if marks else 'none'}")
            out.append(f"- notes: {row.get('notes')}")
            err = str(row.get("error") or "").strip()
            if err:
                out.append(f"- error: {err}")
            out.append("")
            out.append("Answer text:")
            out.append("")
            out.append("```")
            out.append(_truncate(str(row.get("answer_text") or ""), limit=4000))
            out.append("```")
            out.append("")

    return "\n".join(out).rstrip() + "\n"


def _run_query(
    *,
    query: str,
    workspace_root: str,
    context_url: str,
    plan_gate_url: str,
    vllm_url: str,
    model: str,
    top_k: int,
    timeout_sec: int,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    evidence, export_ms, export_err = _export_evidence(
        context_url=context_url,
        workspace_root=workspace_root,
        query=query,
        top_k=top_k,
        timeout_sec=timeout_sec,
    )
    if export_err:
        for path_id in ("A", "B", "C"):
            results.append(
                {
                    "query": query,
                    "path": path_id,
                    "answer_text": "",
                    "graph_traversal_presence": False,
                    "latency_ms": export_ms,
                    "hallucination_markers": ["export_failure"],
                    "notes": "stiff/shallow",
                    "error": export_err,
                }
            )
        return results

    ask_resp, ask_ms, ask_err = _ask_v1(
        plan_gate_url=plan_gate_url,
        query=query,
        evidence=evidence,
        timeout_sec=timeout_sec,
    )

    if ask_err:
        for path_id in ("A", "B"):
            results.append(
                {
                    "query": query,
                    "path": path_id,
                    "answer_text": "",
                    "graph_traversal_presence": False,
                    "latency_ms": ask_ms,
                    "hallucination_markers": ["ask_failure"],
                    "notes": "stiff/shallow",
                    "error": ask_err,
                }
            )
    else:
        answer_a = _extract_shaped_answer_text(query, ask_resp)
        markers_a = _detect_hallucination_markers(answer_a, evidence)
        results.append(
            {
                "query": query,
                "path": "A",
                "answer_text": answer_a,
                "graph_traversal_presence": bool(isinstance(ask_resp.get("graph_traversal"), dict) and ask_resp.get("graph_traversal")),
                "latency_ms": export_ms + ask_ms,
                "hallucination_markers": markers_a,
                "notes": _fluency_depth_notes(answer_a),
                "error": "",
            }
        )

        answer_b = _extract_raw_answer_text(ask_resp)
        markers_b = _detect_hallucination_markers(answer_b, evidence)
        results.append(
            {
                "query": query,
                "path": "B",
                "answer_text": answer_b,
                "graph_traversal_presence": bool(isinstance(ask_resp.get("graph_traversal"), dict) and ask_resp.get("graph_traversal")),
                "latency_ms": export_ms + ask_ms,
                "hallucination_markers": markers_b,
                "notes": _fluency_depth_notes(answer_b),
                "error": "",
            }
        )

    direct_text, direct_ms, direct_err = _call_direct_vllm(
        vllm_url=vllm_url,
        model=model,
        query=query,
        evidence=evidence,
        timeout_sec=timeout_sec,
    )
    if direct_err:
        results.append(
            {
                "query": query,
                "path": "C",
                "answer_text": "",
                "graph_traversal_presence": _graph_presence_for_evidence(evidence),
                "latency_ms": export_ms + direct_ms,
                "hallucination_markers": ["direct_vllm_failure"],
                "notes": "stiff/shallow",
                "error": direct_err,
            }
        )
    else:
        markers_c = _detect_hallucination_markers(direct_text, evidence)
        results.append(
            {
                "query": query,
                "path": "C",
                "answer_text": direct_text,
                "graph_traversal_presence": _graph_presence_for_evidence(evidence),
                "latency_ms": export_ms + direct_ms,
                "hallucination_markers": markers_c,
                "notes": _fluency_depth_notes(direct_text),
                "error": "",
            }
        )

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnostic-only compare of A/B/C prompt paths.")
    parser.add_argument("--workspace-root", default=os.environ.get("MOTADATA_REPO_ROOT", ""), help="Workspace root sent to Context Layer export_evidence")
    parser.add_argument("--context-url", default="http://127.0.0.1:8091")
    parser.add_argument("--plan-gate-url", default="http://127.0.0.1:8089")
    parser.add_argument("--vllm-url", default=os.environ.get("MOTADATA_EXPLAIN_VLLM_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--model", default=os.environ.get("MOTADATA_EXPLAIN_MODEL", "motadata-coder"))
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--timeout-sec", type=int, default=180)
    parser.add_argument("--query", action="append", dest="queries", default=[], help="Repeatable query override. If omitted, uses the 4 diagnostic queries.")
    parser.add_argument(
        "--report-out",
        default="runtime/eval/compare_prompt_paths_report.md",
        help="Markdown report output path",
    )
    args = parser.parse_args()

    workspace_root = str(args.workspace_root or "").strip()
    if not workspace_root:
        workspace_root = str(Path(__file__).resolve().parents[2])

    queries = args.queries if args.queries else list(DEFAULT_QUERIES)
    all_rows: List[Dict[str, Any]] = []

    print("[diag] compare_prompt_paths starting")
    print(f"[diag] workspace_root={workspace_root}")
    for idx, q in enumerate(queries, start=1):
        print(f"[diag] ({idx}/{len(queries)}) {q}")
        all_rows.extend(
            _run_query(
                query=q,
                workspace_root=workspace_root,
                context_url=args.context_url,
                plan_gate_url=args.plan_gate_url,
                vllm_url=args.vllm_url,
                model=args.model,
                top_k=int(args.top_k),
                timeout_sec=int(args.timeout_sec),
            )
        )

    report_text = _render_report(
        workspace_root=workspace_root,
        context_url=args.context_url,
        plan_gate_url=args.plan_gate_url,
        vllm_url=args.vllm_url,
        model=args.model,
        top_k=int(args.top_k),
        timeout_sec=int(args.timeout_sec),
        rows=all_rows,
    )

    report_path = Path(args.report_out)
    if not report_path.is_absolute():
        report_path = Path(__file__).resolve().parents[2] / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding="utf-8")

    print(f"[diag] report written: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
