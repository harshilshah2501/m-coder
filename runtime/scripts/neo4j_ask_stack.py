#!/usr/bin/env python3
"""
All-in-one Neo4j stack manager for Ask class-relationship rollout.

Capabilities:
  - Host Neo4j in Docker with restart policy.
  - Build/refresh class graph from Motadata workspace.
  - Emit/export consistent runtime env flags for Ask-only enablement.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

# Allow direct script execution without requiring PYTHONPATH exports.
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from runtime.scripts.build_neo4j_class_graph import index_class_graph


DEFAULT_MOTADATA_REPO_ROOT = Path("/home/harshil/Projects/Motadata")
DEFAULT_CONTAINER_NAME = "motadata-neo4j"
DEFAULT_IMAGE = "neo4j:5"
DEFAULT_DATA_VOLUME = "motadata_neo4j_data"
DEFAULT_HTTP_PORT = 7474
DEFAULT_BOLT_PORT = 7687
DEFAULT_WAIT_SECONDS = 60


@dataclass(frozen=True)
class StackConfig:
    workspace_root: Path
    source_dirs: tuple[str, ...]
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    container_name: str
    image: str
    data_volume: str
    http_port: int
    bolt_port: int
    wait_timeout_s: int


def _run(cmd: List[str], *, check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def _workspace_root_from_arg(raw: str) -> Path:
    base = raw.strip() if raw and raw.strip() else os.environ.get("MOTADATA_REPO_ROOT", "").strip()
    if not base:
        base = str(DEFAULT_MOTADATA_REPO_ROOT)
    return Path(base).expanduser().resolve()


def _source_dirs(raw_dirs: Iterable[str]) -> tuple[str, ...]:
    vals = tuple(str(v).strip() for v in raw_dirs if str(v).strip())
    return vals if vals else ("motadata/src/main/java",)


def _resolve_password(cli_password: str, env_password: str) -> str:
    cli = (cli_password or "").strip()
    if cli:
        return cli
    env = (env_password or "").strip()
    if env:
        return env
    if sys.stdin.isatty():
        prompt = getpass.getpass("Enter Neo4j password (MOTADATA_NEO4J_PASSWORD): ").strip()
        if prompt:
            return prompt
    raise SystemExit("Neo4j password is required (--neo4j-password or MOTADATA_NEO4J_PASSWORD).")


def _docker_names(only_running: bool) -> set[str]:
    cmd = ["docker", "ps", "--format", "{{.Names}}"]
    if not only_running:
        cmd.insert(2, "-a")
    out = _run(cmd).stdout.strip()
    return {line.strip() for line in out.splitlines() if line.strip()}


def _container_exists(name: str) -> bool:
    return name in _docker_names(only_running=False)


def _container_running(name: str) -> bool:
    return name in _docker_names(only_running=True)


def _docker_run_command(cfg: StackConfig) -> List[str]:
    return [
        "docker",
        "run",
        "-d",
        "--name",
        cfg.container_name,
        "--restart",
        "unless-stopped",
        "-p",
        f"{cfg.http_port}:7474",
        "-p",
        f"{cfg.bolt_port}:7687",
        "-e",
        f"NEO4J_AUTH={cfg.neo4j_user}/{cfg.neo4j_password}",
        "-v",
        f"{cfg.data_volume}:/data",
        cfg.image,
    ]


def _ensure_docker() -> None:
    try:
        _run(["docker", "--version"])
    except Exception as exc:
        raise RuntimeError("Docker is required for Neo4j hosting but is unavailable.") from exc


def _wait_for_neo4j(cfg: StackConfig) -> None:
    try:
        from neo4j import GraphDatabase  # type: ignore
    except Exception as exc:
        raise RuntimeError("neo4j python driver is required; install with `pip install neo4j`.") from exc

    auth = (cfg.neo4j_user, cfg.neo4j_password) if (cfg.neo4j_user or cfg.neo4j_password) else None
    deadline = time.time() + max(5, int(cfg.wait_timeout_s))
    last_err = ""
    while time.time() < deadline:
        try:
            driver = GraphDatabase.driver(cfg.neo4j_uri, auth=auth)
            driver.verify_connectivity()
            driver.close()
            return
        except Exception as exc:  # pragma: no cover - runtime dependent
            last_err = str(exc)
            time.sleep(2.0)
    raise RuntimeError(f"Neo4j did not become ready within {cfg.wait_timeout_s}s: {last_err}")


def _host_up(cfg: StackConfig) -> str:
    _ensure_docker()
    if _container_running(cfg.container_name):
        return "already_running"
    if _container_exists(cfg.container_name):
        _run(["docker", "start", cfg.container_name])
        return "started_existing"
    _run(_docker_run_command(cfg))
    return "created"


def _host_down(cfg: StackConfig, *, remove_container: bool) -> str:
    if _container_running(cfg.container_name):
        _run(["docker", "stop", cfg.container_name])
    if remove_container and _container_exists(cfg.container_name):
        _run(["docker", "rm", cfg.container_name])
        return "stopped_and_removed"
    return "stopped"


def _emit_env(cfg: StackConfig, env_out: Path | None) -> dict:
    payload = {
        "MOTADATA_NEO4J_URI": cfg.neo4j_uri,
        "MOTADATA_NEO4J_USER": cfg.neo4j_user,
        "MOTADATA_NEO4J_PASSWORD": cfg.neo4j_password,
        "MOTADATA_NEO4J_ENABLED": "1",
        "MOTADATA_NEO4J_ASK_ENABLED": "1",
        "MOTADATA_NEO4J_DEBUG_ENABLED": "0",
        "MOTADATA_NEO4J_CODE_ENABLED": "0",
    }
    if env_out:
        env_out.parent.mkdir(parents=True, exist_ok=True)
        lines = [f'export {k}="{v}"' for k, v in payload.items()]
        env_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def _index(cfg: StackConfig, *, clear_existing: bool) -> dict:
    return index_class_graph(
        workspace_root=cfg.workspace_root,
        source_dirs=list(cfg.source_dirs),
        max_files=100000,
        neo4j_uri=cfg.neo4j_uri,
        neo4j_user=cfg.neo4j_user,
        neo4j_password=cfg.neo4j_password,
        clear_existing=clear_existing,
    )


def _status(cfg: StackConfig) -> dict:
    running = _container_running(cfg.container_name)
    exists = _container_exists(cfg.container_name)
    state = {"exists": exists, "running": running}
    if exists:
        insp = _run(["docker", "inspect", cfg.container_name]).stdout
        try:
            obj = json.loads(insp)
            if obj and isinstance(obj, list):
                st = ((obj[0] or {}).get("State") or {}) if isinstance(obj[0], dict) else {}
                health = (st.get("Health") or {}).get("Status") if isinstance(st, dict) else None
                state["health"] = str(health or "n/a")
        except Exception:
            state["health"] = "unknown"
    return state


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Neo4j Ask stack manager (host + index + refresh).")
    p.add_argument(
        "--workspace-root",
        default="",
        help=f"Motadata workspace root (default: {DEFAULT_MOTADATA_REPO_ROOT})",
    )
    p.add_argument(
        "--source-dir",
        action="append",
        default=[],
        help='Relative source dir for indexing (repeatable, default: "motadata/src/main/java").',
    )
    p.add_argument("--neo4j-uri", default="bolt://127.0.0.1:7687")
    p.add_argument("--neo4j-user", default="neo4j")
    p.add_argument("--neo4j-password", default="")
    p.add_argument("--container-name", default=DEFAULT_CONTAINER_NAME)
    p.add_argument("--image", default=DEFAULT_IMAGE)
    p.add_argument("--data-volume", default=DEFAULT_DATA_VOLUME)
    p.add_argument("--http-port", type=int, default=DEFAULT_HTTP_PORT)
    p.add_argument("--bolt-port", type=int, default=DEFAULT_BOLT_PORT)
    p.add_argument("--wait-timeout-s", type=int, default=DEFAULT_WAIT_SECONDS)
    p.add_argument("--env-out", default="runtime/.run/neo4j_ask.env")

    sp = p.add_subparsers(dest="command", required=True)
    sp.add_parser("up", help="Start/host Neo4j container and wait for readiness.")
    sp.add_parser("status", help="Show Neo4j container status.")
    down = sp.add_parser("down", help="Stop Neo4j container.")
    down.add_argument("--remove-container", action="store_true")
    sp.add_parser("index", help="Generate/replace class graph (full rebuild).")
    sp.add_parser("refresh", help="Refresh class graph in-place (no graph wipe).")
    bootstrap = sp.add_parser("bootstrap", help="All-in-one: up + wait + full index + env export.")
    bootstrap.add_argument("--skip-index", action="store_true", help="Only host Neo4j and emit env.")
    return p


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    workspace_root = _workspace_root_from_arg(args.workspace_root)
    source_dirs = _source_dirs(args.source_dir)
    password = _resolve_password(
        args.neo4j_password,
        os.environ.get("MOTADATA_NEO4J_PASSWORD", ""),
    )
    cfg = StackConfig(
        workspace_root=workspace_root,
        source_dirs=source_dirs,
        neo4j_uri=args.neo4j_uri.strip(),
        neo4j_user=args.neo4j_user.strip(),
        neo4j_password=password,
        container_name=args.container_name.strip(),
        image=args.image.strip(),
        data_volume=args.data_volume.strip(),
        http_port=int(args.http_port),
        bolt_port=int(args.bolt_port),
        wait_timeout_s=int(args.wait_timeout_s),
    )
    env_out = Path(args.env_out).resolve() if str(args.env_out).strip() else None

    if args.command == "status":
        print(json.dumps(_status(cfg), indent=2))
        return 0

    if args.command == "down":
        result = _host_down(cfg, remove_container=bool(args.remove_container))
        print(f"neo4j_host={result}")
        return 0

    if args.command == "up":
        hosted = _host_up(cfg)
        _wait_for_neo4j(cfg)
        print(f"neo4j_host={hosted} uri={cfg.neo4j_uri}")
        return 0

    if args.command == "index":
        stats = _index(cfg, clear_existing=True)
        print(json.dumps({"action": "index", "stats": stats}, indent=2))
        return 0

    if args.command == "refresh":
        stats = _index(cfg, clear_existing=False)
        print(json.dumps({"action": "refresh", "stats": stats}, indent=2))
        return 0

    if args.command == "bootstrap":
        hosted = _host_up(cfg)
        _wait_for_neo4j(cfg)
        payload = _emit_env(cfg, env_out)
        out = {
            "action": "bootstrap",
            "host": hosted,
            "uri": cfg.neo4j_uri,
            "workspace_root": str(cfg.workspace_root),
            "source_dirs": list(cfg.source_dirs),
            "env_out": str(env_out) if env_out else "",
            "env": payload,
            "index": None,
        }
        if not bool(args.skip_index):
            out["index"] = _index(cfg, clear_existing=True)
        print(json.dumps(out, indent=2))
        if env_out:
            print(f"\nsource {shlex.quote(str(env_out))}")
        return 0

    raise SystemExit(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

