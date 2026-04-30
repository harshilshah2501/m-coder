#!/usr/bin/env python3
"""
Run all developer-evaluation checks in one shot and write a merged report.

1) Motadata behavior verify — developer utility suite (Ask / Debug / Plan scenarios).
2) Optional: mcoder one-shot prompt batch (same as run_mcoder_prompt_batch.py).

Outputs (default under runtime/eval/reports/):
  - developer_eval_batch_<timestamp>.json
  - developer_eval_batch_<timestamp>.md
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_UTILITY = REPO_ROOT / "docs" / "validation" / "motadata_developer_utility_scenarios.v1.json"
VERIFY_SCRIPT = REPO_ROOT / "runtime" / "scripts" / "motadata_behavior_verify.py"
PROMPT_BATCH = REPO_ROOT / "runtime" / "eval" / "run_mcoder_prompt_batch.py"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run_verify(
    *,
    workspace_root: str,
    context_url: str,
    plan_gate_url: str,
    utility_scenarios: Path,
    out_json: Path,
    timeout_sec: int,
) -> dict:
    cmd = [
        sys.executable,
        str(VERIFY_SCRIPT),
        "--workspace-root",
        workspace_root,
        "--context-url",
        context_url,
        "--plan-gate-url",
        plan_gate_url,
        "--utility-scenarios",
        str(utility_scenarios),
        "--scenarios-only",
        "--print",
        "json",
        "--out",
        str(out_json),
    ]
    env = os.environ.copy()
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    parsed = None
    parse_err = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout.strip())
        except json.JSONDecodeError as e:
            parse_err = str(e)
    merged = None
    if out_json.is_file():
        try:
            merged = json.loads(out_json.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "phase": "motadata_behavior_verify_utility",
        "cmd": cmd,
        "returncode": proc.returncode,
        "stderr_tail": (proc.stderr or "")[-4000:],
        "stdout_parse_error": parse_err,
        "stdout_json": parsed,
        "report_file_json": str(out_json),
        "merged_from_out_file": merged,
    }


def _run_prompt_batch(*, workspace: Path, timeout_sec: int) -> dict:
    mcoder_bin = workspace / ".mcoder" / "venv" / "bin" / "mcoder"
    if not mcoder_bin.exists():
        return {
            "phase": "mcoder_prompt_batch",
            "skipped": True,
            "reason": f"mcoder not found at {mcoder_bin}",
        }
    proc = subprocess.run(
        [sys.executable, str(PROMPT_BATCH), "--workspace", str(workspace), "--timeout-sec", str(timeout_sec)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout_sec * 20,
    )
    report_path = Path(__file__).resolve().parent / "mcoder_prompt_batch_report.json"
    payload = None
    if report_path.is_file():
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            payload = None
    return {
        "phase": "mcoder_prompt_batch",
        "skipped": False,
        "returncode": proc.returncode,
        "stderr_tail": (proc.stderr or "")[-2000:],
        "stdout_tail": (proc.stdout or "")[-4000:],
        "report_file_json": str(report_path),
        "report": payload,
    }


def _suite_summary(merged: dict | None) -> dict:
    if not merged:
        return {}
    du = merged.get("developer_utility_suite") or {}
    rows = du.get("results") or du.get("scenario_results") or []
    if isinstance(rows, dict):
        rows = list(rows.values())
    passed = sum(1 for r in rows if isinstance(r, dict) and r.get("pass"))
    total = len(rows)
    by_cap: dict[str, list[str]] = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        cap = str(r.get("capability") or "?")
        sid = str(r.get("id") or "?")
        ok = r.get("pass")
        by_cap.setdefault(cap, []).append(f"{'PASS' if ok else 'FAIL'} {sid}")
    return {
        "utility_rows_total": total,
        "utility_rows_passed": passed,
        "by_capability": by_cap,
        "overall_pass": merged.get("all_pass"),
    }


def _write_markdown(path: Path, payload: dict) -> None:
    lines = [
        "# Developer evaluation batch report",
        "",
        f"- Generated: `{payload.get('generated_utc')}`",
        f"- Workspace: `{payload.get('workspace_root')}`",
        "",
        "## Summary",
        "",
    ]
    su = payload.get("suite_summary") or {}
    lines.append(f"- Utility scenarios: **{su.get('utility_rows_passed', '?')}/{su.get('utility_rows_total', '?')}** passed")
    if su.get("by_capability"):
        lines.append("")
        lines.append("### By capability")
        for cap, items in sorted(su["by_capability"].items()):
            lines.append(f"- **{cap}**")
            for it in items[:20]:
                lines.append(f"  - {it}")
            if len(items) > 20:
                lines.append(f"  - … ({len(items) - 20} more)")
    pb = payload.get("prompt_batch") or {}
    if pb.get("skipped"):
        lines.extend(["", "## Prompt batch", "", f"- Skipped: {pb.get('reason', '')}"])
    elif pb.get("report"):
        r = pb["report"]
        results = r.get("results") or []
        ok = sum(1 for x in results if isinstance(x, dict) and x.get("ok"))
        lines.extend(
            [
                "",
                "## Prompt batch (mcoder prompt)",
                "",
                f"- Queries: **{ok}/{len(results)}** ok",
                f"- Detail: `{pb.get('report_file_json')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Full JSON: `{payload.get('output_json')}`",
            f"- Verify output: `{payload.get('verify_out_json')}`",
            "",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run developer utility verify + optional prompt batch; write JSON + Markdown reports.",
    )
    parser.add_argument(
        "--workspace-root",
        default=os.environ.get("MOTADATA_GATE_WORKSPACE_ROOT", ""),
        help="Motadata workspace root (required for verify)",
    )
    parser.add_argument("--context-url", default=os.environ.get("MCODER_CONTEXT_URL", "http://127.0.0.1:8091"))
    parser.add_argument("--plan-gate-url", default=os.environ.get("MCODER_PLAN_GATE_URL", "http://127.0.0.1:8089"))
    parser.add_argument("--utility-scenarios", type=Path, default=DEFAULT_UTILITY)
    parser.add_argument(
        "--skip-prompt-batch",
        action="store_true",
        help="Only run motadata_behavior_verify utility suite (no mcoder prompt batch).",
    )
    parser.add_argument("--timeout-sec", type=int, default=600, help="Subprocess timeout for verify")
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=REPO_ROOT / "runtime" / "eval" / "reports",
        help="Directory for merged JSON + Markdown reports",
    )
    args = parser.parse_args()

    ws = str(Path(args.workspace_root).expanduser().resolve()) if args.workspace_root.strip() else ""
    if not ws:
        print("ERROR: --workspace-root or MOTADATA_GATE_WORKSPACE_ROOT is required.", file=sys.stderr)
        return 2

    args.reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = _utc_stamp()
    verify_out = args.reports_dir / f"behavior_verify_utility_{stamp}.json"
    merged_out = args.reports_dir / f"developer_eval_batch_{stamp}.json"
    md_out = args.reports_dir / f"developer_eval_batch_{stamp}.md"

    print(f"[1/2] Running utility suite → {verify_out}")
    verify_result = _run_verify(
        workspace_root=ws,
        context_url=args.context_url,
        plan_gate_url=args.plan_gate_url,
        utility_scenarios=args.utility_scenarios.resolve(),
        out_json=verify_out,
        timeout_sec=args.timeout_sec,
    )

    merged = verify_result.get("merged_from_out_file") or verify_result.get("stdout_json") or {}
    suite_summary = _suite_summary(merged)

    prompt_batch: dict = {"skipped": True, "reason": "--skip-prompt-batch"}
    if not args.skip_prompt_batch:
        print("[2/2] Running mcoder prompt batch…")
        prompt_batch = _run_prompt_batch(workspace=Path(ws), timeout_sec=min(180, args.timeout_sec))

    payload = {
        "schema_version": "developer_eval_batch_report.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "workspace_root": ws,
        "utility_scenarios_file": str(args.utility_scenarios),
        "verify_out_json": str(verify_out),
        "output_json": str(merged_out),
        "verify_subprocess": verify_result,
        "suite_summary": suite_summary,
        "prompt_batch": prompt_batch,
    }
    merged_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown(md_out, payload)

    print("\nDone.")
    print(f"  JSON: {merged_out}")
    print(f"  Markdown: {md_out}")
    print(f"  Verify raw: {verify_out}")

    rc_verify = int(verify_result.get("returncode") or 1)
    rc_prompt = 0 if prompt_batch.get("skipped") else int(prompt_batch.get("returncode") or 0)
    total = suite_summary.get("utility_rows_total") or 0
    passed = suite_summary.get("utility_rows_passed") or 0
    if total and passed < total:
        return 1
    return 0 if rc_verify == 0 and rc_prompt == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
