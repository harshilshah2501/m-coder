"""Unit tests for stack_daemon helpers."""

from runtime.mcoder_cli.stack_daemon import plan_gate_loopback_info


def test_plan_gate_loopback_localhost() -> None:
    ok, port = plan_gate_loopback_info("http://127.0.0.1:8089/healthz")
    assert ok is True
    assert port == 8089


def test_plan_gate_loopback_default_port() -> None:
    ok, port = plan_gate_loopback_info("http://localhost:/")
    assert ok is True
    assert port == 8089


def test_plan_gate_remote_not_loopback() -> None:
    ok, port = plan_gate_loopback_info("http://45.195.82.10:8089/")
    assert ok is False
    assert port == 8089
