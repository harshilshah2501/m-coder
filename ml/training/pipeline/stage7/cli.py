"""
Stage-7 freeze CLI forwarding.

Forwards to stage6.stage6c.freeze.cli:main.
"""
from __future__ import annotations

import sys

from stage6.stage6c.freeze.cli import main

if __name__ == "__main__":
    sys.exit(main())
