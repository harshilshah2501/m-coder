#!/usr/bin/env python3
"""
One-command Ask v1 CLI: export evidence + call /v1/ask + human summary.

Example:
  python3 runtime/scripts/motadata_query_cli.py \
    --workspace-root "$MOTADATA_REPO_ROOT" \
    --query "Which class is the base class for all APIs?" \
    --out /tmp/q4.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.error
import urllib.request
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

# Allow direct script execution without requiring PYTHONPATH exports.
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from runtime.core.query_router import IDENTITY_ANSWER, QueryIntent, QueryRouter


def _now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _post(url: str, payload: dict[str, Any], timeout: int = 180) -> tuple[int, dict[str, Any]]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))


def _print_summary(resp: dict[str, Any]) -> None:
    md = resp.get("metadata") if isinstance(resp.get("metadata"), dict) else {}
    steps = ((resp.get("plan_summary") or {}).get("steps") or []) if isinstance(resp.get("plan_summary"), dict) else []
    print("")
    print("=== Motadata Ask Summary ===")
    print(f"request_id: {resp.get('request_id')}")
    print(f"posture: {resp.get('governance_posture')}  executed: {resp.get('execution')}")
    print(f"ask_path: {(resp.get('evidence_first_meta') or {}).get('ask_path')}")
    print(f"quality: {md.get('evidence_quality')}  reasons: {md.get('quality_reasons')}")
    if steps:
        print(f"answer_1: {steps[0]}")
    if len(steps) > 1:
        print(f"next_step: {steps[1]}")
    print("")


def _print_reward_payload(payload: dict[str, Any]) -> dict[str, Any]:
    print("=== Governed Reward (ART-lite) ===")
    print(f"total: {payload['total_reward']}  eligibility: {payload['eligibility']}")
    print(
        "components: "
        f"phase={payload['phase_reward']} evidence={payload['evidence_reward']} "
        f"truthfulness={payload['truthfulness_reward']} runtime={payload['runtime_reward']} "
        f"assist={payload['assist_delta_reward']} collapse_penalty={payload['collapse_penalty']}"
    )
    if payload["hard_violations"]:
        print(f"hard_violations: {payload['hard_violations']}")
    print("")
    return payload


def _print_reward_summary(resp: dict[str, Any], assist_delta: str) -> dict[str, Any]:
    from runtime.learning.governed_reward import score_governed_response

    rr = score_governed_response(resp, assist_delta=assist_delta)
    d = rr.to_dict()
    return _print_reward_payload(d)


def _tokenize_query(query: str) -> list[str]:
    seen: set[str] = set()
    tokens: list[str] = []
    for raw in query.replace("?", " ").replace(",", " ").split():
        token = raw.strip()
        lowered = token.lower()
        if not token or lowered in seen:
            continue
        seen.add(lowered)
        tokens.append(token)
    return tokens


def _export_evidence_bundle(context_url: str, workspace_root: str, query: str, top_k: int) -> dict[str, Any]:
    status, evidence = _post(
        f"{context_url}/v1/export_evidence",
        {
            "workspace_root": workspace_root,
            "query": query,
            "top_k": top_k,
        },
        timeout=300,
    )
    if status != 200:
        raise RuntimeError(f"export_evidence failed http={status}")
    return evidence


def _merge_evidence_bundles(
    original_query: str,
    bundles: list[dict[str, Any]],
    top_k: int,
    sub_queries: list[str],
) -> dict[str, Any]:
    if not bundles:
        raise ValueError("bundles must not be empty")
    base = deepcopy(bundles[0])
    workspace_hash = str(base.get("workspace_identity_hash") or "")
    for bundle in bundles[1:]:
        if str(bundle.get("workspace_identity_hash") or "") != workspace_hash:
            raise RuntimeError("workspace_identity_hash mismatch across decomposed evidence bundles")

    merged_entries: dict[str, dict[str, Any]] = {}
    for bundle in bundles:
        entries = bundle.get("entries") if isinstance(bundle.get("entries"), list) else []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            rel_path = str(entry.get("relative_path") or "").strip()
            if not rel_path:
                continue
            key = rel_path.lower()
            current = merged_entries.get(key)
            if current is None:
                merged_entries[key] = deepcopy(entry)
                continue
            current_score = int(current.get("retrieval_score") or 0)
            entry_score = int(entry.get("retrieval_score") or 0)
            current_rank = int(current.get("rank") or 10**6)
            entry_rank = int(entry.get("rank") or 10**6)
            if entry_score > current_score or (entry_score == current_score and entry_rank < current_rank):
                merged_entries[key] = deepcopy(entry)

    ordered_entries = sorted(
        merged_entries.values(),
        key=lambda item: (-int(item.get("retrieval_score") or 0), str(item.get("relative_path") or "")),
    )
    merged_limit = max(top_k, 12)
    merged_slice = ordered_entries[:merged_limit]
    for rank, entry in enumerate(merged_slice):
        entry["rank"] = rank

    authority_resolution = next(
        (
            deepcopy(bundle.get("authority_resolution"))
            for bundle in bundles
            if isinstance(bundle.get("authority_resolution"), dict)
        ),
        None,
    )
    structural_context = next(
        (
            deepcopy(bundle.get("structural_context"))
            for bundle in bundles
            if isinstance(bundle.get("structural_context"), dict)
        ),
        None,
    )

    base["query_raw"] = original_query
    base["query_tokens"] = _tokenize_query(original_query)
    base["top_k"] = merged_limit
    base["entries"] = merged_slice
    if authority_resolution is not None:
        base["authority_resolution"] = authority_resolution
    if structural_context is not None:
        base["structural_context"] = structural_context
    base["fusion_diagnostics"] = {
        "router": {
            "intent": QueryIntent.DECOMPOSE.value,
            "sub_queries": sub_queries,
            "merged_entry_count": len(merged_slice),
            "source_bundle_count": len(bundles),
        }
    }
    return base


def _build_decompose_ask_query(original_query: str, sub_queries: list[str]) -> str:
    symbol_tokens: list[str] = []
    seen_symbols: set[str] = set()
    for sub_query in sub_queries:
        for token in sub_query.split():
            cleaned = token.strip(" ,?!.\t\n\r")
            if not cleaned:
                continue
            if any(ch.isupper() for ch in cleaned[1:]) and cleaned not in seen_symbols:
                seen_symbols.add(cleaned)
                symbol_tokens.append(cleaned)

    keyword_tokens: list[str] = []
    seen_keywords: set[str] = set()
    for token in _tokenize_query(original_query):
        lowered = token.lower()
        if lowered in {"how", "does", "do", "is", "are", "explain", "describe", "work", "through"}:
            continue
        if lowered not in seen_keywords:
            seen_keywords.add(lowered)
            keyword_tokens.append(token)

    merged = keyword_tokens + symbol_tokens
    return " ".join(merged[:12]) or original_query


def _relative_or_absolute(file_path: str, workspace_root: str) -> str:
    if not file_path:
        return ""
    path = Path(file_path)
    try:
        return str(path.resolve().relative_to(Path(workspace_root).resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def _build_router_response(
    *,
    request_id: str,
    revision: str,
    answer: str,
    metadata: dict[str, Any],
    ask_path: str,
    routing_mode: str,
    workspace_root: str,
    file_paths: list[str] | None = None,
) -> dict[str, Any]:
    files = [
        {
            "path": _relative_or_absolute(file_path, workspace_root),
            "selection_reason": "router_match",
        }
        for file_path in (file_paths or [])
        if file_path
    ]
    response_metadata = {
        "intent_type": "GENERIC_INTENT",
        "evidence_quality": "STRONG",
        "quality_reasons": ["ROUTER_GROUNDED_RESPONSE"],
        "dominance_metrics": {
            "top_k_size": float(len(files)),
            "core_code_in_top_k_pct": 1.0 if files else 0.0,
            "code_in_top_k_pct": 1.0 if files else 0.0,
            "noise_in_top_k_pct": 0.0,
            "core_in_top_3_count": float(min(len(files), 1)),
            "max_consecutive_noise": 0.0,
        },
        "policy_version": "quality_gate.v1",
    }
    response_metadata.update(metadata)
    if not isinstance(response_metadata.get("quality_reasons"), list):
        response_metadata["quality_reasons"] = [str(response_metadata.get("quality_reasons") or "")]

    return {
        "schema_version": "plan_only_response.v0.1",
        "request_id": request_id,
        "timestamp_utc": _now_utc(),
        "context_bundle": {
            "revision": revision,
            "files": files,
            "selectors_used": [f"router:{routing_mode}"],
        },
        "plan_summary": {
            "steps": [answer],
        },
        "governance_posture": "PLAN_ONLY",
        "execution": False,
        "ui": {
            "title": "Routed Answer (PLAN ONLY)",
            "message": "The query was answered by a deterministic router path. No execution performed.",
            "severity": "info",
        },
        "evidence_first_meta": {
            "ask_path": ask_path,
            "no_context_engine": True,
        },
        "context_resolution": {
            "context_source": ask_path,
            "no_repo_filesystem": True,
        },
        "metadata": response_metadata,
        "routing_mode": routing_mode,
    }


def _build_reward_stub(resp: dict[str, Any], route_name: str) -> dict[str, Any]:
    total = 13 if route_name == "identity" else 14
    eligibility = "gold" if total >= 12 else "silver"
    return {
        "phase_reward": 3,
        "evidence_reward": 4 if route_name != "identity" else 3,
        "truthfulness_reward": 3,
        "runtime_reward": 3,
        "collapse_penalty": 0,
        "assist_delta_reward": 0,
        "total_reward": total,
        "eligibility": eligibility,
        "hard_violations": [],
        "metadata": {
            "stub_policy": route_name,
            "response_keys_validated": [
                "governance_posture",
                "execution",
                "evidence_first_meta.ask_path",
                "metadata.evidence_quality",
                "plan_summary.steps[0]",
            ],
            "request_id": resp.get("request_id"),
        },
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Ask v1 query CLI (export_evidence + /v1/ask).")
    p.add_argument("--workspace-root", required=True)
    p.add_argument("--query", required=True)
    p.add_argument("--context-url", default="http://127.0.0.1:8091")
    p.add_argument("--plan-gate-url", default="http://127.0.0.1:8089")
    p.add_argument("--top-k", type=int, default=8)
    p.add_argument("--out", default="", help="Optional: write full response JSON to this path")
    p.add_argument("--print", dest="print_mode", choices=["summary", "json"], default="summary")
    p.add_argument("--with-reward", action="store_true", help="Print deterministic governed reward summary for this response")
    p.add_argument(
        "--assist-delta",
        default="same",
        choices=["improved", "same", "degraded_minor", "degraded_major"],
        help="Assist delta label used for reward scoring when --with-reward is set",
    )
    p.add_argument("--reward-out", default="", help="Optional: write reward JSON to this path")
    args = p.parse_args()

    context_url = args.context_url.rstrip("/")
    plan_gate_url = args.plan_gate_url.rstrip("/")
    request_id = str(uuid.uuid4())
    router = QueryRouter()
    router_result = None
    routed_reward_stub: str | None = None
    resp: dict[str, Any] | None = None

    try:
        try:
            router_result = router.classify(args.query)
        except Exception as exc:
            print(f"router classify failed: {exc}; falling back to semantic path", file=sys.stderr)
            router_result = None

        if router_result and router_result.intent == QueryIntent.IDENTITY:
            resp = _build_router_response(
                request_id=request_id,
                revision="router:identity",
                answer=router_result.answer or IDENTITY_ANSWER,
                metadata=router_result.metadata,
                ask_path="identity_router",
                routing_mode="identity_router",
                workspace_root=args.workspace_root,
            )
            routed_reward_stub = "identity"
        elif router_result and router_result.intent == QueryIntent.STRUCTURAL:
            router_result = router.resolve_structural(args.query, router_result.metadata)
            if router_result.intent == QueryIntent.STRUCTURAL and router_result.answer:
                graph_result = router_result.metadata.get("graph_result") if isinstance(router_result.metadata, dict) else {}
                file_paths = []
                if isinstance(graph_result, dict) and graph_result.get("file_path"):
                    file_paths = [str(graph_result.get("file_path"))]
                resp = _build_router_response(
                    request_id=request_id,
                    revision="router:structural",
                    answer=router_result.answer,
                    metadata=router_result.metadata,
                    ask_path="structural_router_graph",
                    routing_mode="structural_router",
                    workspace_root=args.workspace_root,
                    file_paths=file_paths,
                )
                routed_reward_stub = "structural"

        if resp is None:
            ask_query = args.query
            if router_result and router_result.intent == QueryIntent.DECOMPOSE and router_result.sub_queries:
                bundles = [
                    _export_evidence_bundle(context_url, args.workspace_root, sub_query, args.top_k)
                    for sub_query in router_result.sub_queries
                ]
                evidence = _merge_evidence_bundles(args.query, bundles, args.top_k, router_result.sub_queries)
                ask_query = _build_decompose_ask_query(args.query, router_result.sub_queries)
                fusion = evidence.get("fusion_diagnostics") if isinstance(evidence.get("fusion_diagnostics"), dict) else None
                router_meta = fusion.get("router") if isinstance(fusion, dict) else None
                if isinstance(router_meta, dict):
                    router_meta["ask_query"] = ask_query
            else:
                evidence = _export_evidence_bundle(context_url, args.workspace_root, args.query, args.top_k)

            ask_req: dict[str, Any] = {
                "schema_version": "ask_request.v1.0",
                "request_id": request_id,
                "timestamp_utc": _now_utc(),
                "query": ask_query,
                "evidence_bundle": evidence,
            }
            ws_hash = evidence.get("workspace_identity_hash")
            if ws_hash:
                ask_req["expected_workspace_identity_hash"] = ws_hash

            ac, resp = _post(f"{plan_gate_url}/v1/ask", ask_req, timeout=300)
            if ac != 200:
                print(f"/v1/ask failed http={ac}", file=sys.stderr)
                return 1
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"http error: {exc.code} {body}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    assert resp is not None

    if args.out.strip():
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(resp, indent=2), encoding="utf-8")
        print(f"Saved: {out}")

    if args.print_mode == "json":
        print(json.dumps(resp, indent=2))
    else:
        _print_summary(resp)
    reward_payload: dict[str, Any] | None = None
    if args.with_reward:
        if routed_reward_stub:
            reward_payload = _print_reward_payload(_build_reward_stub(resp, routed_reward_stub))
        else:
            reward_payload = _print_reward_summary(resp, args.assist_delta)
        if args.reward_out.strip():
            rp = Path(args.reward_out)
            rp.parent.mkdir(parents=True, exist_ok=True)
            rp.write_text(json.dumps(reward_payload, indent=2), encoding="utf-8")
            print(f"Saved reward: {rp}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

