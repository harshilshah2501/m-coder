#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


QUERIES = [
	"Explain the API layer architecture.",
	"How does mail server configuration work?",
	"Find all classes that handle notifications.",
	"How are config stores organized?",
]


def _now_utc() -> str:
	return datetime.now(timezone.utc).isoformat()


def _extract_answer(payload: dict) -> str:
	if isinstance(payload.get("answer"), str):
		return payload["answer"]
	steps = ((payload.get("plan_summary") or {}).get("steps") or [])
	if isinstance(steps, list) and steps:
		return " ".join(str(s) for s in steps)
	return ""


def _bool(v: bool) -> str:
	return "yes" if v else "no"


def run_query(mcoder_bin: Path, cwd: Path, query: str, timeout_sec: int) -> dict:
	env = os.environ.copy()
	env.pop("PYTHONPATH", None)
	cmd = [str(mcoder_bin), "prompt", "--json", query]
	start = time.time()
	proc = subprocess.run(
		cmd,
		cwd=str(cwd),
		env=env,
		capture_output=True,
		text=True,
		timeout=timeout_sec,
	)
	latency_ms = round((time.time() - start) * 1000.0, 1)

	out = (proc.stdout or "").strip()
	err = (proc.stderr or "").strip()
	data = None
	parse_error = None
	if out:
		try:
			data = json.loads(out)
		except Exception as exc:
			parse_error = str(exc)

	answer_text = _extract_answer(data or {})
	lower = answer_text.lower()
	has_reasoning_context = bool(((data or {}).get("metadata") or {}).get("reasoning_context"))
	has_owner_anchor = "primary implementation owner" in lower or "primary owner" in lower
	has_confidence_limit = "confidence" in lower or "partial graph coverage" in lower

	return {
		"query": query,
		"ok": proc.returncode == 0 and data is not None,
		"returncode": proc.returncode,
		"latency_ms": latency_ms,
		"parse_error": parse_error,
		"stderr": err,
		"response": data,
		"signals": {
			"reasoning_context_present": has_reasoning_context,
			"owner_anchor_signal": has_owner_anchor,
			"confidence_limit_signal": has_confidence_limit,
		},
	}


def main() -> int:
	parser = argparse.ArgumentParser(description="Run one-shot batch mcoder prompt diagnostics.")
	parser.add_argument(
		"--workspace",
		default="/root/Harshil-PoCs/Motadata",
		help="Workspace where .mcoder/venv/bin/mcoder is installed",
	)
	parser.add_argument(
		"--timeout-sec",
		type=int,
		default=180,
		help="Per-query timeout in seconds",
	)
	args = parser.parse_args()

	workspace = Path(args.workspace).resolve()
	mcoder_bin = workspace / ".mcoder" / "venv" / "bin" / "mcoder"
	if not mcoder_bin.exists():
		print(f"ERROR: mcoder binary not found at {mcoder_bin}")
		return 2

	results = []
	for i, q in enumerate(QUERIES, start=1):
		print(f"[run] ({i}/{len(QUERIES)}) {q}")
		results.append(run_query(mcoder_bin, workspace, q, args.timeout_sec))

	out = {
		"generated_utc": _now_utc(),
		"workspace": str(workspace),
		"pythopath_unset": True,
		"queries": len(QUERIES),
		"results": results,
	}

	out_dir = Path(__file__).resolve().parent
	out_json = out_dir / "mcoder_prompt_batch_report.json"
	out_json.write_text(json.dumps(out, indent=2), encoding="utf-8")

	print("\nSummary")
	print("query | ok | latency_ms | rc_present | owner_anchor | confidence_limit")
	for r in results:
		s = r["signals"]
		print(
			f"- {r['query']} | {_bool(r['ok'])} | {r['latency_ms']} | "
			f"{_bool(s['reasoning_context_present'])} | {_bool(s['owner_anchor_signal'])} | "
			f"{_bool(s['confidence_limit_signal'])}"
		)

	ok_count = sum(1 for r in results if r["ok"])
	rc_count = sum(1 for r in results if r["signals"]["reasoning_context_present"])
	print(
		f"\n[analysis] ok={ok_count}/{len(results)}, reasoning_context={rc_count}/{len(results)} "
		f"(JSON report: {out_json})"
	)
	return 0 if ok_count == len(results) else 1


if __name__ == "__main__":
	raise SystemExit(main())
