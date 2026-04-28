"""Periodic stack diagnostics: install check, Context Layer / Plan-Gate health, optional SSH tunnel."""

from __future__ import annotations

import datetime as dt
import importlib.metadata
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.mcoder_cli import venv_diagnose


@dataclass
class StackMonitorConfig:
    """Configuration for stack check/watch (decoupled from CLI Cfg to avoid import cycles)."""

    context_url: str
    plan_gate_url: str
    timeout_sec: int
    state_dir: Path
    workspace_root: str
    plan_gate_ssh_target: str = ""
    plan_gate_ssh_remote_port: int = 8089
    verbose: bool = False


def _now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _http_code(url: str, timeout_sec: int) -> str:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as r:
            return str(r.status)
    except urllib.error.HTTPError as e:
        return str(e.code)
    except Exception:
        return "000"


def plan_gate_loopback_info(plan_gate_url: str) -> tuple[bool, int]:
    """Return (is_loopback, local_port) for ssh -L binding decisions."""
    u = urllib.parse.urlparse(plan_gate_url)
    h = (u.hostname or "").lower()
    port = u.port or 8089
    if u.scheme == "http" and h in ("127.0.0.1", "localhost", "::1"):
        return True, port
    return False, port


def check_wheel() -> tuple[bool, str]:
    """Verify mcoder-suite is importable as an installed distribution."""
    try:
        v = importlib.metadata.version("mcoder-suite")
        return True, v
    except importlib.metadata.PackageNotFoundError:
        return False, "mcoder-suite not installed in this interpreter (pip install mcoder-suite)"
    except Exception as e:
        return False, str(e)


def _tunnel_pid_file(state_dir: Path) -> Path:
    d = state_dir / "stack"
    d.mkdir(parents=True, exist_ok=True)
    return d / "tunnel.pid"


def _tunnel_log(state_dir: Path) -> Path:
    d = state_dir / "stack"
    d.mkdir(parents=True, exist_ok=True)
    return d / "tunnel.log"


def _read_tunnel_pid(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def maybe_start_ssh_tunnel(cfg: StackMonitorConfig, *, replace_stale_tunnel: bool = False) -> tuple[bool, str]:
    """If Plan-Gate URL is loopback and ssh target is set, start ssh -L or report why not."""
    is_lo, local_port = plan_gate_loopback_info(cfg.plan_gate_url)
    if not is_lo:
        return False, "plan_gate_url is not loopback; SSH tunnel not used"
    if not cfg.plan_gate_ssh_target.strip():
        return False, "plan_gate_ssh_target unset (set in config or MCODER_PLAN_GATE_SSH)"
    remote_port = cfg.plan_gate_ssh_remote_port
    health = _http_code(f"http://127.0.0.1:{local_port}/healthz", cfg.timeout_sec)
    if health == "200":
        return True, "Plan-Gate already reachable on loopback (tunnel or local)"

    pid_file = _tunnel_pid_file(cfg.state_dir)
    old = _read_tunnel_pid(pid_file)
    if old is not None and _pid_alive(old):
        if replace_stale_tunnel:
            try:
                os.kill(old, signal.SIGTERM)
            except ProcessLookupError:
                pass
            time.sleep(0.5)
            try:
                pid_file.unlink(missing_ok=True)
            except OSError:
                pass
        else:
            return False, f"tunnel pid {old} present but health still failing; see {_tunnel_log(cfg.state_dir)}"

    log_f = _tunnel_log(cfg.state_dir)
    bind = f"{local_port}:127.0.0.1:{remote_port}"
    cmd = [
        "ssh",
        "-N",
        "-o",
        "ExitOnForwardFailure=yes",
        "-o",
        "ServerAliveInterval=30",
        "-o",
        "ServerAliveCountMax=3",
        "-o",
        "BatchMode=yes",
        "-L",
        bind,
        cfg.plan_gate_ssh_target.strip(),
    ]
    with log_f.open("a", encoding="utf-8") as log:
        log.write(f"\n{_now_utc()} starting tunnel {' '.join(cmd)}\n")
        log.flush()
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        except FileNotFoundError:
            return False, "ssh executable not found"
        except Exception as e:
            return False, str(e)

    pid_file.write_text(str(proc.pid), encoding="utf-8")
    time.sleep(1.5)
    health2 = _http_code(f"http://127.0.0.1:{local_port}/healthz", cfg.timeout_sec)
    if health2 == "200":
        return True, f"started ssh tunnel pid={proc.pid} ({bind})"
    proc.poll()
    if proc.returncode is not None:
        tail = log_f.read_text(encoding="utf-8")[-800:] if log_f.is_file() else ""
        return False, f"ssh exited ({proc.returncode}); log tail:\n{tail}"
    return False, f"tunnel pid={proc.pid} started but health not OK yet (retry or check {log_f})"


def maybe_restart_context_layer(_cfg: StackMonitorConfig) -> tuple[bool, str]:
    """Best-effort systemd user restart for mcoder-context."""
    try:
        r = subprocess.run(
            ["systemctl", "--user", "restart", "mcoder-context"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode == 0:
            return True, "systemctl --user restart mcoder-context OK"
        msg = (r.stderr or r.stdout or "").strip() or f"exit {r.returncode}"
        return False, msg
    except FileNotFoundError:
        return False, "systemctl not available"
    except Exception as e:
        return False, str(e)


def run_check(cfg: StackMonitorConfig, *, json_out: bool = False, try_tunnel: bool = False) -> int:
    """One-shot: wheel + context + plan-gate; optional single tunnel attempt."""
    rows: list[dict[str, Any]] = []

    ok, wheel_msg = check_wheel()
    rows.append({"component": "wheel", "ok": ok, "detail": wheel_msg})

    ctx_url = f"{cfg.context_url.rstrip('/')}/healthz"
    ctx_code = _http_code(ctx_url, cfg.timeout_sec)
    ctx_ok = ctx_code == "200"
    rows.append({"component": "context_layer", "ok": ctx_ok, "detail": ctx_url, "http": ctx_code})

    pg_url = f"{cfg.plan_gate_url.rstrip('/')}/healthz"
    pg_code = _http_code(pg_url, cfg.timeout_sec)
    pg_ok = pg_code == "200"
    rows.append({"component": "plan_gate", "ok": pg_ok, "detail": pg_url, "http": pg_code})

    is_lo, _lp = plan_gate_loopback_info(cfg.plan_gate_url)
    tunnel_note = ""
    if try_tunnel and is_lo and not pg_ok and cfg.plan_gate_ssh_target.strip():
        ok_t, tunnel_note = maybe_start_ssh_tunnel(cfg)
        rows.append({"component": "tunnel_attempt", "ok": ok_t, "detail": tunnel_note})
        pg_code = _http_code(pg_url, cfg.timeout_sec)
        pg_ok = pg_code == "200"
        rows.append({"component": "plan_gate_after_tunnel", "ok": pg_ok, "detail": pg_url, "http": pg_code})

    fails = sum([not ok, not ctx_ok, not pg_ok])

    if json_out:
        print(json.dumps({"timestamp_utc": _now_utc(), "checks": rows}, indent=2))
    else:
        print(f"mcoder stack check @ {_now_utc()}")
        print(f"  wheel (mcoder-suite): {'OK ' + wheel_msg if ok else 'FAIL ' + wheel_msg}")
        print(f"  Context Layer: {'OK' if ctx_ok else 'FAIL'} {ctx_url} (http={ctx_code})")
        print(f"  Plan-Gate: {'OK' if pg_ok else 'FAIL'} {pg_url} (http={pg_code})")
        if tunnel_note:
            print(f"  tunnel: {tunnel_note}")
        if not is_lo:
            print("  note: Plan-Gate is not loopback; ssh tunnel not applicable — use reachable plan_gate_url.")
        elif not pg_ok and not cfg.plan_gate_ssh_target.strip():
            print("  hint: for SSH tunnel automation, set plan_gate_ssh_target or MCODER_PLAN_GATE_SSH")

    return 0 if fails == 0 else 1


def run_bootstrap(cfg: StackMonitorConfig, *, fix: bool = True, json_out: bool = False) -> int:
    """Ordered checklist: wheel → Context Layer → Plan-Gate (optional SSH tunnel) → final health.

    When ``fix`` is True (default), attempts ``systemctl --user restart mcoder-context`` if Context Layer
    is down, and brings up ``ssh -L`` when ``plan_gate_url`` is loopback and ``plan_gate_ssh_target`` is set.
    Use ``fix=False`` (--check-only) for a read-only diagnostic pass.
    """
    lines: list[dict[str, Any]] = []
    _out = print if not json_out else lambda *_a, **_k: None

    _out("=== mcoder bootstrap (session checklist) ===")
    if not json_out:
        venv_diagnose.print_venv_report()
        _out("")
    _out(f"config: context={cfg.context_url} plan_gate={cfg.plan_gate_url}")
    ssh_hint = cfg.plan_gate_ssh_target.strip() or "(unset — add plan_gate_ssh_target for auto tunnel)"
    _out(f"ssh target: {ssh_hint}")
    _out()

    ok_w, wheel_msg = check_wheel()
    lines.append({"step": 1, "name": "mcoder-suite", "ok": ok_w, "detail": wheel_msg})
    _out(f"[1/5] Installation: mcoder-suite {'OK — ' + wheel_msg if ok_w else 'FAIL — ' + wheel_msg}")

    ctx_url = f"{cfg.context_url.rstrip('/')}/healthz"
    pg_url = f"{cfg.plan_gate_url.rstrip('/')}/healthz"

    ctx_code = _http_code(ctx_url, cfg.timeout_sec)
    ctx_ok = ctx_code == "200"
    lines.append({"step": 2, "name": "context_layer", "ok": ctx_ok, "http": ctx_code, "url": ctx_url})
    _out(f"[2/5] Context Layer: GET {ctx_url} → http={ctx_code} {'OK' if ctx_ok else 'FAIL'}")

    if not ctx_ok and fix:
        ok_r, msg = maybe_restart_context_layer(cfg)
        lines.append({"step": "2b", "name": "context_remediation", "ok": ok_r, "detail": msg})
        _out(f"       remediation (systemctl): {msg}")
        time.sleep(2.0)
        ctx_code = _http_code(ctx_url, cfg.timeout_sec)
        ctx_ok = ctx_code == "200"
        lines.append({"step": "2c", "name": "context_layer_recheck", "ok": ctx_ok, "http": ctx_code})
        _out(f"       re-check Context Layer → http={ctx_code} {'OK' if ctx_ok else 'FAIL'}")
    elif not ctx_ok:
        _out("       (--check-only: not restarting Context Layer service)")

    pg_code = _http_code(pg_url, cfg.timeout_sec)
    pg_ok = pg_code == "200"
    lines.append({"step": 3, "name": "plan_gate_initial", "ok": pg_ok, "http": pg_code, "url": pg_url})
    _out(f"[3/5] Plan-Gate: GET {pg_url} → http={pg_code} {'OK' if pg_ok else 'FAIL'}")

    is_lo, _lp = plan_gate_loopback_info(cfg.plan_gate_url)
    if pg_ok:
        lines.append({"step": 4, "name": "ssh_tunnel", "ok": None, "detail": "not_needed"})
        _out("[4/5] SSH tunnel: not needed (Plan-Gate already healthy)")
    elif not fix:
        lines.append({"step": 4, "name": "ssh_tunnel", "ok": None, "detail": "skipped_check_only"})
        _out("[4/5] SSH tunnel: SKIP (--check-only)")
    elif not is_lo:
        lines.append({"step": 4, "name": "ssh_tunnel", "ok": None, "detail": "skipped_remote_url"})
        _out("[4/5] SSH tunnel: SKIP — plan_gate_url is not loopback (use reachable URL or switch to http://127.0.0.1:8089)")
    elif not cfg.plan_gate_ssh_target.strip():
        lines.append({"step": 4, "name": "ssh_tunnel", "ok": False, "detail": "skipped_no_ssh_target"})
        _out("[4/5] SSH tunnel: SKIP — no plan_gate_ssh_target (cannot forward to GPU)")
        _out("")
        _out("  Fix: add to .mcoder/config.yaml (adjust user@host), then run mcoder bootstrap:")
        _out("    plan_gate_ssh_target: harshil@45.195.82.10")
        _out("    plan_gate_ssh_remote_port: 8089")
        _out("  Or once: MCODER_PLAN_GATE_SSH=harshil@45.195.82.10 mcoder bootstrap")
        _out("  Or: mcoder init --force --workspace-root … --plan-gate-url http://127.0.0.1:8089 \\")
        _out("           --plan-gate-ssh harshil@45.195.82.10")
    else:
        ok_t, msg = maybe_start_ssh_tunnel(cfg, replace_stale_tunnel=True)
        lines.append({"step": 4, "name": "ssh_tunnel", "ok": ok_t, "detail": msg})
        _out(f"[4/5] SSH tunnel to GPU Plan-Gate: {msg}")
        time.sleep(1.5)
        pg_code = _http_code(pg_url, cfg.timeout_sec)
        pg_ok = pg_code == "200"
        lines.append({"step": "4b", "name": "plan_gate_after_tunnel", "ok": pg_ok, "http": pg_code})
        _out(f"       re-check Plan-Gate → http={pg_code} {'OK' if pg_ok else 'FAIL'}")

    ctx_final = _http_code(ctx_url, cfg.timeout_sec)
    pg_final = _http_code(pg_url, cfg.timeout_sec)
    all_ok = ctx_final == "200" and pg_final == "200"
    lines.append(
        {
            "step": 5,
            "name": "final_health",
            "ok": all_ok,
            "context_http": ctx_final,
            "plan_gate_http": pg_final,
        }
    )

    if json_out:
        print(
            json.dumps(
                {
                    "timestamp_utc": _now_utc(),
                    "fix": fix,
                    "context_url": cfg.context_url,
                    "plan_gate_url": cfg.plan_gate_url,
                    "plan_gate_ssh_target": cfg.plan_gate_ssh_target,
                    "steps": lines,
                    "success": all_ok,
                },
                indent=2,
            )
        )
    else:
        _out()
        _out(f"[5/5] Final health: Context Layer http={ctx_final}, Plan-Gate http={pg_final}")
        if all_ok:
            _out()
            _out('Bootstrap complete — both endpoints healthy. Next: mcoder prompt "…"')
        else:
            _out()
            _out("Bootstrap incomplete — fix errors above or see docs/guides/MCODER_API_ONLY_DEVELOPER_SETUP.md")

    return 0 if all_ok else 1


def run_watch(
    cfg: StackMonitorConfig,
    *,
    interval_sec: int,
    auto_tunnel: bool,
    auto_context: bool,
    quiet: bool = False,
) -> int:
    """Loop: health checks; log to stack-watch.log. Remediation only when flags are set.

    Non-intrusive defaults: append JSON to the log only; no ssh/systemctl unless
    --auto-tunnel / --auto-context. Console stays silent except one startup line
    (--quiet) or per-iteration JSON (--verbose).
    """
    log_dir = cfg.state_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    watch_log = log_dir / "stack-watch.log"

    def shutdown(_signum: int | None = None, _frame: Any = None) -> None:
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    if not quiet:
        print(
            f"mcoder stack watch → {watch_log} "
            f"(observe-only; no ssh/systemctl unless --auto-tunnel / --auto-context; "
            f"use --verbose for console lines)",
            flush=True,
        )

    with watch_log.open("a", encoding="utf-8") as slog:
        slog.write(f"\n{_now_utc()} stack watch start interval={interval_sec}s auto_tunnel={auto_tunnel} auto_context={auto_context} quiet={quiet}\n")

    while True:
        line = {"ts": _now_utc(), "context": None, "plan_gate": None, "actions": []}
        ctx_url = f"{cfg.context_url.rstrip('/')}/healthz"
        ctx_code = _http_code(ctx_url, cfg.timeout_sec)
        line["context"] = {"http": ctx_code, "url": ctx_url}

        pg_url = f"{cfg.plan_gate_url.rstrip('/')}/healthz"
        pg_code = _http_code(pg_url, cfg.timeout_sec)
        line["plan_gate"] = {"http": pg_code, "url": pg_url}

        if ctx_code != "200" and auto_context:
            ok_r, msg = maybe_restart_context_layer(cfg)
            line["actions"].append({"restart_context": ok_r, "detail": msg})
            time.sleep(2.0)
            ctx_code = _http_code(ctx_url, cfg.timeout_sec)
            line["context"]["http_after"] = ctx_code

        if pg_code != "200" and auto_tunnel:
            ok_t, msg = maybe_start_ssh_tunnel(cfg)
            line["actions"].append({"tunnel": ok_t, "detail": msg})
            time.sleep(1.0)
            pg_code = _http_code(pg_url, cfg.timeout_sec)
            line["plan_gate"]["http_after"] = pg_code

        summary = "OK" if ctx_code == "200" and pg_code == "200" else "DEGRADED"
        line["summary"] = summary

        rec = json.dumps(line, ensure_ascii=False)
        with watch_log.open("a", encoding="utf-8") as slog:
            slog.write(rec + "\n")

        if cfg.verbose:
            print(rec, flush=True)

        time.sleep(max(5, interval_sec))

