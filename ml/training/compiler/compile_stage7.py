#!/usr/bin/env python3
"""
Stage-7 Deterministic Compiler — Governance → JSONL

Parses STAGE4_VARIANT_GENERATION.md per COMPILER_PARSING_CONTRACT_v1.0.
Abort-only on any contract violation. No LLM calls, no heuristics.
"""
from __future__ import annotations

import argparse
from typing import List, Tuple
import hashlib
import json
import re
import sys
import unicodedata
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent  # compiler -> training -> ml -> repo
DEFAULT_DOCTRINE = SCRIPT_DIR.parent / "pipeline" / "STAGE4_VARIANT_GENERATION.md"
DEFAULT_OUT_DIR = SCRIPT_DIR.parent / "generated"
DEFAULT_SCHEMA = SCRIPT_DIR / "dataset_schema.json"
DEFAULT_MANIFEST_SCHEMA = SCRIPT_DIR / "manifest_schema.json"
VALID_PHASES = {"REF", "CONF", "DES", "MIX", "CODE"}

BASE_HEADER_RE = re.compile(r"^##\s+BASE-(\d{3})\s+Variants:.*$")
VARIANT_HEADER_RE = re.compile(r"^###\s+BASE-(\d{3})-V([1-4])\s*$")

SECTION_LABELS = [
    "**Boundary Phrase:**",
    "**Phase:**",
    "**Context:**",
    "**Response Posture:**",
    "**Allow:**",
    "**Block at boundary:**",
    "**Validation:**",
]


def _abort(msg: str) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().lower()


def _normalize_section_text(text: str) -> str:
    """Strip leading/trailing blank lines, trim trailing spaces, uniform deindent."""
    lines = text.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    lines = [ln.rstrip() for ln in lines]
    if not lines:
        return ""
    non_empty = [ln for ln in lines if ln.strip()]
    if not non_empty:
        return ""
    min_indent = min(len(ln) - len(ln.lstrip()) for ln in non_empty)
    if min_indent > 0 and all(ln.startswith(" " * min_indent) for ln in non_empty):
        lines = [ln[min_indent:] if len(ln) >= min_indent else ln for ln in lines]
    return "\n".join(lines)


def _boundary_hash_normalize(s: str) -> str:
    """NFC, collapse internal whitespace for hashing."""
    n = unicodedata.normalize("NFC", s)
    return " ".join(n.split())


def _compute_boundary_hash(display_form: str) -> str:
    normalized = _boundary_hash_normalize(display_form)
    return _sha256_hex(normalized.encode("utf-8"))


def _extract_invariants(response_posture_text: str) -> list[str]:
    """Extract invariant lines from Response Posture section. Abort if none."""
    invariants = []
    for line in response_posture_text.split("\n"):
        stripped = line.strip()
        lower = stripped.lower()
        if not (
            lower.startswith("invariant:") or
            lower.startswith("- invariant:") or
            lower.startswith("* invariant:")
        ):
            continue
        parts = stripped.split(":", 1)
        if len(parts) < 2:
            continue
        value = parts[1].strip()
        if not value:
            _abort("Empty invariant value")
        invariants.append(value)
    seen = set()
    deduped = []
    for inv in invariants:
        if inv not in seen:
            seen.add(inv)
            deduped.append(inv)
    if not deduped:
        print("---- No invariants found in Response Posture ----")
        print(response_posture_text)
        print("------------------------------------------------")
        _abort("No invariants found in Response Posture")    
    return deduped


def _parse_variant_sections(variant_text: str) -> dict[str, str]:
    """Extract sections by label. Enforce presence, uniqueness; no order requirement."""
    sections: dict[str, str] = {}
    lines = variant_text.split("\n")
    label_to_pos: List[Tuple[int, str]] = []
    required_set = set(SECTION_LABELS)
    seen_labels: set[str] = set()
    for i, line in enumerate(lines):
        stripped = line.strip()
        normalized = stripped.lower()
        for label in SECTION_LABELS:
            if normalized.startswith(label.lower()):
                if label in seen_labels:
                    _abort("Duplicate section labels")
                seen_labels.add(label)
                label_to_pos.append((i, label))
                break
    found_set = {lbl for _, lbl in label_to_pos}
    for lbl in found_set:
        if lbl not in required_set:
            _abort(f"Unknown section label: {lbl}")
    if found_set != required_set:
        missing = required_set - found_set
        if missing:
            _abort(f"Missing section: {next(iter(missing))}")
    label_to_pos.sort(key=lambda x: x[0])
    for idx, (line_idx, label) in enumerate(label_to_pos):
        label_line = lines[line_idx].strip()
        rest_of_label_line = label_line[len(label):].strip() if label_line.lower().startswith(label.lower()) else label_line
        content_start = line_idx + 1
        content_end = label_to_pos[idx + 1][0] if idx + 1 < len(label_to_pos) else len(lines)
        following = "\n".join(lines[content_start:content_end])
        content = (rest_of_label_line + "\n" + following) if rest_of_label_line else following
        normalized = _normalize_section_text(content)
        if not normalized.strip():
            _abort(f"Empty section content for {label}")
        sections[label] = normalized
    return sections


def _build_synthetic_doctrine() -> str:
    """Generate 25 bases × 4 variants with minimal valid content."""
    phases_cycle = ["REF", "CONF", "DES", "MIX", "CODE"]
    lines = []
    for b in range(1, 26):
        base_id = f"BASE-{b:03d}"
        phase = phases_cycle[(b - 1) % 5]
        lines.append(f"## {base_id} Variants: Selftest")
        lines.append("")
        for v in range(1, 5):
            variant_id = f"V{v}"
            lines.append(f"### {base_id}-{variant_id}")
            lines.append("")
            lines.append("**Boundary Phrase:**")
            lines.append(f"boundary_{base_id}_{variant_id}()")
            lines.append("")
            lines.append("**Phase:**")
            lines.append(phase)
            lines.append("")
            lines.append("**Context:**")
            lines.append(f"Context for {base_id} {variant_id}.")
            lines.append("")
            lines.append("**Response Posture:**")
            lines.append("ALLOW up to boundary.")
            lines.append(f"- INVARIANT: block at {base_id}.")
            lines.append("")
            lines.append("**Allow:**")
            lines.append("- Pre-boundary checks")
            lines.append("")
            lines.append("**Block at boundary:**")
            lines.append("- boundary call")
            lines.append("")
            lines.append("**Validation:**")
            lines.append("- PASS")
            lines.append("")
            lines.append("---")
            lines.append("")
    return "\n".join(lines)


def _parse_doctrine(text: str) -> List[Tuple[str, str, str]]:
    """Parse doctrine text. Returns list of (base_id, variant_id, variant_content)."""
    lines = text.split("\n")
    bases_found: List[Tuple[str, int, int]] = []
    variants_found: List[Tuple[str, str, int, int]] = []
    i = 0
    current_base = None
    current_base_start = None
    while i < len(lines):
        m_base = BASE_HEADER_RE.match(lines[i])
        if m_base:
            bid = f"BASE-{m_base.group(1)}"
            num = int(m_base.group(1))
            if num < 1 or num > 25:
                _abort(f"Base outside BASE-001..BASE-025: {bid}")
            current_base = bid
            current_base_start = i
            j = i + 1
            while j < len(lines) and not BASE_HEADER_RE.match(lines[j]):
                j += 1
            bases_found.append((bid, current_base_start, j))
            i += 1
            continue
        m_var = VARIANT_HEADER_RE.match(lines[i])
        if m_var:
            vbid = f"BASE-{m_var.group(1)}"
            vid = f"V{m_var.group(2)}"
            if current_base and vbid != current_base:
                _abort(f"Variant base {vbid} does not match enclosing base {current_base}")
            start = i
            j = i + 1
            while j < len(lines) and not VARIANT_HEADER_RE.match(lines[j]) and not BASE_HEADER_RE.match(lines[j]):
                j += 1
            variants_found.append((vbid, vid, start, j))
            i = j
            continue
        i += 1
    if len(bases_found) != 25:
        _abort(f"Expected 25 bases, found {len(bases_found)}")
    seen_bases = set()
    for bid, _, _ in bases_found:
        if bid in seen_bases:
            _abort(f"Duplicate base: {bid}")
        seen_bases.add(bid)
    result: List[Tuple[str, str, str]] = []
    for bid, base_start, base_end in bases_found:
        base_variants = [(vb, vid, s, e) for vb, vid, s, e in variants_found if vb == bid and base_start <= s < base_end]
        if len(base_variants) != 4:
            _abort(f"Base {bid} must have exactly 4 variants, found {len(base_variants)}")
        seen_v = set()
        for vb, vid, s, e in base_variants:
            if vid in seen_v:
                _abort(f"Duplicate variant {vid} in base {bid}")
            seen_v.add(vid)
        for vb, vid, s, e in sorted(base_variants, key=lambda x: int(x[1][1])):
            content = "\n".join(lines[s:e])
            result.append((bid, vid, content))
    return result


def _emit_row(
    base_id: str,
    variant_id: str,
    sections: dict[str, str],
    doctrine_file: str,
    doctrine_sha256: str,
    compiler_version: str,
    compiled_at_utc: str,
) -> OrderedDict:
    phase_raw = sections.get("**Phase:**", "").strip().upper()
    if phase_raw not in VALID_PHASES:
        _abort(f"Invalid phase: {phase_raw}")
    boundary_display = sections.get("**Boundary Phrase:**", "").strip()
    if len(boundary_display) < 3:
        _abort("boundary_phrase length < 3 after trim")
    invariants = _extract_invariants(sections.get("**Response Posture:**", ""))
    boundary_hash = _compute_boundary_hash(boundary_display)
    row = OrderedDict()
    row["base_id"] = base_id
    row["variant_id"] = variant_id
    row["phase"] = phase_raw
    row["instruction"] = _normalize_section_text(sections.get("**Context:**", ""))
    row["response"] = OrderedDict([
        ("posture", _normalize_section_text(sections.get("**Response Posture:**", ""))),
        ("allow", _normalize_section_text(sections.get("**Allow:**", ""))),
        ("block", _normalize_section_text(sections.get("**Block at boundary:**", ""))),
        ("validation", _normalize_section_text(sections.get("**Validation:**", ""))),
    ])
    row["boundary_phrase"] = boundary_display
    row["boundary_hash"] = boundary_hash
    row["invariants"] = invariants
    row["ids"] = OrderedDict([
        ("sample_id", f"{base_id}-{variant_id}"),
        ("phase_id", phase_raw),
    ])
    row["source"] = OrderedDict([
        ("doctrine_file", doctrine_file),
        ("doctrine_sha256", doctrine_sha256),
        ("compiler_version", compiler_version),
        ("compiled_at_utc", compiled_at_utc),
    ])
    return row


def _validate_row(row: dict, schema: dict) -> None:
    try:
        import jsonschema
        jsonschema.validate(row, schema)
    except ImportError:
        _abort("jsonschema not installed. Run: pip install jsonschema")
    except Exception as e:
        _abort(f"Row schema validation failed: {e}")


def _validate_manifest(manifest: dict, schema: dict) -> None:
    try:
        import jsonschema
        jsonschema.validate(manifest, schema)
    except ImportError:
        _abort("jsonschema not installed. Run: pip install jsonschema")
    except Exception as e:
        _abort(f"Manifest schema validation failed: {e}")


def compile_doctrine(
    doctrine_path: Path,
    compiler_version: str,
    schema: dict,
) -> tuple[list[OrderedDict], str]:
    """Parse doctrine, return (rows, doctrine_sha256)."""
    raw = doctrine_path.read_bytes()
    doctrine_sha256 = _sha256_hex(raw)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        _abort(f"Invalid UTF-8: {e}")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    parsed = _parse_doctrine(text)
    compiled_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    doctrine_file_str = str(doctrine_path)
    rows = []
    for base_id, variant_id, variant_content in parsed:
        sections = _parse_variant_sections(variant_content)
        row = _emit_row(
            base_id, variant_id, sections,
            doctrine_file_str, doctrine_sha256, compiler_version, compiled_at,
        )
        _validate_row(dict(row), schema)
        rows.append(row)
    return rows, doctrine_sha256


def run_selftest(
    compiler_version: str,
    schema: dict,
    manifest_schema: dict,
) -> bool:
    """Run synthetic doctrine through compiler. Returns True on success."""
    synthetic = _build_synthetic_doctrine()
    with __import__("tempfile").NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(synthetic)
        path = Path(f.name)
    try:
        rows, doctrine_sha256 = compile_doctrine(path, compiler_version, schema)
        if len(rows) != 100:
            _abort(f"Selftest expected 100 rows, got {len(rows)}")
        return True
    finally:
        path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage-7 Deterministic Compiler")
    parser.add_argument("--doctrine", type=Path, default=None, help="Override doctrine path")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="Dataset JSON Schema path")
    parser.add_argument("--manifest-schema", type=Path, default=DEFAULT_MANIFEST_SCHEMA, help="Manifest JSON Schema path")
    parser.add_argument("--version", default="stage7-compiler-v1.0", help="Compiler version string")
    parser.add_argument("--dry-run", action="store_true", help="Parse and validate only, no outputs")
    parser.add_argument("--selftest", action="store_true", help="Run synthetic selftest")
    parser.add_argument("--force", action="store_true", help="Overwrite existing outputs")
    args = parser.parse_args()

    doctrine_path = args.doctrine if args.doctrine is not None else DEFAULT_DOCTRINE

    def _repo_relative(p: Path) -> str:
        try:
            return str(p.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")
        except ValueError:
            return str(p)

    if args.selftest:
        schema = json.loads(args.schema.read_text())
        manifest_schema = json.loads(args.manifest_schema.read_text())
        run_selftest(args.version, schema, manifest_schema)
        print("Selftest PASSED")
        return

    if not doctrine_path.exists():
        _abort(f"Doctrine file not found: {doctrine_path}")

    schema = json.loads(args.schema.read_text())
    manifest_schema = json.loads(args.manifest_schema.read_text())

    rows, doctrine_sha256 = compile_doctrine(doctrine_path, args.version, schema)

    if args.dry_run:
        print(f"Dry run: parsed {len(rows)} rows from {doctrine_path}")
        return

    args.out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = args.out_dir / "golden_exemplars_v1.jsonl"
    manifest_path = args.out_dir / "dataset_manifest.json"
    if (jsonl_path.exists() or manifest_path.exists()) and not args.force:
        _abort(
            f"Outputs already exist in {args.out_dir}. Use --force to overwrite."
        )

    with open(jsonl_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    rows_per_phase = {"REF": 0, "CONF": 0, "DES": 0, "MIX": 0, "CODE": 0}
    bases_per_phase: dict[str, set[str]] = {p: set() for p in rows_per_phase}
    for row in rows:
        p = row["phase"]
        rows_per_phase[p] = rows_per_phase.get(p, 0) + 1
        bases_per_phase[p].add(row["base_id"])
    bases_per_phase_counts = {p: len(bases_per_phase[p]) for p in rows_per_phase}

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    manifest = OrderedDict([
        ("dataset_version", "v1"),
        ("compiler_version", args.version),
        ("doctrine_file", _repo_relative(doctrine_path)),
        ("doctrine_sha256", doctrine_sha256),
        ("generated_at_utc", generated_at),
        ("total_bases", 25),
        ("total_rows", len(rows)),
        ("rows_per_phase", rows_per_phase),
        ("bases_per_phase", bases_per_phase_counts),
        ("output_files", OrderedDict([
            ("golden_exemplars_jsonl", "golden_exemplars_v1.jsonl"),
            ("manifest_json", "dataset_manifest.json"),
        ])),
    ])
    _validate_manifest(dict(manifest), manifest_schema)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Wrote {jsonl_path}")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
