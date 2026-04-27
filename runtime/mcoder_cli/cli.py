from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any


def _now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _project_root_from_cwd() -> Path | None:
    cur = Path.cwd().resolve()
    for p in [cur, *cur.parents]:
        if (p / ".git").exists():
            return p
    return None


def _state_dir() -> Path:
    root = _project_root_from_cwd()
    if root is not None:
        d = root / ".mcoder"
    else:
        d = Path.home() / ".mcoder"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _discover_config(config_path: str | None) -> Path:
    if config_path:
        return Path(config_path).expanduser()
    sd = _state_dir()
    local_cfg = sd / "config.yaml"
    if local_cfg.is_file():
        return local_cfg
    return Path.home() / ".mcoder" / "config.yaml"


def _read_simple_yaml(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in raw:
            continue
        k, v = raw.split(":", 1)
        out[k.strip()] = v.strip().strip("'").strip('"')
    return out


def _http_code(url: str, timeout_sec: int) -> str:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as r:
            return str(r.status)
    except urllib.error.HTTPError as e:
        return str(e.code)
    except Exception:
        return "000"


def _post_json(url: str, payload: dict[str, Any], timeout_sec: int) -> tuple[int, dict[str, Any]]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_sec) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


class Cfg:
    def __init__(self, args: argparse.Namespace):
        self.verbose = bool(args.verbose)
        self.timeout_sec = int(args.timeout_sec)
        self.state_dir = _state_dir()
        self.config_path = _discover_config(args.config)
        env = _read_simple_yaml(self.config_path)
        self.workspace_root = args.workspace_root or os.environ.get("MCODER_WORKSPACE_ROOT") or env.get("workspace_root") or str(_project_root_from_cwd() or Path.home() / "Projects" / "Motadata")
        self.context_url = args.context_url or os.environ.get("MCODER_CONTEXT_URL") or env.get("context_url") or "http://127.0.0.1:8091"
        self.plan_gate_url = args.plan_gate_url or os.environ.get("MCODER_PLAN_GATE_URL") or env.get("plan_gate_url") or "http://127.0.0.1:8089"
        self.mode = env.get("mode", "")
        if self.verbose:
            print(
                f"[DEBUG] config_file={self.config_path} state_dir={self.state_dir} "
                f"workspace_root={self.workspace_root} context_url={self.context_url} "
                f"plan_gate_url={self.plan_gate_url} timeout_sec={self.timeout_sec}",
                file=sys.stderr,
            )


def _cmd_init(args: argparse.Namespace) -> int:
    cfg = Cfg(args)
    d = cfg.state_dir
    cfg_file = d / "config.yaml"
    env_file = d / "context.env"
    if not args.force:
        if cfg_file.exists():
            print(f"config exists: {cfg_file} (use --force to overwrite)", file=sys.stderr)
            return 2
        if env_file.exists():
            print(f"context env exists: {env_file} (use --force to overwrite)", file=sys.stderr)
            return 2

    parsed = urllib.parse.urlparse(cfg.context_url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    cfg_file.write_text(
        "\n".join(
            [
                f"workspace_root: {cfg.workspace_root}",
                f"context_url: {cfg.context_url}",
                f"plan_gate_url: {cfg.plan_gate_url}",
                "mode: api_only",
                "output: human",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    env_file.write_text(
        "\n".join(
            [
                "MOTADATA_CONTEXT_LAYER_HOST=127.0.0.1",
                f"MOTADATA_CONTEXT_LAYER_PORT={port}",
                f"MOTADATA_ROOT={cfg.workspace_root}",
                f"MOTADATA_CONTEXT_LAYER_DEFAULT_WORKSPACE={cfg.workspace_root}",
                f"MOTADATA_CONTEXT_LAYER_LOG_PATH={d / 'context-layer.log'}",
                "MOTADATA_CONTEXT_LAYER_INDEX_CACHE=1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print("Initialized mcoder project config:")
    print(f"  {cfg_file}")
    print(f"  {env_file}")
    return 0


def _health_core(cfg: Cfg, auto_fix: bool) -> int:
    logs = cfg.state_dir / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    journal = logs / f"mcoder-health-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    with journal.open("w", encoding="utf-8") as f:
        f.write(f"timestamp_utc={_now_utc()}\n")
        f.write(f"config_file={cfg.config_path}\n")
        f.write(f"workspace_root={cfg.workspace_root}\n")
        f.write(f"context_url={cfg.context_url}\n")
        f.write(f"plan_gate_url={cfg.plan_gate_url}\n")
        f.write(f"auto_fix={1 if auto_fix else 0}\n")
        f.write(f"timeout_sec={cfg.timeout_sec}\n")

    print(f"[STEP] Checking Context Layer health: {cfg.context_url}/healthz (timeout {cfg.timeout_sec}s)")
    ctx_code = _http_code(f"{cfg.context_url}/healthz", cfg.timeout_sec)
    print(f"[STEP] Checking Plan-Gate health: {cfg.plan_gate_url}/healthz (timeout {cfg.timeout_sec}s)")
    pg_code = _http_code(f"{cfg.plan_gate_url}/healthz", cfg.timeout_sec)
    with journal.open("a", encoding="utf-8") as f:
        f.write(f"context_health_code={ctx_code}\n")
        f.write(f"plan_gate_health_code={pg_code}\n")

    ctx_ok = ctx_code == "200"
    pg_ok = pg_code == "200"

    if not ctx_ok and auto_fix:
        print("[STEP] Context unhealthy; attempting service restart")
        with journal.open("a", encoding="utf-8") as f:
            f.write("diagnosis: context health check failed\n")
            f.write("action: attempting systemctl --user restart mcoder-context\n")
        try:
            subprocess.run(["systemctl", "--user", "restart", "mcoder-context"], check=False, capture_output=True, text=True)
        except Exception:
            pass
        ctx_code2 = _http_code(f"{cfg.context_url}/healthz", cfg.timeout_sec)
        with journal.open("a", encoding="utf-8") as f:
            f.write(f"context_health_code_after_fix={ctx_code2}\n")
            f.write("result: context recovered after restart\n" if ctx_code2 == "200" else "result: context still failing after restart\n")
        ctx_ok = ctx_code2 == "200"

    if not pg_ok and auto_fix:
        print("[STEP] Plan-Gate unhealthy; running stack diagnostics")
        with journal.open("a", encoding="utf-8") as f:
            f.write("diagnosis: plan-gate health check failed\n")
            f.write("action: stack diagnostics requested\n")
        pg_code2 = _http_code(f"{cfg.plan_gate_url}/healthz", cfg.timeout_sec)
        with journal.open("a", encoding="utf-8") as f:
            f.write(f"plan_gate_health_code_after_diagnosis={pg_code2}\n")
        pg_ok = pg_code2 == "200"

    if ctx_ok and pg_ok:
        print("Context Layer + Plan-Gate health: OK")
        print(f"health journal: {journal}")
        return 0
    print("Context Layer + Plan-Gate health: FAILED")
    print(f"health journal: {journal}")
    return 1


def _cmd_health(args: argparse.Namespace) -> int:
    cfg = Cfg(args)
    return _health_core(cfg, auto_fix=bool(args.auto_fix))


def _cmd_doctor(args: argparse.Namespace) -> int:
    cfg = Cfg(args)
    fails = 0
    cfg_ok = cfg.config_path.is_file()
    ws_ok = Path(cfg.workspace_root).is_dir()
    ctx_ok = _http_code(f"{cfg.context_url}/healthz", cfg.timeout_sec) == "200"
    pg_ok = _http_code(f"{cfg.plan_gate_url}/healthz", cfg.timeout_sec) == "200"
    mode_ok = cfg.mode == "api_only"
    try:
        import neo4j  # type: ignore # noqa: F401
        neo4j_ok = True
    except Exception:
        neo4j_ok = False

    if cfg_ok:
        print(f"Config: OK ({cfg.config_path})")
    else:
        print(f"Config: FAIL ({cfg.config_path})")
        fails += 1
    if ws_ok:
        print(f"Workspace root: OK ({cfg.workspace_root})")
    else:
        print(f"Workspace root: FAIL ({cfg.workspace_root})")
        fails += 1
    if ctx_ok:
        print(f"Context Layer: OK ({cfg.context_url})")
    else:
        print(f"Context Layer: FAIL ({cfg.context_url})")
        fails += 1
    if pg_ok:
        print(f"Plan-Gate: OK ({cfg.plan_gate_url})")
    else:
        print(f"Plan-Gate: FAIL ({cfg.plan_gate_url})")
        fails += 1
    if mode_ok:
        print("API-only mode: OK")
    else:
        print(f"API-only mode: FAIL (mode={cfg.mode or '<unset>'})")
        fails += 1
    if neo4j_ok:
        print("Neo4j driver: OK (structural queries enabled)")
    else:
        print("Neo4j driver: WARN (structural graph queries may return GRAPH_UNAVAILABLE)")
    return 0 if fails == 0 else 1


def _run_ask_like(cfg: Cfg, query: str, *, task_type: str, selected_file: str = "", response_extensions: list[str] | None = None, print_json: bool = False) -> int:
    rid = str(uuid.uuid4())
    status, evidence = _post_json(
        f"{cfg.context_url.rstrip('/')}/v1/export_evidence",
        {
            "workspace_root": cfg.workspace_root,
            "query": query,
            "top_k": 8,
            "task_type": task_type,
            "selected_file": selected_file,
            "active_file": selected_file,
        },
        cfg.timeout_sec,
    )
    if status != 200:
        print(f"export_evidence failed http={status}", file=sys.stderr)
        return 1
    ask_req: dict[str, Any] = {
        "schema_version": "ask_request.v1.0",
        "request_id": rid,
        "timestamp_utc": _now_utc(),
        "query": query,
        "task_type": task_type,
        "selected_file": selected_file,
        "evidence_bundle": evidence,
    }
    if response_extensions:
        ask_req["response_extensions"] = response_extensions
    ac, resp = _post_json(f"{cfg.plan_gate_url.rstrip('/')}/v1/ask", ask_req, cfg.timeout_sec)
    if ac != 200:
        print(f"/v1/ask failed http={ac}", file=sys.stderr)
        return 1
    if print_json:
        print(json.dumps(resp, indent=2))
    else:
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
    return 0


def _cmd_prompt(args: argparse.Namespace) -> int:
    cfg = Cfg(args)
    return _run_ask_like(cfg, args.query, task_type="general", print_json=args.json)


def _cmd_plan(args: argparse.Namespace) -> int:
    cfg = Cfg(args)
    return _run_ask_like(cfg, args.query, task_type="general", response_extensions=["plan_contract.v1"], print_json=args.json)


def _cmd_debug(args: argparse.Namespace) -> int:
    cfg = Cfg(args)
    q = args.query or "Explain/debug this file"
    if args.symbol:
        q = f"{q} (symbol: {args.symbol})"
    return _run_ask_like(cfg, q, task_type="EXPLAIN_DEBUG", selected_file=args.file, print_json=args.json)


def _cmd_scenario(args: argparse.Namespace) -> int:
    cfg = Cfg(args)
    path = Path(args.file)
    if not path.is_file():
        print(f"scenario file not found: {path}", file=sys.stderr)
        return 2
    out_dir = Path(args.out_dir) if args.out_dir else cfg.state_dir / "scenario-runs" / dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    failed = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        total += 1
        print(f"\n=== Scenario {total} ({args.type}) ===")
        print(f"query: {line}")
        rc = 0
        if args.type == "ask":
            rc = _run_ask_like(cfg, line, task_type="general")
        elif args.type == "plan":
            rc = _run_ask_like(cfg, line, task_type="general", response_extensions=["plan_contract.v1"])
        else:
            if "|" not in line:
                print("[FAIL] debug scenario must be selected_file|query", file=sys.stderr)
                rc = 2
            else:
                sf, q = line.split("|", 1)
                rc = _run_ask_like(cfg, q.strip(), task_type="EXPLAIN_DEBUG", selected_file=sf.strip())
        if rc != 0:
            failed += 1
            print(f"[FAIL] scenario {total}")
        else:
            print(f"[OK] saved: {out_dir / (str(total).zfill(3) + '.json')}")
    print(f"\nScenario run complete: total={total} failed={failed} out_dir={out_dir}")
    if total == 0:
        print(f"No runnable scenarios in {path}", file=sys.stderr)
        return 2
    return 0 if failed == 0 else 1


def _cmd_version(_args: argparse.Namespace) -> int:
    print("mcoder unified package CLI")
    try:
        import importlib.metadata as md
        print(f"mcoder-suite version: {md.version('mcoder-suite')}")
    except Exception:
        pass
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mcoder")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--config", default="")
    p.add_argument("--timeout-sec", type=int, default=int(os.environ.get("MCODER_TIMEOUT_SEC", "15")))
    p.add_argument("--workspace-root", default="")
    p.add_argument("--context-url", default="")
    p.add_argument("--plan-gate-url", default="")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=_cmd_init)

    s = sub.add_parser("health")
    s.add_argument("--auto-fix", action="store_true")
    s.set_defaults(func=_cmd_health)

    s = sub.add_parser("doctor")
    s.set_defaults(func=_cmd_doctor)

    s = sub.add_parser("prompt")
    s.add_argument("query")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=_cmd_prompt)

    s = sub.add_parser("plan")
    s.add_argument("query")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=_cmd_plan)

    s = sub.add_parser("debug")
    s.add_argument("--file", required=True)
    s.add_argument("--query", default="")
    s.add_argument("--symbol", default="")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=_cmd_debug)

    s = sub.add_parser("scenario")
    s.add_argument("--type", choices=["ask", "plan", "debug"], required=True)
    s.add_argument("--file", required=True)
    s.add_argument("--out-dir", default="")
    s.set_defaults(func=_cmd_scenario)

    s = sub.add_parser("version")
    s.set_defaults(func=_cmd_version)
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

