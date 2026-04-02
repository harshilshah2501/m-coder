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
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from runtime.context_layer_service.evidence_api import export_evidence_bundle_dict
from runtime.layer5.evidence.schema_validate import EvidenceSchemaValidationError, validate_evidence_bundle_dict
from runtime.layer5.index import build_file_index
from runtime.layer5.retrieval.action_target_selection import select_plan_action_target
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
    *,
    rank_nudge: bool = True,
) -> Tuple[List[str], float, str]:
    t0 = time.perf_counter()
    eff_cfg = replace(cfg, enable_deterministic_rank_nudge=rank_nudge)
    result = retrieve_lexical(idx, query, top_k=top_k, config=eff_cfg)
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


def _anchor_cluster_ok(case: Dict[str, Any], ranked: Sequence[str], query: str, pred: str) -> bool:
    """Top-3 anchor hit OR (plan_steps only) deterministic selected target in owner/anchors."""
    anchors = list(case.get("acceptable_anchors") or [])
    owner = (case.get("expected_primary_owner") or "").strip()
    if not anchors:
        return True
    top3 = list(ranked[:3]) if ranked else []
    if any(a in top3 for a in anchors):
        return True
    ao = case.get("expected_action_output") or {}
    if (ao.get("surface") or "none") != "plan_steps" or pred == NO_MATCH:
        return False
    sel = select_plan_action_target(list(ranked), query)
    if not sel:
        return False
    return bool((owner and sel == owner) or (sel in anchors))


def _action_ok(
    case: Dict[str, Any],
    top1: str,
    top3: Sequence[str],
    ranked: Sequence[str],
    query: str,
    pred: str,
) -> bool:
    ao = case.get("expected_action_output") or {}
    surface = (ao.get("surface") or "none").strip()
    if surface == "none":
        return True
    owner = (case.get("expected_primary_owner") or "").strip()
    anchors = list(case.get("acceptable_anchors") or [])
    if (owner and top1 == owner) or (anchors and any(a in top3 for a in anchors)):
        return True
    if surface == "plan_steps" and pred != NO_MATCH:
        sel = select_plan_action_target(list(ranked), query)
        if sel:
            return bool((owner and sel == owner) or (sel in anchors))
    return False


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


def _action_surface_relevant(case: Dict[str, Any]) -> bool:
    ao = case.get("expected_action_output") or {}
    return (ao.get("surface") or "none").strip() not in ("none", "")


def _expected_owner_rank(ranked: List[str], owner: str) -> Optional[int]:
    if not owner:
        return None
    try:
        return ranked.index(owner) + 1
    except ValueError:
        return None


def _case_level_failure_reasons(case: Dict[str, Any], row: Dict[str, Any]) -> List[str]:
    """Human-readable reasons a row failed overall_pass (for failure_log.md)."""
    reasons: List[str] = []
    if row.get("status") != "ok":
        reasons.append(f"status={row.get('status')}")
    if row.get("false_strong") == "true":
        reasons.append("false_strong")
    if row.get("distractor_fail") == "true":
        reasons.append("distractor_top5")
    ec = case.get("expected_evidence_class") or {}
    primary = ec.get("primary") or "WEAK"
    pred = row.get("predicted_evidence_class", "")
    allow = list(ec.get("allow") or [])
    if not _accepted_evidence(str(pred), str(primary), allow):
        reasons.append(f"evidence_mismatch(pred={pred}, expected_primary={primary})")
    owner = (case.get("expected_primary_owner") or "").strip()
    anchors = list(case.get("acceptable_anchors") or [])
    top1 = row.get("top_1_path", "") or ""
    ranked = [p for p in (row.get("ranked_paths") or "").split("|") if p]
    top3 = ranked[:3]
    q = str(case.get("query_text") or "")
    pred = str(row.get("predicted_evidence_class", "") or "")
    owner_ok = (bool(owner) and top1 == owner) or (not owner)
    anchor_ok = _anchor_cluster_ok(case, ranked, q, pred)
    if owner:
        if not owner_ok and not anchor_ok:
            reasons.append("owner@1_and_anchor_miss")
        elif not owner_ok and anchor_ok:
            reasons.append("owner@1_miss_only")
    if (case.get("expected_action_output") or {}).get("surface", "none") != "none" and row.get("action_ok") == "false":
        reasons.append("action_surface_mismatch")
    return reasons


def _compute_metrics(cases: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_id = {r["case_id"]: r for r in rows}
    with_owner = [c for c in cases if (c.get("expected_primary_owner") or "").strip()]
    n_owner = max(len(with_owner), 1)
    o1_raw = 0
    o3_raw = 0
    for c in with_owner:
        cid = c["id"]
        r = by_id[cid]
        owner = (c.get("expected_primary_owner") or "").strip()
        anchors = list(c.get("acceptable_anchors") or [])
        ranked = [x for x in (r.get("ranked_paths") or "").split("|") if x]
        top1 = ranked[0] if ranked else ""
        top3 = ranked[:3]
        if top1 == owner:
            o1_raw += 1
        if anchors and any(a in top3 for a in anchors):
            o3_raw += 1

    eligible_sel = [
        c
        for c in with_owner
        if _action_surface_relevant(c)
        and str(by_id[c["id"]].get("predicted_evidence_class", "") or "") != NO_MATCH
    ]
    n_sel = len(eligible_sel)
    o1_sel = 0
    o3_sel = 0
    for c in eligible_sel:
        cid = c["id"]
        r = by_id[cid]
        owner = (c.get("expected_primary_owner") or "").strip()
        anchors = list(c.get("acceptable_anchors") or [])
        ranked = [x for x in (r.get("ranked_paths") or "").split("|") if x]
        q = str(c.get("query_text") or "")
        sel = select_plan_action_target(ranked, q)
        if not sel:
            continue
        if sel == owner:
            o1_sel += 1
        if sel == owner or (anchors and sel in anchors):
            o3_sel += 1

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
        "owner_at_1_raw": o1_raw / n_owner,
        "owner_at_3_raw": o3_raw / n_owner,
        "owner_at_1_selected": (o1_sel / n_sel) if n_sel else 1.0,
        "owner_at_3_selected": (o3_sel / n_sel) if n_sel else 1.0,
        "distractor_error_rate": dist_fails / n_d,
        "weak_evidence_honesty": weak_honesty,
        "no_match_precision": nm_correct / n_pred_nm,
        "false_strong_rate": fs_count / n_all,
        "action_correctness": (action_hits / n_a) if n_a else 1.0,
        "counts": {
            "n_owner": len(with_owner),
            "n_selection_metric_cases": n_sel,
            "distractor_eval": len(distractor_cases),
            "weak_eval": len(weak_cases),
            "pred_no_match": len(pred_nm),
            "action_eval": n_a,
            "timeouts": sum(1 for r in rows if r["status"] == "TIMEOUT"),
        },
    }


def _write_owner_at1_diagnostic(out_dir: Path, cases: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> None:
    by_id = {r["case_id"]: r for r in rows}
    lines: List[str] = [
        "# Stage 2 — owner@1_raw diagnostic",
        "",
        "Raw metrics use the lexical ranked list only (no selection layer).",
        "",
        "## Per-case rows where `top_1_path` ≠ `expected_primary_owner`",
        "",
        "| case_id | expected_owner | rank-1 (raw) | rank of expected owner | selected_action_target |",
        "|---------|----------------|--------------|-------------------------|------------------------|",
    ]
    raw_fails: List[Tuple[str, str, str, Optional[int], str]] = []
    for c in cases:
        owner = (c.get("expected_primary_owner") or "").strip()
        if not owner:
            continue
        r = by_id[c["id"]]
        ranked = [x for x in (r.get("ranked_paths") or "").split("|") if x]
        top1 = (r.get("top_1_path") or "").strip()
        if top1 == owner:
            continue
        q = str(c.get("query_text") or "")
        pred = str(r.get("predicted_evidence_class") or "")
        rank = _expected_owner_rank(ranked, owner)
        sel = ""
        if pred != NO_MATCH and ranked:
            sel = select_plan_action_target(ranked, q) or ""
        raw_fails.append((c["id"], owner, top1, rank, sel))
        rk = "" if rank is None else str(rank)
        lines.append(f"| `{c['id']}` | `{owner}` | `{top1}` | {rk} | `{sel}` |")

    lines.append("")
    lines.append("## Summary (owner@1_raw failures only)")
    lines.append("")
    n = len(raw_fails)
    if n == 0:
        lines.append("- No raw top-1 misses with an expected owner.")
    else:
        in3 = sum(1 for (_, _, _, rk, _) in raw_fails if rk is not None and rk <= 3)
        in8 = sum(1 for (_, _, _, rk, _) in raw_fails if rk is not None and rk <= 8)
        missing = sum(1 for (_, _, _, rk, _) in raw_fails if rk is None)
        lines.append(f"- Total raw top-1 misses: **{n}**")
        lines.append(f"- Expected owner present in top-3: **{in3}**")
        lines.append(f"- Expected owner present in top-8: **{in8}**")
        lines.append(f"- Expected owner missing from ranked list: **{missing}**")
        lines.append("")
        lines.append(
            "- Interpretation: high counts in top-3/top-8 indicate a **ranking** issue; "
            "high “missing” indicates **recall** (owner not in top-k window)."
        )
    lines.append("")
    (out_dir / "stage2_owner_at1_diagnostic.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage 2 grounded validation runner")
    ap.add_argument("--query_pack", type=Path, required=True)
    ap.add_argument("--workspace_root", type=Path, required=True)
    ap.add_argument("--output_dir", type=Path, required=True)
    ap.add_argument("--top_k", type=int, default=8)
    ap.add_argument("--per_query_timeout_sec", type=int, default=120)
    ap.add_argument("--write_traces", action="store_true")
    ap.add_argument(
        "--no-rank-nudge",
        action="store_true",
        help="Disable deterministic lexical rank nudge (raw retrieval order only).",
    )
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
                    ranked, elapsed_ms, pred = _run_one_retrieval(
                        idx, cfg, q, args.top_k, rank_nudge=not args.no_rank_nudge
                    )
                finally:
                    _clear_alarm()
            else:
                ranked, elapsed_ms, pred = _run_one_retrieval(
                    idx, cfg, q, args.top_k, rank_nudge=not args.no_rank_nudge
                )
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
        anchor_ok = _anchor_cluster_ok(case, ranked, q, pred)

        evidence_ok = _accepted_evidence(pred, primary, allow)
        fs = _false_strong(pred, primary, allow)

        dist_fail = False
        if case.get("expected_distractor_behavior") == "must_not_rank_in_top5":
            if case.get("category") in ("distractor", "compound"):
                dist_fail = _distractor_top5_violation(top5, unacceptable)

        weak_primary = primary in (WEAK, INSUFFICIENT)
        weak_honest = (not weak_primary) or (pred in (WEAK, INSUFFICIENT, NO_MATCH))

        action_ok = _action_ok(case, top1, top3, ranked, q, pred)

        sel_eligible = bool(owner) and pred != NO_MATCH and _action_surface_relevant(case)
        sel_tgt = ""
        if sel_eligible and ranked:
            sel_tgt = select_plan_action_target(ranked, q) or ""
        exp_rank = _expected_owner_rank(ranked, owner)
        owner_1_raw_str = str(bool(owner and top1 == owner)).lower() if owner else ""
        owner_3_raw_str = str(bool(anchors and any(a in top3 for a in anchors))).lower() if owner else ""

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
                "owner_1_raw": owner_1_raw_str,
                "owner_3_raw": owner_3_raw_str,
                "anchor_ok_cluster": str(anchor_ok).lower(),
                "selection_metrics_eligible": str(sel_eligible).lower(),
                "selected_action_target": sel_tgt,
                "expected_owner_rank": str(exp_rank) if exp_rank is not None else "",
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

    # Hard gates: raw lexical only (selection-aware metrics are reported separately)
    gate_owner = metrics["owner_at_1_raw"] >= 0.90
    gate_o3 = metrics["owner_at_3_raw"] >= 0.95
    gate_dist = metrics["distractor_error_rate"] <= 0.10
    gate_fs = metrics["false_strong_rate"] == 0.0
    gate_nm = metrics["no_match_precision"] >= 0.95
    n_action = int(metrics["counts"].get("action_eval", 0))
    gate_action = metrics["action_correctness"] >= 0.90 if n_action > 0 else True
    gates_ok = (
        gate_owner
        and gate_o3
        and gate_dist
        and gate_fs
        and gate_nm
        and gate_action
        and not timeout_storm
    )

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
        f"| **Raw retrieval** | | | |",
        f"| owner@1_raw | {metrics['owner_at_1_raw']:.4f} | ≥ 0.90 | {'yes' if gate_owner else 'no'} |",
        f"| owner@3_raw | {metrics['owner_at_3_raw']:.4f} | ≥ 0.95 | {'yes' if gate_o3 else 'no'} |",
        f"| **Action-aware** (`expected_action_output` surface ≠ none, pred ≠ NO_MATCH) | | | |",
        f"| owner@1_selected | {metrics['owner_at_1_selected']:.4f} | (informational) | |",
        f"| owner@3_selected | {metrics['owner_at_3_selected']:.4f} | (informational) | |",
        f"| action_correctness | {metrics['action_correctness']:.4f} | ≥ 0.90 | {'yes' if gate_action else 'no'} |",
        f"| **Other** | | | |",
        f"| distractor_error_rate | {metrics['distractor_error_rate']:.4f} | ≤ 0.10 | {'yes' if gate_dist else 'no'} |",
        f"| weak_evidence_honesty | {metrics['weak_evidence_honesty']:.4f} | ≥ 0.85 (warn < 0.85) | |",
        f"| no_match_precision | {metrics['no_match_precision']:.4f} | ≥ 0.95 | {'yes' if gate_nm else 'no'} |",
        f"| false_strong_rate | {metrics['false_strong_rate']:.4f} | = 0 | {'yes' if gate_fs else 'no'} |",
        "",
        f"- Selection-metric denominator: `{metrics['counts'].get('n_selection_metric_cases', 0)}` cases (owner + action surface + pred ≠ NO_MATCH).",
        f"- Raw rows use lexical order only; `owner@3_raw` is **strict** anchor-in-top-3 (unlike legacy blended `owner@3`). Compare `owner@3_selected` for action-target alignment.",
        f"- Lexical rank nudge: `{'off' if args.no_rank_nudge else 'on'}` (`--no-rank-nudge` to disable).",
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

    _write_owner_at1_diagnostic(out_dir, cases, rows)

    # failure log
    fl = out_dir / "stage2_failure_log.md"
    fl_body = ["# Stage 2 failure log", ""]
    if failure_lines:
        fl_body.append("## Retrieval / invariant events")
        fl_body.append("")
        fl_body.extend(failure_lines)
        fl_body.append("")
    if not gates_ok:
        fl_body.append("## Aggregate metric gates (failed thresholds)")
        fl_body.append("")
        agg = []
        if not gate_owner:
            agg.append("- **owner@1_raw** — below 0.90")
        if not gate_o3:
            agg.append("- **owner@3_raw** — below 0.95")
        if not gate_dist:
            agg.append("- **distractor_error_rate** — above 0.10")
        if not gate_fs:
            agg.append("- **false_strong_rate** — non-zero")
        if not gate_nm:
            agg.append("- **no_match_precision** — below 0.95")
        if not gate_action:
            agg.append("- **action_correctness** — below 0.90 (when action cases exist)")
        if timeout_storm:
            agg.append("- **timeouts** — more than 20% of cases")
        fl_body.extend(agg if agg else ["- (no aggregate gate flags; check runner logic)"])
        fl_body.append("")
    by_id = {r["case_id"]: r for r in rows}
    per_case_fails: List[str] = []
    for c in cases:
        cid = c["id"]
        r = by_id[cid]
        if r.get("overall_pass") != "false":
            continue
        rs = _case_level_failure_reasons(c, r)
        per_case_fails.append(f"- **`{cid}`** — {', '.join(rs) if rs else 'overall_pass false (see CSV)'}")
    if per_case_fails:
        fl_body.append("## Per-case failures (`overall_pass` false)")
        fl_body.append("")
        fl_body.extend(per_case_fails)
        fl_body.append("")
    if not failure_lines and gates_ok and not per_case_fails:
        fl_body.append("(no per-case or invariant failures; gates passed)")
    elif failure_lines and gates_ok and not per_case_fails:
        fl_body.append("*(Aggregate gates passed; see invariant events above.)*")
    fl_body.append("")
    if timeout_storm:
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

    # traces (reuse lexical index + authority adapter — same semantics, no N× full rebuilds)
    if args.write_traces:
        trace_dir = out_dir / "stage2_trace_samples"
        if trace_dir.is_dir():
            shutil.rmtree(trace_dir)
        trace_dir.mkdir(parents=True, exist_ok=True)
        sel = _trace_case_ids(cases, rows)
        ws = str(workspace_root)
        authority_adapter = None
        try:
            from runtime.layer5.authority.code_index_adapter import create_adapter
            from runtime.layer5.authority.code_index_builder import build_index

            authority_adapter = create_adapter(code_index=build_index(workspace_root))
        except Exception:
            authority_adapter = None
        for cid in sel:
            case = next(c for c in cases if c["id"] == cid)
            q = case["query_text"]
            tdir = trace_dir / f"trace_{cid}"
            tdir.mkdir(parents=True, exist_ok=True)
            try:
                bundle = export_evidence_bundle_dict(
                    ws,
                    q,
                    top_k=args.top_k,
                    file_index=idx,
                    authority_adapter=authority_adapter,
                )
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
