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
from runtime.mcoder_cli.answer_shaping import shape_prompt_summary
from runtime.mcoder_cli import stack_daemon


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


def _post_json_or_fail(
    phase: str,
    url: str,
    payload: dict[str, Any],
    timeout_sec: int,
) -> tuple[int, dict[str, Any]] | tuple[None, None]:
    """POST JSON; on timeout/network failure print phase-specific help and return (None, None)."""
    try:
        return _post_json(url, payload, timeout_sec)
    except TimeoutError:
        print(
            f"{phase}: timed out after {timeout_sec}s ({url}). "
            "Large workspaces or cold Context Layer indexing often need >15s.",
            file=sys.stderr,
        )
        print(
            "Try: mcoder --timeout-sec 120 prompt \"...\"   (or 300 for very large trees)",
            file=sys.stderr,
        )
        return None, None
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        if isinstance(reason, TimeoutError):
            print(
                f"{phase}: timed out after {timeout_sec}s ({url}).",
                file=sys.stderr,
            )
            print("Try: mcoder --timeout-sec 120 prompt \"...\"", file=sys.stderr)
            return None, None
        print(f"{phase}: request failed ({url}): {e}", file=sys.stderr)
        return None, None
    except OSError as e:
        print(f"{phase}: network error ({url}): {e}", file=sys.stderr)
        return None, None


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
        ssh_cli = getattr(args, "plan_gate_ssh", None)
        if ssh_cli is None:
            ssh_cli = ""
        self.plan_gate_ssh_target = (
            str(ssh_cli).strip()
            or os.environ.get("MCODER_PLAN_GATE_SSH", "").strip()
            or env.get("plan_gate_ssh_target", "").strip()
        )
        rp_cli = getattr(args, "ssh_remote_port", None)
        if rp_cli is not None:
            self.plan_gate_ssh_remote_port = int(rp_cli)
        else:
            self.plan_gate_ssh_remote_port = int(
                os.environ.get("MCODER_PLAN_GATE_SSH_REMOTE_PORT", env.get("plan_gate_ssh_remote_port", "8089"))
            )
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
    yaml_lines = [
        f"workspace_root: {cfg.workspace_root}",
        f"context_url: {cfg.context_url}",
        f"plan_gate_url: {cfg.plan_gate_url}",
    ]
    if cfg.plan_gate_ssh_target:
        yaml_lines.append(f"plan_gate_ssh_target: {cfg.plan_gate_ssh_target}")
        yaml_lines.append(f"plan_gate_ssh_remote_port: {cfg.plan_gate_ssh_remote_port}")
    yaml_lines += ["mode: api_only", "output: human"]
    cfg_file.write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")
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
    print()
    print("Next:")
    print("  • Start Context Layer (e.g. systemctl --user start mcoder-context; see setup guide).")
    if "127.0.0.1" in cfg.plan_gate_url or "localhost" in cfg.plan_gate_url:
        if not cfg.plan_gate_ssh_target:
            print("  • plan_gate_url is loopback — add plan_gate_ssh_target (or: mcoder init --force ... --plan-gate-ssh USER@GPU)")
            print("    so mcoder bootstrap can create the SSH tunnel to Plan-Gate automatically.")
        else:
            print("  • plan_gate_ssh_target is set — mcoder bootstrap will try ssh -L when Plan-Gate is down.")
    print("  • Run: mcoder bootstrap")
    print("Docs: docs/guides/MCODER_API_ONLY_DEVELOPER_SETUP.md")
    return 0


def _print_health_failure_hint(cfg: Cfg, ctx_ok: bool, pg_ok: bool) -> None:
    print()
    print("Health checks failed. Typical fixes:")
    if not ctx_ok:
        print(f"  • Context Layer ({cfg.context_url}): start the service or run motadata-context-layer")
        print("    with .mcoder/context.env — see systemd unit mcoder-context in the setup guide.")
    if not pg_ok:
        print(f"  • Plan-Gate ({cfg.plan_gate_url}): ensure the server is up or SSH-tunnel :8089")
        print("    if using http://127.0.0.1:8089 (pip/init do not open tunnels).")
    print("  • Full steps: docs/guides/MCODER_API_ONLY_DEVELOPER_SETUP.md")


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

        # Auto-remediate common WSL tunnel mismatch:
        # config points to remote host, but local tunneled Plan-Gate is healthy.
        parsed = urllib.parse.urlparse(cfg.plan_gate_url)
        current_host = parsed.hostname or ""
        local_fallback = "http://127.0.0.1:8089"
        local_code = _http_code(f"{local_fallback}/healthz", cfg.timeout_sec)
        with journal.open("a", encoding="utf-8") as f:
            f.write(f"plan_gate_local_fallback_code={local_code}\n")
        if not pg_ok and current_host not in ("127.0.0.1", "localhost") and local_code == "200":
            print("[STEP] Plan-Gate fallback detected at 127.0.0.1:8089; updating config")
            with journal.open("a", encoding="utf-8") as f:
                f.write("action: apply local Plan-Gate fallback url http://127.0.0.1:8089\n")
            cfg_map = _read_simple_yaml(cfg.config_path)
            cfg_map["plan_gate_url"] = local_fallback
            lines = []
            for k in ("workspace_root", "context_url", "plan_gate_url", "mode", "output"):
                v = cfg_map.get(k, "")
                if v:
                    lines.append(f"{k}: {v}")
            cfg.config_path.parent.mkdir(parents=True, exist_ok=True)
            cfg.config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            cfg.plan_gate_url = local_fallback
            pg_ok = True
            with journal.open("a", encoding="utf-8") as f:
                f.write("result: config updated with local Plan-Gate fallback\n")

    if ctx_ok and pg_ok:
        print("Context Layer + Plan-Gate health: OK")
        print(f"health journal: {journal}")
        return 0
    print("Context Layer + Plan-Gate health: FAILED")
    print(f"health journal: {journal}")
    _print_health_failure_hint(cfg, ctx_ok, pg_ok)
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
    export_url = f"{cfg.context_url.rstrip('/')}/v1/export_evidence"
    ask_url = f"{cfg.plan_gate_url.rstrip('/')}/v1/ask"
    status, evidence = _post_json_or_fail(
        "Context Layer export_evidence",
        export_url,
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
    if status is None or evidence is None:
        return 1
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
    ac, resp = _post_json_or_fail("Plan-Gate /v1/ask", ask_url, ask_req, cfg.timeout_sec)
    if ac is None or resp is None:
        return 1
    if ac != 200:
        print(f"/v1/ask failed http={ac}", file=sys.stderr)
        return 1
    if print_json:
        print(json.dumps(resp, indent=2))
    else:
        md = resp.get("metadata") if isinstance(resp.get("metadata"), dict) else {}
        steps = ((resp.get("plan_summary") or {}).get("steps") or []) if isinstance(resp.get("plan_summary"), dict) else []
        explain_debug = resp.get("explain_debug") if isinstance(resp.get("explain_debug"), dict) else {}
        print("")
        print("=== Motadata Ask Summary ===")
        print(f"request_id: {resp.get('request_id')}")
        print(f"posture: {resp.get('governance_posture')}  executed: {resp.get('execution')}")
        print(f"ask_path: {(resp.get('evidence_first_meta') or {}).get('ask_path')}")
        print(f"quality: {md.get('evidence_quality')}  reasons: {md.get('quality_reasons')}")
        if task_type == "EXPLAIN_DEBUG":
            dbg_summary = str(explain_debug.get("summary") or "").strip()
            dbg_logic = str(explain_debug.get("logic_flow") or "").strip()
            dbg_quality = str(md.get("debug_narration_quality") or "").strip().upper()
            dbg_issues = md.get("debug_narration_issues") if isinstance(md.get("debug_narration_issues"), list) else []
            if dbg_summary:
                print(f"debug_summary: {dbg_summary}")
            if dbg_logic:
                first = dbg_logic.splitlines()[0].strip()
                if first:
                    print(f"debug_logic_head: {first}")
            if dbg_quality == "CURATED":
                issue_note = f", issues={len(dbg_issues)}" if dbg_issues else ""
                print(f"debug_note: narration curated by governance for precision{issue_note}")
        if steps:
            shaped = shape_prompt_summary(query, resp)
            answer_1 = str(shaped.get("answer_1") or "").strip()
            next_step = str(shaped.get("next_step") or "").strip()
            if answer_1:
                print(f"answer_1: {answer_1}")
            if next_step:
                print(f"next_step: {next_step}")
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


def _stack_monitor_cfg(cfg: Cfg) -> stack_daemon.StackMonitorConfig:
    return stack_daemon.StackMonitorConfig(
        context_url=cfg.context_url,
        plan_gate_url=cfg.plan_gate_url,
        timeout_sec=cfg.timeout_sec,
        state_dir=cfg.state_dir,
        workspace_root=cfg.workspace_root,
        plan_gate_ssh_target=cfg.plan_gate_ssh_target,
        plan_gate_ssh_remote_port=cfg.plan_gate_ssh_remote_port,
        verbose=cfg.verbose,
    )


def _cmd_bootstrap(args: argparse.Namespace) -> int:
    cfg = Cfg(args)
    sm = _stack_monitor_cfg(cfg)
    fix = not bool(getattr(args, "check_only", False))
    return stack_daemon.run_bootstrap(sm, fix=fix, json_out=bool(getattr(args, "json", False)))


def _cmd_stack(args: argparse.Namespace) -> int:
    cfg = Cfg(args)
    sm = _stack_monitor_cfg(cfg)
    cmd = getattr(args, "stack_cmd", "") or ""
    if cmd == "check":
        return stack_daemon.run_check(
            sm,
            json_out=bool(getattr(args, "json", False)),
            try_tunnel=bool(getattr(args, "try_tunnel", False)),
        )
    if cmd == "watch":
        return stack_daemon.run_watch(
            sm,
            interval_sec=int(getattr(args, "interval", 30)),
            auto_tunnel=bool(getattr(args, "auto_tunnel", False)),
            auto_context=bool(getattr(args, "auto_context", False)),
            quiet=bool(getattr(args, "quiet", False)),
        )
    print(f"unknown stack subcommand: {cmd}", file=sys.stderr)
    return 2


def _cmd_version(_args: argparse.Namespace) -> int:
    print("mcoder unified package CLI")
    try:
        import importlib.metadata as md
        print(f"mcoder-suite version: {md.version('mcoder-suite')}")
    except Exception:
        pass
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mcoder",
        description=(
            "mcoder unified developer CLI for Motadata on WSL/Linux. "
            "Supports setup, diagnostics, and governed ask/debug/plan flows."
        ),
        epilog=(
            "Examples:\n"
            "  mcoder init --workspace-root /root/Harshil-PoCs/Motadata --plan-gate-url http://127.0.0.1:8089\n"
            "  mcoder bootstrap\n"
            "  mcoder doctor\n"
            "  mcoder --timeout-sec 10 health --auto-fix\n"
            "  mcoder stack check\n"
            "  mcoder stack watch --interval 60 --auto-tunnel --auto-context\n"
            "  mcoder --timeout-sec 20 prompt \"Which class is the base class for all APIs?\""
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument("--verbose", action="store_true", help="Enable detailed diagnostic output")
    p.add_argument("--config", default="", help="Path to explicit mcoder config.yaml")
    p.add_argument("--timeout-sec", type=int, default=int(os.environ.get("MCODER_TIMEOUT_SEC", "15")), help="HTTP timeout in seconds for health/export/ask calls")
    p.add_argument("--workspace-root", default="", help="Override workspace root path")
    p.add_argument("--context-url", default="", help="Override Context Layer base URL")
    p.add_argument("--plan-gate-url", default="", help="Override Plan-Gate base URL")
    sub = p.add_subparsers(
        dest="cmd",
        required=True,
        title="commands",
        description="Run `mcoder <command> --help` for command-specific options.",
    )

    s = sub.add_parser(
        "init",
        help="Create/refresh project-local .mcoder config files",
        description="Initialize .mcoder/config.yaml and .mcoder/context.env for current project.",
    )
    s.add_argument("--workspace-root", default="")
    s.add_argument("--context-url", default="")
    s.add_argument("--plan-gate-url", default="")
    s.add_argument(
        "--plan-gate-ssh",
        default="",
        dest="plan_gate_ssh",
        metavar="USER@HOST",
        help="Write plan_gate_ssh_target for mcoder bootstrap SSH tunnel (loopback plan_gate_url)",
    )
    s.add_argument(
        "--ssh-remote-port",
        type=int,
        default=None,
        dest="ssh_remote_port",
        metavar="PORT",
        help="Remote Plan-Gate port on GPU (written when --plan-gate-ssh is set; default 8089)",
    )
    s.add_argument("--force", action="store_true", help="Overwrite existing config/context files")
    s.set_defaults(func=_cmd_init)

    boot = sub.add_parser(
        "bootstrap",
        help="Session checklist: package, Context Layer & Plan-Gate health, SSH tunnel when configured",
        description=(
            "Runs ordered steps after install/init: verify mcoder-suite, probe both /healthz endpoints,\n"
            "optionally restart mcoder-context (systemd user) if Context Layer is down, then create SSH -L\n"
            "forward to Plan-Gate when plan_gate_url is loopback and plan_gate_ssh_target / MCODER_PLAN_GATE_SSH is set.\n"
            "Use --check-only to skip remediation (inspect only)."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    boot.add_argument("--plan-gate-ssh", default="", dest="plan_gate_ssh", metavar="USER@HOST", help="SSH target for Plan-Gate forward")
    boot.add_argument("--ssh-remote-port", type=int, default=None, dest="ssh_remote_port", metavar="PORT", help="Remote GPU Plan-Gate port")
    boot.add_argument(
        "--check-only",
        action="store_true",
        help="Do not restart Context Layer or create SSH tunnel (health probes only)",
    )
    boot.add_argument("--json", action="store_true", help="Machine-readable checklist on stdout")
    boot.set_defaults(func=_cmd_bootstrap)

    s = sub.add_parser(
        "health",
        help="Check Context Layer and Plan-Gate health",
        description="Run bounded health checks and optional auto-remediation with journaling.",
    )
    s.add_argument("--auto-fix", action="store_true", help="Attempt safe local remediations and config fallback updates")
    s.set_defaults(func=_cmd_health)

    s = sub.add_parser(
        "doctor",
        help="Run readiness diagnostics",
        description="Validate config, workspace, service reachability, API mode, and Neo4j availability.",
    )
    s.set_defaults(func=_cmd_doctor)

    stack_p = sub.add_parser(
        "stack",
        help="Stack diagnostics (non-intrusive by default; optional remediation flags)",
        description=(
            "check: read-only except optional --try-tunnel (explicit opt-in).\n"
            "watch: by default only appends JSON to .mcoder/logs/stack-watch.log — no ssh, no systemctl, no terminal spam.\n"
            "Use --auto-tunnel / --auto-context only when you want remediation; --verbose for console lines.\n"
            "Config: plan_gate_ssh_target in .mcoder/config.yaml or MCODER_PLAN_GATE_SSH."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    stack_p.add_argument(
        "--plan-gate-ssh",
        default="",
        dest="plan_gate_ssh",
        metavar="USER@HOST",
        help="Override SSH destination for Plan-Gate port forward (same as MCODER_PLAN_GATE_SSH)",
    )
    stack_p.add_argument(
        "--ssh-remote-port",
        type=int,
        default=None,
        dest="ssh_remote_port",
        metavar="PORT",
        help="Remote Plan-Gate port on GPU host (default 8089 or plan_gate_ssh_remote_port in config)",
    )
    stack_sub = stack_p.add_subparsers(dest="stack_cmd", required=True, title="stack commands")
    sc = stack_sub.add_parser(
        "check",
        help="One-shot wheel + Context Layer + Plan-Gate diagnostics",
    )
    sc.add_argument("--json", action="store_true", help="Emit JSON for automation")
    sc.add_argument(
        "--try-tunnel",
        action="store_true",
        help="If Plan-Gate URL is loopback and unhealthy, try starting ssh -L once",
    )
    sc.set_defaults(func=_cmd_stack)
    sw = stack_sub.add_parser(
        "watch",
        help="Periodic observe-only logging (optional remediation flags)",
        description=(
            "Runs until SIGTERM/SIGINT.\n"
            "Default: append JSON lines to .mcoder/logs/stack-watch.log only — no ssh, no systemctl, no per-tick stdout.\n"
            "Use --verbose for JSON on stdout; --quiet for zero console output.\n"
            "Run under systemd --user or tmux on WSL."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    sw.add_argument("--interval", type=int, default=30, help="Seconds between iterations (minimum 5)")
    sw.add_argument(
        "--auto-tunnel",
        action="store_true",
        help="When Plan-Gate fails on loopback, call ssh -L using plan_gate_ssh_target",
    )
    sw.add_argument(
        "--auto-context",
        action="store_true",
        help="When Context Layer fails, run systemctl --user restart mcoder-context",
    )
    sw.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress startup banner (still logs to stack-watch.log only)",
    )
    sw.set_defaults(func=_cmd_stack)

    s = sub.add_parser(
        "prompt",
        help="Run one governed ask query",
        description="Implicitly exports evidence then calls Plan-Gate /v1/ask.",
    )
    s.add_argument("query", help="Question to ask")
    s.add_argument("--json", action="store_true", help="Print full JSON response instead of concise summary")
    s.set_defaults(func=_cmd_prompt)

    s = sub.add_parser(
        "plan",
        help="Run one plan-focused query",
        description="Ask path with plan_contract.v1 response extension enabled.",
    )
    s.add_argument("query", help="Planning prompt")
    s.add_argument("--json", action="store_true", help="Print full JSON response instead of concise summary")
    s.set_defaults(func=_cmd_plan)

    s = sub.add_parser(
        "debug",
        help="Run one debug-focused query for selected file",
        description="Ask path with task_type=EXPLAIN_DEBUG and selected file anchoring.",
    )
    s.add_argument("--file", required=True, help="File path to anchor debug analysis")
    s.add_argument("--query", default="", help="Debug question")
    s.add_argument("--symbol", default="", help="Optional symbol/method hint")
    s.add_argument("--json", action="store_true", help="Print full JSON response instead of concise summary")
    s.set_defaults(func=_cmd_debug)

    s = sub.add_parser(
        "scenario",
        help="Run batch scenario file",
        description="Execute ask/plan/debug scenario lists from a file.",
    )
    s.add_argument("--type", choices=["ask", "plan", "debug"], required=True, help="Scenario mode")
    s.add_argument("--file", required=True, help="Scenario list file path")
    s.add_argument("--out-dir", default="", help="Optional output directory for saved responses")
    s.set_defaults(func=_cmd_scenario)

    s = sub.add_parser(
        "version",
        help="Show mcoder package version",
        description="Print unified CLI identity and installed package version.",
    )
    s.set_defaults(func=_cmd_version)
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

