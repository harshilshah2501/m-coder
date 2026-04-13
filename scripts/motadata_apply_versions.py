#!/usr/bin/env python3
"""Apply MOTADATA_CONTEXT_LAYER_VERSION and MOTADATA_JETBRAINS_PLUGIN_VERSION to repo files."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def main() -> int:
    repo = Path(os.environ.get("M_CODER_REPO_ROOT", Path(__file__).resolve().parent.parent))
    cl_ver = os.environ.get("MOTADATA_CONTEXT_LAYER_VERSION", "").strip()
    jb_ver = os.environ.get("MOTADATA_JETBRAINS_PLUGIN_VERSION", "").strip()
    if not cl_ver or not jb_ver:
        print("Set MOTADATA_CONTEXT_LAYER_VERSION and MOTADATA_JETBRAINS_PLUGIN_VERSION", file=sys.stderr)
        return 1

    pyproject = repo / "packaging" / "motadata-context-layer" / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    m = re.search(r"^version\s*=\s*\"([^\"]*)\"", text, flags=re.MULTILINE)
    if not m:
        print(f"[WARN] {pyproject.relative_to(repo)}: no version = line found", file=sys.stderr)
    elif m.group(1) == cl_ver:
        print(f"[OK] {pyproject.relative_to(repo)} already at {cl_ver}")
    else:
        text_new = re.sub(
            r'^version\s*=\s*"[^"]*"',
            f'version = "{cl_ver}"',
            text,
            count=1,
            flags=re.MULTILINE,
        )
        pyproject.write_text(text_new, encoding="utf-8")
        print(f"[OK] {pyproject.relative_to(repo)} -> {cl_ver}")

    gradle = repo / "jetbrains-plugin" / "build.gradle.kts"
    gtxt = gradle.read_text(encoding="utf-8")
    gm = re.search(r'^version\s*=\s*"([^"]*)"', gtxt, flags=re.MULTILINE)
    if not gm:
        print(f"[WARN] {gradle.relative_to(repo)}: no version = line found", file=sys.stderr)
    elif gm.group(1) == jb_ver:
        print(f"[OK] {gradle.relative_to(repo)} already at {jb_ver}")
    else:
        gnew = re.sub(
            r'^version\s*=\s*"[^"]*"',
            f'version = "{jb_ver}"',
            gtxt,
            count=1,
            flags=re.MULTILINE,
        )
        gradle.write_text(gnew, encoding="utf-8")
        print(f"[OK] {gradle.relative_to(repo)} -> {jb_ver}")

    pxml = repo / "jetbrains-plugin" / "src" / "main" / "resources" / "META-INF" / "plugin.xml"
    xtxt = pxml.read_text(encoding="utf-8")
    xm = re.search(r"<version>([^<]*)</version>", xtxt)
    if not xm:
        print(f"[WARN] {pxml.relative_to(repo)}: no <version> found", file=sys.stderr)
    elif xm.group(1) == jb_ver:
        print(f"[OK] {pxml.relative_to(repo)} already at {jb_ver}")
    else:
        xnew = re.sub(
            r"<version>[^<]*</version>",
            f"<version>{jb_ver}</version>",
            xtxt,
            count=1,
        )
        pxml.write_text(xnew, encoding="utf-8")
        print(f"[OK] {pxml.relative_to(repo)} -> {jb_ver}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
