from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .evaluator import DEFAULT_ARTIFACT_DIR, evaluate_assist_v2
from .policy import generate_confidence_policy


DATASET_PATH = Path("runtime/assist_layer/evaluation/assist_eval_dataset.v1.json")
SUMMARY_FILENAME = "assist_eval_summary.json"
POLICY_FILENAME = "assist_confidence_policy.v1.json"


def _load_dataset(path: Path | None = None) -> Dict[str, Any]:
    p = path or DATASET_PATH
    data = json.loads(p.read_text(encoding="utf-8"))
    if str(data.get("schema_version") or "") != "assist_eval_dataset.v1":
        raise ValueError("invalid assist evaluation dataset schema_version")
    return data


def _build_ask_request(entry: Dict[str, Any], repo_root: str, revision: str) -> Dict[str, Any]:
    rid = str(entry.get("id") or "eval-item")
    return {
        "schema_version": "ask_request.v0.1",
        "request_id": f"assist-v2-batch-{rid}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": repo_root,
        "revision": revision,
        "query": str(entry.get("query") or ""),
        "task_type": "general",
        "selected_file": str(entry.get("selected_file") or "runtime/ask_service/handlers.py"),
        "client_context": {
            "diagnostics_labels": ["assist_v2_eval"]
        },
        "trace_id": f"assist-v2-batch-trace-{rid}",
        "query_category": str(entry.get("category") or "uncategorized"),
        "query_note": str(entry.get("note") or ""),
    }


def _add_bucket_count(container: Dict[str, Dict[str, int]], bucket: str, verdict: str) -> None:
    if bucket not in container:
        container[bucket] = {
            "total": 0,
            "improved": 0,
            "same": 0,
            "degraded_minor": 0,
            "degraded_major": 0,
        }
    container[bucket]["total"] += 1
    container[bucket][verdict] = container[bucket].get(verdict, 0) + 1


def _extract_patterns(runs: List[Dict[str, Any]], summary: Dict[str, Any]) -> List[str]:
    patterns: List[str] = []

    by_transform = summary.get("counts_by_transform_code") or {}
    for transform, stats in sorted(by_transform.items()):
        total = int(stats.get("total", 0))
        if total == 0:
            continue
        same_ratio = (int(stats.get("same", 0)) + int(stats.get("improved", 0))) / total
        major_ratio = int(stats.get("degraded_major", 0)) / total
        if same_ratio >= 0.8:
            patterns.append(f"transform {transform} is mostly stable ({same_ratio:.0%} same/improved)")
        if major_ratio >= 0.2:
            patterns.append(f"transform {transform} shows elevated major degradation ({major_ratio:.0%})")

    by_category = summary.get("counts_by_query_category") or {}
    for category, stats in sorted(by_category.items()):
        total = int(stats.get("total", 0))
        if total == 0:
            continue
        degraded_ratio = (int(stats.get("degraded_minor", 0)) + int(stats.get("degraded_major", 0))) / total
        if degraded_ratio >= 0.5:
            patterns.append(f"category {category} frequently degrades ({degraded_ratio:.0%})")
        if int(stats.get("improved", 0)) >= 1 and degraded_ratio <= 0.25:
            patterns.append(f"category {category} shows promising stability/improvement")

    # top failure clusters by tuple(category, primary transform)
    cluster_counts: Counter = Counter()
    for run in runs:
        verdict = str(run.get("final_verdict") or "")
        if verdict not in {"degraded_minor", "degraded_major"}:
            continue
        category = str(run.get("query_category") or "uncategorized")
        t_codes = (run.get("assist_metadata") or {}).get("transform_codes_applied") or []
        primary = str(t_codes[0]) if t_codes else "no_transform"
        cluster_counts[(category, primary)] += 1

    for (category, primary), count in cluster_counts.most_common(3):
        patterns.append(f"failure cluster: category={category}, transform={primary}, count={count}")

    if not patterns:
        patterns.append("no strong patterns detected in current batch")

    return patterns


def run_assist_eval_batch(
    *,
    repo_root: str,
    revision: str,
    dataset_path: Path | None = None,
    output_root: Path | None = None,
    run_prefix: str = "assist_eval",
) -> Dict[str, Any]:
    dataset = _load_dataset(dataset_path)
    entries = dataset.get("entries") or []
    root = output_root or DEFAULT_ARTIFACT_DIR
    root.mkdir(parents=True, exist_ok=True)

    runs: List[Dict[str, Any]] = []
    by_transform: Dict[str, Dict[str, int]] = {}
    by_category: Dict[str, Dict[str, int]] = {}

    verdict_counts: Counter = Counter()
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        run_id = f"{run_prefix}_{idx+1:03d}_{entry.get('id', 'item')}"
        ask_request = _build_ask_request(entry, repo_root=repo_root, revision=revision)
        result = evaluate_assist_v2(
            ask_request,
            output_root=root,
            run_id=run_id,
            persist_artifact=True,
        )
        runs.append(result)

        verdict = str(result.get("final_verdict") or "same")
        if verdict not in {"improved", "same", "degraded_minor", "degraded_major"}:
            verdict = "same"
        verdict_counts[verdict] += 1

        category = str(result.get("query_category") or "uncategorized")
        _add_bucket_count(by_category, category, verdict)

        transforms = (result.get("assist_metadata") or {}).get("transform_codes_applied") or []
        if not transforms:
            transforms = ["no_transform"]
        for code in transforms:
            _add_bucket_count(by_transform, str(code), verdict)

    summary = {
        "schema_version": "assist_eval_summary.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_schema_version": dataset.get("schema_version"),
        "dataset_entries": len(entries),
        "total_runs": len(runs),
        "improved_count": verdict_counts.get("improved", 0),
        "same_count": verdict_counts.get("same", 0),
        "degraded_minor_count": verdict_counts.get("degraded_minor", 0),
        "degraded_major_count": verdict_counts.get("degraded_major", 0),
        "counts_by_transform_code": by_transform,
        "counts_by_query_category": by_category,
        "notable_patterns": [],
        "run_ids": [str(r.get("run_id") or "") for r in runs],
    }
    summary["notable_patterns"] = _extract_patterns(runs, summary)

    summary_path = root / SUMMARY_FILENAME
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    policy = generate_confidence_policy(summary, runs)
    policy_path = root / POLICY_FILENAME
    policy_path.write_text(json.dumps(policy, indent=2), encoding="utf-8")

    return {
        "summary": summary,
        "summary_path": str(summary_path),
        "policy": policy,
        "policy_path": str(policy_path),
        "runs": runs,
    }
