#!/usr/bin/env python3
"""
Stage 2 validation runner — retrieval truth + quality gate (no query-pack shortcuts).

Usage (repo root):
  PYTHONPATH=. python validation/stage2_runner.py \\
    --query_pack validation/stage2_query_pack.json \\
    --workspace_root runtime/layer5/audit/fixture_noisy_aiops_workspace \\
    --output_dir validation/
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from runtime.context_layer_service.evidence_api import export_evidence_bundle_dict
from runtime.layer5.evidence.schema_validate import EvidenceSchemaValidationError, validate_evidence_bundle_dict
from runtime.layer5.index import build_file_index
from runtime.layer5.retrieval import LexicalRetrievalConfig, retrieve_lexical
from runtime.layer5.retrieval.quality_gate import assess_evidence_quality
from runtime.layer5.workspace.identity import WorkspaceIdentity

STRONG, WEAK, INSUFFICIENT, NO_MATCH = "STRONG", "WEAK", "INSUFFICIENT", "NO_MATCH"


class PerQueryTimeout(Exception):
    """Raised when per-query wall clock exceeds the limit."""


def _git_sha(repo: Path) -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unknown"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _workspace_identity(workspace_root: Path) -> WorkspaceIdentity:
    root_s = str(workspace_root.resolve())
    return WorkspaceIdentity(
        canonical_root=root_s,
        identity_hash=WorkspaceIdentity.compute_identity_hash(root_s),
        original_input=root_s,
        path_type="posix",
        is_git_repo=(workspace_root / ".git").is_dir(),
    )


def _accepted_evidence(pred: str, primary: str, allow: Sequence[str]) -> bool:
    if pred == primary:
        return True
    return pred in set(allow)


def _false_strong(pred: str, primary: str, allow: Sequence[str]) -> bool:
    if pred != STRONG:
        return False
    if primary in (WEAK, INSUFFICIENT, NO_MATCH) and STRONG not in set(allow):
        return True
    return False


def _run_one_retrieval(
    idx: Any,
    cfg: LexicalRetrievalConfig,
    query: str,
    top_k: int,
) -> Tuple[List[str], float, str]:
    t0 = time.perf_counter()
    result = retrieve_lexical(idx, query, top_k=top_k, config=cfg)
    ranked = [h.relative_path for h in result.hits]
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    pred = assess_evidence_quality(query, ranked).evidence_quality
    return ranked, elapsed_ms, pred


def _install_alarm_handler(seconds: int) -> None:
    if seconds <= 0:
        return
    if not hasattr(signal, "SIGALRM"):
        return

    def _handler(signum: int, frame: Any) -> None:
        raise PerQueryTimeout(f"exceeded {seconds}s")

    signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, float(seconds))


def _clear_alarm() -> None:
    if not hasattr(signal, "SIGALRM"):
        return
    signal.setitimer(signal.ITIMER_REAL, 0.0)
    signal.signal(signal.SIGALRM, signal.SIG_DFL)


def _distractor_top5_violation(
    ranked_top5: Sequence[str],
    unacceptable: Sequence[str],
) -> bool:
    if not unacceptable:
        return False
    norm = [p.replace("\\", "/").lower() for p in ranked_top5]
    for p in norm:
        for sub in unacceptable:
            s = (sub or "").lower().strip()
            if s and s in p:
                return True
    return False


def _action_ok(case: Dict[str, Any], top1: str, top3: Sequence[str]) -> bool:
    ao = case.get("expected_action_output") or {}
    surface = (ao.get("surface") or "none").strip()
    if surface == "none":
        return True
    owner = (case.get("expected_primary_owner") or "").strip()
    anchors = list(case.get("acceptable_anchors") or [])
    ok = (owner and top1 == owner) or (anchors and any(a in top3 for a in anchors))
    return bool(ok)


def _trace_case_ids(pack_cases: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> List[str]:
    by_id = {r["case_id"]: r for r in rows}
    out: List[str] = []

    strong_codes: List[str] = []
    for c in pack_cases:
        ec = c.get("expected_evidence_class") or {}
        if ec.get("primary") != STRONG:
            continue
        if c.get("category") not in ("ask", "debug", "code"):
            continue
        strong_codes.append(c["id"])
        if len(strong_codes) >= 2:
            break
    out.extend(strong_codes)

    wk = [c["id"] for c in pack_cases if c.get("category") == "weak_ambiguous"][:2]
    out.extend(wk)

    d = [c["id"] for c in pack_cases if c.get("category") == "distractor"][:2]
    out.extend(d)

    fails: List[str] = []
    for c in pack_cases:
        cid = c["id"]
        r = by_id.get(cid)
        if r and r.get("overall_pass") == "false":
            fails.append(cid)
            if len(fails) >= 2:
                break
    out.extend(fails)

    seen: set[str] = set()
    ordered: List[str] = []
    for x in out:
        if x not in seen:
            seen.add(x)
            ordered.append(x)
    return ordered


def _compute_metrics(cases: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_id = {r["case_id"]: r for r in rows}
    with_owner = [c for c in cases if (c.get("expected_primary_owner") or "").strip()]
    n_owner = max(len(with_owner), 1)
    o1_hits = 0
    o3_hits = 0
    for c in with_owner:
        cid = c["id"]
        r = by_id[cid]
        owner = (c.get("expected_primary_owner") or "").strip()
        anchors = list(c.get("acceptable_anchors") or [])
        ranked = (r.get("ranked_paths") or "").split("|")
        top1 = ranked[0] if ranked else ""
        top3 = ranked[:3]
        if top1 == owner:
            o1_hits += 1
        if anchors and any(a in top3 for a in anchors):
            o3_hits += 1

    distractor_cases = [
        c
        for c in cases
        if c.get("category") in ("distractor", "compound")
        and c.get("expected_distractor_behavior") == "must_not_rank_in_top5"
    ]
    n_d = max(len(distractor_cases), 1)
    dist_fails = sum(1 for c in distractor_cases if by_id[c["id"]]["distractor_fail"] == "true")

    weak_cases = [c for c in cases if (c.get("expected_evidence_class") or {}).get("primary") in (WEAK, INSUFFICIENT)]
    if not weak_cases:
        weak_honesty = 1.0
    else:
        n_w = len(weak_cases)
        weak_honesty = sum(1 for c in weak_cases if by_id[c["id"]]["weak_honest"] == "true") / n_w

    pred_nm = [c for c in cases if by_id[c["id"]]["predicted_evidence_class"] == NO_MATCH]
    nm_correct = sum(
        1
        for c in pred_nm
        if (c.get("expected_evidence_class") or {}).get("primary") == NO_MATCH
    )
    n_pred_nm = max(len(pred_nm), 1)

    n_all = max(len(cases), 1)
    fs_count = sum(1 for r in rows if r["false_strong"] == "true")

    action_cases = [c for c in cases if (c.get("expected_action_output") or {}).get("surface", "none") != "none"]
    n_a = len(action_cases)
    action_hits = sum(1 for c in action_cases if by_id[c["id"]]["action_ok"] == "true")

    return {
        "owner_at_1": o1_hits / n_owner,
        "owner_at_3": o3_hits / n_owner,
        "distractor_error_rate": dist_fails / n_d,
        "weak_evidence_honesty": weak_honesty,
        "no_match_precision": nm_correct / n_pred_nm,
        "false_strong_rate": fs_count / n_all,
        "action_correctness": (action_hits / n_a) if n_a else 1.0,
        "counts": {
            "n_owner": len(with_owner),
            "distractor_eval": len(distractor_cases),
            "weak_eval": len(weak_cases),
            "pred_no_match": len(pred_nm),
            "action_eval": n_a,
            "timeouts": sum(1 for r in rows if r["status"] == "TIMEOUT"),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage 2 grounded validation runner")
    ap.add_argument("--query_pack", type=Path, required=True)
    ap.add_argument("--workspace_root", type=Path, required=True)
    ap.add_argument("--output_dir", type=Path, required=True)
    ap.add_argument("--top_k", type=int, default=8)
    ap.add_argument("--per_query_timeout_sec", type=int, default=120)
    ap.add_argument("--write_traces", action="store_true")
    args = ap.parse_args()

    if args.per_query_timeout_sec < 1:
        print("per_query_timeout_sec must be >= 1", file=sys.stderr)
        return 2

    pack_path = args.query_pack.resolve()
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    workspace_root = args.workspace_root.resolve()
    if not workspace_root.is_dir():
        print(f"workspace_root is not a directory: {workspace_root}", file=sys.stderr)
        return 2

    raw = json.loads(pack_path.read_text(encoding="utf-8"))
    cases: List[Dict[str, Any]] = raw["cases"]
    identity = _workspace_identity(workspace_root)
    idx = build_file_index(identity)
    cfg = LexicalRetrievalConfig(include_score_diagnostics=True)

    rows: List[Dict[str, Any]] = []
    failure_lines: List[str] = []

    for case in cases:
        cid = case["id"]
        q = case["query_text"]
        owner = (case.get("expected_primary_owner") or "").strip()
        anchors = list(case.get("acceptable_anchors") or [])
        ec = case.get("expected_evidence_class") or {}
        primary = ec.get("primary") or "WEAK"
        allow = list(ec.get("allow") or [])
        unacceptable = list(case.get("unacceptable_top5_paths") or [])

        ranked: List[str] = []
        elapsed_ms = 0.0
        pred = NO_MATCH
        status = "ok"
        err: Optional[str] = None

        try:
            if hasattr(signal, "SIGALRM") and args.per_query_timeout_sec > 0:
                _install_alarm_handler(args.per_query_timeout_sec)
                try:
                    ranked, elapsed_ms, pred = _run_one_retrieval(idx, cfg, q, args.top_k)
                finally:
                    _clear_alarm()
            else:
                ranked, elapsed_ms, pred = _run_one_retrieval(idx, cfg, q, args.top_k)
        except PerQueryTimeout:
            status = "TIMEOUT"
            pred = NO_MATCH
            err = "per_query_timeout"
            failure_lines.append(f"- `{cid}`: per-query timeout ({args.per_query_timeout_sec}s), layer=retrieval")
        except Exception as e:
            status = "ERROR"
            err = str(e)
            pred = NO_MATCH
            failure_lines.append(f"- `{cid}`: error `{e}`")

        top1 = ranked[0] if ranked else ""
        top3 = ranked[:3]
        top5 = ranked[:5]

        owner_ok = (bool(owner) and top1 == owner) or (not owner)
        anchor_ok = (not anchors) or any(a in top3 for a in anchors)

        evidence_ok = _accepted_evidence(pred, primary, allow)
        fs = _false_strong(pred, primary, allow)

        dist_fail = False
        if case.get("expected_distractor_behavior") == "must_not_rank_in_top5":
            if case.get("category") in ("distractor", "compound"):
                dist_fail = _distractor_top5_violation(top5, unacceptable)

        weak_primary = primary in (WEAK, INSUFFICIENT)
        weak_honest = (not weak_primary) or (pred in (WEAK, INSUFFICIENT, NO_MATCH))

        action_ok = _action_ok(case, top1, top3)

        empty_strong_fail = primary == STRONG and bool(owner) and not ranked

        overall = (
            evidence_ok
            and not fs
            and not dist_fail
            and status == "ok"
            and not empty_strong_fail
            and (not owner or owner_ok or anchor_ok)
        )

        if empty_strong_fail:
            failure_lines.append(f"- `{cid}`: empty retrieval but expected STRONG with owner `{owner}`")
            overall = False

        if fs:
            failure_lines.append(f"- `{cid}`: false STRONG (predicted STRONG vs primary `{primary}`)")

        rows.append(
            {
                "case_id": cid,
                "status": status,
                "predicted_evidence_class": pred,
                "top_1_path": top1,
                "ranked_paths": "|".join(ranked),
                "owner_at_1": str(owner_ok).lower(),
                "owner_at_3": str(anchor_ok).lower(),
                "false_strong": str(fs).lower(),
                "distractor_fail": str(dist_fail).lower(),
                "weak_honest": str(weak_honest).lower(),
                "action_ok": str(action_ok).lower(),
                "latency_ms": f"{elapsed_ms:.2f}",
                "error": err or "",
                "overall_pass": str(overall).lower(),
            }
        )

    timeouts = sum(1 for r in rows if r["status"] == "TIMEOUT")
    timeout_storm = bool(cases) and (timeouts / len(cases) > 0.20)

    metrics = _compute_metrics(cases, rows)

    # Hard gates
    gate_owner = metrics["owner_at_1"] >= 0.90
    gate_dist = metrics["distractor_error_rate"] <= 0.10
    gate_fs = metrics["false_strong_rate"] == 0.0
    gate_nm = metrics["no_match_precision"] >= 0.95
    gates_ok = gate_owner and gate_dist and gate_fs and gate_nm and not timeout_storm

    # CSV
    csv_path = out_dir / "stage2_results_sheet.csv"
    fieldnames = list(rows[0].keys()) if rows else ["case_id"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # metrics report
    report_path = out_dir / "stage2_metrics_report.md"
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Stage 2 metrics report",
        "",
        f"- Generated (UTC): `{now}`",
        f"- Query pack SHA-256: `{_sha256_file(pack_path)}`",
        f"- Workspace root: `{workspace_root}`",
        f"- `workspace_identity_hash`: `{identity.identity_hash}`",
        f"- Git HEAD (m-coder): `{_git_sha(_REPO_ROOT)}`",
        f"- Command: `{' '.join(sys.argv)}`",
        "",
        "## Metrics",
        "",
        f"| Metric | Value | Threshold | Pass |",
        f"|--------|-------|-----------|------|",
        f"| owner@1 | {metrics['owner_at_1']:.4f} | ≥ 0.90 | {'yes' if gate_owner else 'no'} |",
        f"| owner@3 | {metrics['owner_at_3']:.4f} | ≥ 0.95 | {'yes' if metrics['owner_at_3'] >= 0.95 else 'no'} |",
        f"| distractor_error_rate | {metrics['distractor_error_rate']:.4f} | ≤ 0.10 | {'yes' if gate_dist else 'no'} |",
        f"| weak_evidence_honesty | {metrics['weak_evidence_honesty']:.4f} | ≥ 0.85 (warn < 0.85) | |",
        f"| no_match_precision | {metrics['no_match_precision']:.4f} | ≥ 0.95 | {'yes' if gate_nm else 'no'} |",
        f"| false_strong_rate | {metrics['false_strong_rate']:.4f} | = 0 | {'yes' if gate_fs else 'no'} |",
        f"| action_correctness | {metrics['action_correctness']:.4f} | ≥ 0.90 | {'yes' if metrics['action_correctness'] >= 0.90 else 'no'} |",
        "",
        f"- Timeouts: {metrics['counts']['timeouts']} / {len(cases)}",
        f"- Timeout storm abort (>20%): `{timeout_storm}`",
        "",
        "## Human audit (§3.15)",
        "",
        "Complete `stage2_human_audit_checkpoint.md` with 3 deterministic spot-checks before release.",
        "",
        "## Gates",
        "",
        f"- **OVERALL:** {'PASS' if gates_ok else 'FAIL'}",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")

    # failure log
    fl = out_dir / "stage2_failure_log.md"
    fl_body = ["# Stage 2 failure log", ""]
    if failure_lines:
        fl_body.extend(failure_lines)
    else:
        fl_body.append("(no failures recorded)")
    if timeout_storm:
        fl_body.append("")
        fl_body.append("## Abort")
        fl_body.append("")
        fl_body.append("- `abort_reason=timeout_storm` — more than 20% of queries timed out.")
    fl.write_text("\n".join(fl_body) + "\n", encoding="utf-8")

    # manifest
    manifest = {
        "schema_version": "stage2.runner_manifest.v1",
        "utc_timestamp": now,
        "runner_argv": sys.argv,
        "query_pack_sha256": _sha256_file(pack_path),
        "workspace_identity_hash": identity.identity_hash,
        "git_head_m_coder": _git_sha(_REPO_ROOT),
        "partial": False,
        "abort_reason": "timeout_storm" if timeout_storm else None,
        "gates_pass": gates_ok,
    }
    (out_dir / "stage2_runner_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # traces
    if args.write_traces:
        trace_dir = out_dir / "stage2_trace_samples"
        if trace_dir.is_dir():
            shutil.rmtree(trace_dir)
        trace_dir.mkdir(parents=True, exist_ok=True)
        sel = _trace_case_ids(cases, rows)
        ws = str(workspace_root)
        for cid in sel:
            case = next(c for c in cases if c["id"] == cid)
            q = case["query_text"]
            tdir = trace_dir / f"trace_{cid}"
            tdir.mkdir(parents=True, exist_ok=True)
            try:
                bundle = export_evidence_bundle_dict(ws, q, top_k=args.top_k)
                validate_evidence_bundle_dict(bundle)
                (tdir / "evidence_bundle.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
                (tdir / "case_meta.json").write_text(json.dumps({"case_id": cid, "query": q}, indent=2), encoding="utf-8")
            except (EvidenceSchemaValidationError, OSError, ValueError, RuntimeError) as e:
                (tdir / "export_error.txt").write_text(str(e), encoding="utf-8")

    exit_code = 0 if gates_ok and not timeout_storm else 1
    if timeout_storm:
        exit_code = 2
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
