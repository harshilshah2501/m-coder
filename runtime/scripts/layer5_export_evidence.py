#!/usr/bin/env python3
"""
Export layer5.evidence_bundle.v1 as JSON to stdout (development / CLI).

For packaged deployments, prefer the Context Layer HTTP service
(``python -m runtime.context_layer_service``) or an installed entrypoint
that calls ``runtime.context_layer_service.evidence_api``.

Usage:
  python3 layer5_export_evidence.py <workspace_root>   (query on stdin)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: layer5_export_evidence.py <workspace_root>  (read query from stdin)", file=sys.stderr)
        return 2
    workspace = sys.argv[1].strip()
    query = sys.stdin.read()
    if not query.strip():
        print("error: empty query on stdin", file=sys.stderr)
        return 2

    from runtime.context_layer_service.evidence_api import export_evidence_bundle_dict

    try:
        d = export_evidence_bundle_dict(workspace, query, top_k=8)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    sys.stdout.write(json.dumps(d, ensure_ascii=False))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
