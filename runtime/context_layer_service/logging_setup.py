"""Stdlib logging for Context Layer service (file and/or stderr)."""

from __future__ import annotations

import logging
import os
import sys
from typing import Optional


def setup_logging_from_env() -> None:
    """Configure root logger once from env (idempotent if handlers already present)."""
    if logging.getLogger().handlers:
        return

    level_name = (os.environ.get("MOTADATA_CONTEXT_LAYER_LOG_LEVEL") or "INFO").strip().upper()
    level = getattr(logging, level_name, logging.INFO)
    log_path = (os.environ.get("MOTADATA_CONTEXT_LAYER_LOG_PATH") or "").strip()

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s [motadata-context-layer] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    root = logging.getLogger()
    root.setLevel(level)

    h_stderr = logging.StreamHandler(sys.stderr)
    h_stderr.setFormatter(fmt)
    root.addHandler(h_stderr)

    if log_path:
        try:
            h_file = logging.FileHandler(log_path, encoding="utf-8")
            h_file.setFormatter(fmt)
            root.addHandler(h_file)
        except OSError as e:
            root.warning("Could not open MOTADATA_CONTEXT_LAYER_LOG_PATH=%s: %s", log_path, e)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name or "motadata_context_layer")
