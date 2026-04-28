"""Detect shadow / dual mcoder-suite installs (Motadata venv vs m-coder repo PYTHONPATH)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _pip_show_field(executable: str, package: str, field_prefix: str) -> str | None:
    try:
        r = subprocess.run(
            [executable, "-m", "pip", "show", package],
            capture_output=True,
            text=True,
            timeout=45,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    for line in r.stdout.splitlines():
        if line.startswith(field_prefix):
            return line.split(":", 1)[1].strip()
    return None


def _site_packages(prefix: Path) -> Path | None:
    """Best-effort lib/pythonX.Y/site-packages for this interpreter."""
    ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    sp = prefix / "lib" / f"python{ver}" / "site-packages"
    if sp.is_dir():
        return sp
    return None


def _egg_links_pointing_at_repo(site_packages: Path) -> list[str]:
    out: list[str] = []
    if not site_packages.is_dir():
        return out
    for p in site_packages.glob("*.egg-link"):
        try:
            first = p.read_text(encoding="utf-8").strip().splitlines()[0]
        except OSError:
            continue
        low = first.lower()
        if "m-coder" in first or "mcoder" in low:
            out.append(f"{p.name} → {first}")
    return out


def _authority_registry_exists(site_packages: Path) -> bool:
    reg = site_packages / "runtime" / "layer5" / "authority" / "product_authority_registry.yaml"
    return reg.is_file()


def build_venv_report(executable: str | None = None) -> list[str]:
    """Human-readable lines for doctor / bootstrap (warnings only when needed)."""
    exe = executable or sys.executable
    lines: list[str] = []
    prefix = Path(sys.prefix).resolve()

    lines.append(f"Interpreter: {exe}")
    lines.append(f"venv prefix:   {prefix}")

    loc_s = _pip_show_field(exe, "mcoder-suite", "Location:")
    if not loc_s:
        lines.append("mcoder-suite:  not installed (pip show failed — install the wheel into this venv)")
        return lines

    loc = Path(loc_s).resolve()
    lines.append(f"pip Location:  {loc}")

    try:
        ok_under = loc.is_relative_to(prefix)
    except AttributeError:
        ok_under = str(loc).startswith(str(prefix))

    if not ok_under:
        lines.append(
            "WARN: mcoder-suite files are registered outside this venv prefix — imports may "
            "resolve from the wrong tree (dual install)."
        )
        lines.append(
            "Fix: unset PYTHONPATH; remove editable/egg-link installs of mcoder-suite from other trees; "
            "then: pip uninstall mcoder-suite -y && pip install /path/to/mcoder_suite-*.whl"
        )
    else:
        lines.append("mcoder-suite:  OK (under active venv prefix)")

    pp = (os.environ.get("PYTHONPATH") or "").strip()
    if pp:
        lines.append(f"WARN: PYTHONPATH={pp} — can shadow site-packages; unset for wheel-only Motadata workflows.")

    sp = _site_packages(prefix)
    if sp:
        if not _authority_registry_exists(sp):
            lines.append(
                "ERROR: missing runtime/layer5/authority/product_authority_registry.yaml in this venv install."
            )
            lines.append(
                "Fix: rebuild/reinstall wheel that includes runtime.layer5.authority package-data."
            )
        egg = _egg_links_pointing_at_repo(sp)
        if egg:
            lines.append("WARN: egg-link(s) referencing a dev checkout:")
            for e in egg:
                lines.append(f"       {e}")
            lines.append("Fix: pip uninstall mcoder-suite -y && rm obsolete *.egg-link if pip leaves them")

    return lines


def print_venv_report(executable: str | None = None, *, heading: str = "Wheel / venv hygiene") -> None:
    print(heading)
    for ln in build_venv_report(executable):
        print(f"  {ln}")
