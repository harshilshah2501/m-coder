from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from runtime.layer5.graph import (
    get_call_chain,
    get_entrypoint_flow,
    load_graph_artifacts,
    validate_graph_integrity,
)


def _write_fixture_workspace(root: Path) -> None:
    src = root / "src/main/java/com/mindarray/api"
    src.mkdir(parents=True, exist_ok=True)

    (src / "AbstractAPI.java").write_text(
        (
            "package com.mindarray.api;\n"
            "public abstract class AbstractAPI {}\n"
        ),
        encoding="utf-8",
    )
    (src / "MailServerConfiguration.java").write_text(
        (
            "package com.mindarray.api;\n"
            "public class MailServerConfiguration extends AbstractAPI {\n"
            "  public static void beforeUpdate() {}\n"
            "}\n"
        ),
        encoding="utf-8",
    )
    (src / "SecondaryApiHandler.java").write_text(
        (
            "package com.mindarray.api;\n"
            "public class SecondaryApiHandler extends AbstractAPI {\n"
            "  public static void handle() {}\n"
            "}\n"
        ),
        encoding="utf-8",
    )
    (src / "APIServer.java").write_text(
        (
            "package com.mindarray.api;\n"
            "@RestController\n"
            "public class APIServer {\n"
            "  @GetMapping(\"/api\")\n"
            "  public static void start() {\n"
            "    MailServerConfiguration.beforeUpdate();\n"
            "    SecondaryApiHandler.handle();\n"
            "  }\n"
            "}\n"
        ),
        encoding="utf-8",
    )


def _write_fixture_registry(path: Path) -> None:
    path.write_text(
        (
            "schema_version: \"product_authority_registry.v1.1\"\n"
            "last_updated: \"2026-04-28\"\n"
            "maintainer: \"ci@motadata.local\"\n"
            "concepts:\n"
            "  api_layer:\n"
            "    primary_owner:\n"
            "      file: \"src/main/java/com/mindarray/api/APIServer.java\"\n"
            "      class: \"APIServer\"\n"
            "      method: \"start\"\n"
            "      confidence: \"high\"\n"
            "    verification:\n"
            "      last_verified_at: \"2026-04-28T00:00:00Z\"\n"
            "      verification_source: \"test\"\n"
            "      staleness_threshold_days: 90\n"
            "    aliases: [\"api layer\", \"api architecture\"]\n"
            "    collaborators:\n"
            "      - file: \"src/main/java/com/mindarray/api/AbstractAPI.java\"\n"
            "        role: \"abstraction\"\n"
            "        relationship: \"base\"\n"
            "    forbidden_distractors: []\n"
        ),
        encoding="utf-8",
    )


def _run_build(project_root: Path, workspace: Path, registry: Path, out_dir: Path) -> subprocess.CompletedProcess[str]:
    cmd = [
        "python3",
        "runtime/scripts/build_code_intelligence_graph.py",
        "--workspace-root",
        str(workspace),
        "--registry-path",
        str(registry),
        "--out-dir",
        str(out_dir),
    ]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(project_root)
    return subprocess.run(
        cmd,
        cwd=str(project_root),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def test_cig_v1_smoke_build_and_determinism(tmp_path: Path):
    project_root = Path(__file__).resolve().parents[2]
    workspace = tmp_path / "fixture_workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    registry = tmp_path / "fixture_registry.yaml"
    out_dir = tmp_path / "graph_out"

    _write_fixture_workspace(workspace)
    _write_fixture_registry(registry)

    first = _run_build(project_root, workspace, registry, out_dir)
    assert first.returncode == 0, first.stderr or first.stdout

    jsonl_path = out_dir / "code_intelligence_graph.v1.jsonl"
    manifest_path = out_dir / "code_intelligence_graph.v1.manifest.json"
    adjacency_path = out_dir / "code_intelligence_graph.v1.adjacency.json"
    assert jsonl_path.exists()
    assert manifest_path.exists()
    assert adjacency_path.exists()

    manifest_1 = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_1.get("schema_version") == "code_intelligence_graph.v1"
    assert int(manifest_1.get("stats", {}).get("node_count", 0)) > 0
    assert int(manifest_1.get("stats", {}).get("edge_count", 0)) > 0
    hash_1 = str(manifest_1.get("content_hash", ""))
    assert hash_1

    graph, _ = load_graph_artifacts(out_dir)
    integrity = validate_graph_integrity(graph)
    assert integrity.passed, integrity.errors

    # No-collapse traversal behavior: branched flows/chains should remain branched.
    call_paths = get_call_chain(graph, "APIServer.start")
    assert len(call_paths) >= 2
    assert any("MailServerConfiguration.beforeUpdate" in p for p in call_paths)
    assert any("SecondaryApiHandler.handle" in p for p in call_paths)

    flow_paths = get_entrypoint_flow(graph, "APIServer.start")
    assert len(flow_paths) >= 2

    second = _run_build(project_root, workspace, registry, out_dir)
    assert second.returncode == 0, second.stderr or second.stdout
    manifest_2 = json.loads(manifest_path.read_text(encoding="utf-8"))
    hash_2 = str(manifest_2.get("content_hash", ""))
    assert hash_2 == hash_1

