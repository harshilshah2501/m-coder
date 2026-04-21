from __future__ import annotations

from pathlib import Path

from runtime.scripts.neo4j_ask_stack import (
    DEFAULT_MOTADATA_REPO_ROOT,
    StackConfig,
    _docker_run_command,
    _source_dirs,
    _workspace_root_from_arg,
)


def test_workspace_root_defaults_to_motadata_path(monkeypatch):
    monkeypatch.delenv("MOTADATA_REPO_ROOT", raising=False)
    root = _workspace_root_from_arg("")
    assert root == DEFAULT_MOTADATA_REPO_ROOT.resolve()


def test_workspace_root_prefers_env_when_arg_missing(monkeypatch, tmp_path):
    motadata = tmp_path / "MotadataEnv"
    motadata.mkdir()
    monkeypatch.setenv("MOTADATA_REPO_ROOT", str(motadata))
    root = _workspace_root_from_arg("")
    assert root == motadata.resolve()


def test_source_dirs_default_to_motadata_java_dir():
    dirs = _source_dirs([])
    assert dirs == ("motadata/src/main/java",)


def test_docker_run_command_sets_restart_ports_and_volume():
    cfg = StackConfig(
        workspace_root=Path("/tmp/motadata"),
        source_dirs=("motadata/src/main/java",),
        neo4j_uri="bolt://127.0.0.1:7687",
        neo4j_user="neo4j",
        neo4j_password="secret",
        container_name="motadata-neo4j",
        image="neo4j:5",
        data_volume="motadata_neo4j_data",
        http_port=7474,
        bolt_port=7687,
        wait_timeout_s=60,
    )
    cmd = _docker_run_command(cfg)
    text = " ".join(cmd)
    assert "--restart unless-stopped" in text
    assert "-p 7474:7474" in text
    assert "-p 7687:7687" in text
    assert "-v motadata_neo4j_data:/data" in text
    assert "NEO4J_AUTH=neo4j/secret" in text

