"""Console entrypoint: ``motadata-context-layer`` (installed wheel or editable install)."""

from __future__ import annotations


def main() -> None:
    from runtime.context_layer_service.logging_setup import setup_logging_from_env

    setup_logging_from_env()
    from runtime.context_layer_service.app import main as serve

    serve()
