"""Minimal test for the taxonomy calibration harness CLI."""
import sys

import pytest


def test_calibrate_taxonomy_cli_output(capsys, monkeypatch):
    """Harness runs and prints expected sections for scenario a."""
    from stage6.stage6c.tools.calibrate_taxonomy import main

    monkeypatch.setattr(sys, "argv", ["prog", "--scenario", "a"])
    main()
    out = capsys.readouterr().out

    assert "Scenario A" in out
    assert "severity:" in out
    assert "collapses:" in out
    assert "BIS:" in out
