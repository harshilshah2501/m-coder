"""
Stage-7 deterministic freeze orchestration.

Canonical implementation under stage6.stage6c. Imports compiler primitives;
does not create a parallel root.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure compiler is importable (freeze lives under pipeline; compiler under training)
_TRAINING_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_TRAINING_ROOT) not in sys.path:
    sys.path.insert(0, str(_TRAINING_ROOT))

from stage6.stage6c.reporting.gates import evaluate_gates, normalize_model_id
from stage6.stage6c.reporting.load import load_ledger

CRITICAL_COLLAPSE_CLASSES = frozenset({"T-BYPASS", "T-ALIAS", "T-DOMINANCE-FLIP"})


@dataclass
class RunFreezeResult:
    success: bool
    manifest: dict | None
    freeze_block_reasons: list[str]
    corpus_hash: str | None
    jsonl_path: Path | None
    manifest_path: Path | None


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().lower()


def _stable_row_key(row: dict) -> tuple:
    """Stable sort key for compiled rows (base_id, variant_id, variant_index, phase)."""
    return (
        row.get("base_id", ""),
        row.get("variant_id", ""),
        row.get("ids", {}).get("sample_id", ""),
        row.get("phase", ""),
    )


_STABLE_ROW_KEYS = frozenset({
    "base_id", "variant_id", "phase", "instruction", "response",
    "boundary_phrase", "boundary_hash", "invariants", "ids",
})


def _stable_row(row: dict) -> dict:
    """Copy of row with only deterministic fields; exclude timestamps, paths, etc."""
    out: dict[str, Any] = {}
    for k in _STABLE_ROW_KEYS:
        if k in row:
            v = row[k]
            if k == "ids" and isinstance(v, dict):
                out[k] = dict(v)
            elif isinstance(v, dict):
                out[k] = dict(v)
            elif isinstance(v, list):
                out[k] = list(v)
            else:
                out[k] = v
    # Include source without volatile fields
    src = row.get("source")
    if isinstance(src, dict):
        out["source"] = {
            "doctrine_sha256": src.get("doctrine_sha256"),
            "compiler_version": src.get("compiler_version"),
        }
    return out


def _canonical_json_bytes(obj: Any) -> bytes:
    """Canonical JSON serialization for hashing."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _round_float(v: float | None) -> float | None:
    """Round to 6 decimals for manifest stability."""
    if v is None:
        return None
    return round(float(v), 6)


def _compute_config_hash(config: dict | None) -> str:
    """Deterministic SHA256 of harness config (sorted keys JSON)."""
    if config is None:
        return _sha256_hex(json.dumps({}, sort_keys=True).encode("utf-8"))
    return _sha256_hex(json.dumps(config, sort_keys=True).encode("utf-8"))


def _canonical_non_dummy_rows(rows: list[dict]) -> list[dict]:
    """Filter canonical rows that have non-dummy model_id."""
    from stage6.stage6c.reporting.gates import _canonical_rows

    canon = _canonical_rows(rows)
    return [r for r in canon if normalize_model_id(r.get("model_id")) != "dummy"]


def _has_critical_collapse(rows: list[dict]) -> tuple[bool, str | None]:
    """Check if any row has T-BYPASS, T-ALIAS, or T-DOMINANCE-FLIP."""
    for r in rows:
        labels = r.get("collapse_labels") or []
        for c in CRITICAL_COLLAPSE_CLASSES:
            if c in labels:
                return True, f"collapse_class:{c} present"
    return False, None


def evaluate_freeze_gates(ledger_rows: list[dict]) -> tuple[bool, list[str]]:
    """
    Evaluate Stage-7 freeze gates over ledger rows.
    Returns (pass, freeze_block_reasons). pass is True only if all conditions hold.
    """
    reasons: list[str] = []
    g = evaluate_gates(ledger_rows)

    meta = g.get("meta", {})
    has_model_labels = meta.get("has_model_labels", False)
    non_dummy_count = meta.get("non_dummy_canonical_runs_count", 0)

    if not has_model_labels:
        reasons.append("non-dummy gates not evaluable")
        return False, reasons

    if non_dummy_count == 0:
        reasons.append("non_dummy_canonical_runs_count==0")
        return False, reasons

    tier2_nd = g.get("tier2_non_dummy")
    tier3_nd = g.get("tier3_non_dummy")
    if tier2_nd is None or tier3_nd is None:
        reasons.append("tier2_non_dummy or tier3_non_dummy not evaluable")
        return False, reasons

    tier2 = g.get("tier2", {})
    tier3 = g.get("tier3", {})

    if not tier2.get("pass", False):
        for f in tier2.get("failed", []):
            reasons.append(f"tier2.{f}")
    if not tier3.get("pass", False):
        for f in tier3.get("failed", []):
            reasons.append(f"tier3.{f}")
    if not tier2_nd.get("pass", False):
        for f in tier2_nd.get("failed", []):
            reasons.append(f"tier2_non_dummy.{f}")
    if not tier3_nd.get("pass", False):
        for f in tier3_nd.get("failed", []):
            reasons.append(f"tier3_non_dummy.{f}")

    s3_count = tier2_nd.get("metrics", {}).get("S3_count", 0)
    if s3_count > 0:
        reasons.append("S3_count>0")

    non_dummy_rows = _canonical_non_dummy_rows(ledger_rows)
    has_critical, crit_reason = _has_critical_collapse(non_dummy_rows)
    if has_critical and crit_reason:
        reasons.append(crit_reason)

    return len(reasons) == 0, sorted(reasons)


def _compute_split_hashes(
    train_records: list[dict], val_records: list[dict]
) -> dict[str, str]:
    """Compute SHA256 of canonical JSON per split (deterministic, stable rows only)."""

    def _hash_records(recs: list[dict]) -> str:
        sorted_recs = sorted(recs, key=_stable_row_key)
        stable = [_stable_row(r) for r in sorted_recs]
        return _sha256_hex(_canonical_json_bytes(stable))

    return {
        "train_hash": _hash_records(train_records),
        "val_hash": _hash_records(val_records),
        "test_hash": None,
    }


def _get_source_git_sha() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parent.parent.parent.parent.parent.parent,
            timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()[:40]
    except Exception:
        pass
    return "nogit"


def run_freeze(
    doctrine_path: Path,
    out_dir: Path,
    ledger_path: Path,
    config_path: Path | None = None,
    *,
    split_seed: int = 42,
    force: bool = False,
    dry_run: bool = False,
) -> RunFreezeResult:
    """
    Orchestrate Stage-7 freeze. Fails closed on any invariant violation.
    """
    from compiler.compile_stage7 import compile_doctrine
    from stage08.enforce_split_stage08D import VALID_PHASES, balanced_base_split_phase08D

    schema_path = _TRAINING_ROOT / "compiler" / "dataset_schema.json"
    schema = json.loads(schema_path.read_text())

    # Load ledger
    if not ledger_path.exists():
        return RunFreezeResult(
            success=False,
            manifest=None,
            freeze_block_reasons=["ledger file not found"],
            corpus_hash=None,
            jsonl_path=None,
            manifest_path=None,
        )

    try:
        ledger_rows = load_ledger(ledger_path)
    except Exception as e:
        return RunFreezeResult(
            success=False,
            manifest=None,
            freeze_block_reasons=[f"ledger load failed: {e}"],
            corpus_hash=None,
            jsonl_path=None,
            manifest_path=None,
        )

    # Evaluate freeze gates
    gates_pass, block_reasons = evaluate_freeze_gates(ledger_rows)
    if not gates_pass:
        return RunFreezeResult(
            success=False,
            manifest=None,
            freeze_block_reasons=block_reasons,
            corpus_hash=None,
            jsonl_path=None,
            manifest_path=None,
        )

    # Load config for stage6c_suite_configuration_hash
    config: dict | None = None
    if config_path and config_path.exists():
        try:
            raw = config_path.read_text()
            if config_path.suffix in (".yaml", ".yml"):
                import yaml
                config = yaml.safe_load(raw)
            else:
                config = json.loads(raw)
        except Exception:
            config = None

    suite_config_hash = _compute_config_hash(config)

    # Compile doctrine
    if not doctrine_path.exists():
        return RunFreezeResult(
            success=False,
            manifest=None,
            freeze_block_reasons=["doctrine file not found"],
            corpus_hash=None,
            jsonl_path=None,
            manifest_path=None,
        )

    try:
        rows, doctrine_sha256 = compile_doctrine(
            doctrine_path, "stage7-compiler-v1.0", schema
        )
    except SystemExit:
        return RunFreezeResult(
            success=False,
            manifest=None,
            freeze_block_reasons=["doctrine compile failed"],
            corpus_hash=None,
            jsonl_path=None,
            manifest_path=None,
        )

    # Build corpus hash (deterministic: sort rows, exclude timestamps/paths)
    sorted_rows = sorted(rows, key=_stable_row_key)
    stable_payload = [_stable_row(r) for r in sorted_rows]
    corpus_hash = _sha256_hex(_canonical_json_bytes(stable_payload))

    # Derive bases_count and variants_count from rows (fail closed if non-uniform)
    base_ids = sorted({r["base_id"] for r in rows})
    bases_count = len(base_ids)
    counts_per_base: dict[str, int] = {b: 0 for b in base_ids}
    for r in rows:
        counts_per_base[r["base_id"]] += 1
    unique_counts = sorted(set(counts_per_base.values()))
    if len(unique_counts) != 1:
        return RunFreezeResult(
            success=False,
            manifest=None,
            freeze_block_reasons=[
                "Non-uniform variants per base_id; cannot infer variants_count deterministically."
            ],
            corpus_hash=corpus_hash,
            jsonl_path=None,
            manifest_path=None,
        )
    variants_count = unique_counts[0]

    # Split (deterministic: pass sorted rows so split assignment is stable)
    sorted_rows_for_split = sorted(rows, key=_stable_row_key)
    try:
        train_records, val_records, _, _, _ = balanced_base_split_phase08D(
            sorted_rows_for_split
        )
    except SystemExit:
        return RunFreezeResult(
            success=False,
            manifest=None,
            freeze_block_reasons=["split feasibility failed"],
            corpus_hash=corpus_hash,
            jsonl_path=None,
            manifest_path=None,
        )
    split_hashes = _compute_split_hashes(train_records, val_records)

    # Collapse snapshot with dual scope (canonical vs non_dummy)
    g = evaluate_gates(ledger_rows)
    t2 = g.get("tier2", {})
    t3 = g.get("tier3", {})
    t2_nd = g.get("tier2_non_dummy", {})
    t3_nd = g.get("tier3_non_dummy", {})
    m_canon = t2.get("metrics", {})
    m_nd = t2_nd.get("metrics", {})
    collapse_rate_snapshot = {
        "canonical": {
            "tier2_pass": t2.get("pass", False),
            "tier3_pass": t3.get("pass", False),
            "fail_rate_ge_S2": _round_float(m_canon.get("fail_rate_ge_S2")),
            "S3_count": m_canon.get("S3_count", 0),
            "BDA_norm_p95": _round_float(m_canon.get("BDA_norm_p95")),
        },
        "non_dummy": {
            "tier2_pass": t2_nd.get("pass", False),
            "tier3_pass": t3_nd.get("pass", False),
            "fail_rate_ge_S2": _round_float(m_nd.get("fail_rate_ge_S2")),
            "S3_count": m_nd.get("S3_count", 0),
            "BDA_norm_p95": _round_float(m_nd.get("BDA_norm_p95")),
        },
    }

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    ledger_sha = _sha256_hex(ledger_path.read_bytes())

    manifest = OrderedDict([
        ("schema_version", "stage7-freeze-manifest.v1"),
        ("source_git_sha", _get_source_git_sha()),
        ("corpus_hash", corpus_hash),
        ("bases_count", bases_count),
        ("variants_count", variants_count),
        ("total_rows", len(rows)),
        ("phase_distribution", dict(
            (p, sum(1 for r in rows if r.get("phase") == p))
            for p in VALID_PHASES
        )),
        ("stage6c_suite_configuration_hash", suite_config_hash),
        ("collapse_rate_snapshot", collapse_rate_snapshot),
        ("mutation_taxonomy_version", "STAGE6C_MUTATION_TAXONOMY_v1"),
        ("adapter_param_signature_snapshot", None),
        ("generated_at_utc", generated_at),
        ("stage6c_pass_reference", {
            "pass": True,
            "ledger_path": str(ledger_path),
            "ledger_sha256": ledger_sha,
        }),
        ("freeze_block_reason", []),
        ("split_hashes", split_hashes),
    ])

    if dry_run:
        return RunFreezeResult(
            success=True,
            manifest=dict(manifest),
            freeze_block_reasons=[],
            corpus_hash=corpus_hash,
            jsonl_path=None,
            manifest_path=None,
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "golden_exemplars_v1.jsonl"
    manifest_path = out_dir / "stage7_freeze_manifest.json"

    if (jsonl_path.exists() or manifest_path.exists()) and not force:
        return RunFreezeResult(
            success=False,
            manifest=None,
            freeze_block_reasons=["outputs exist; use --force to overwrite"],
            corpus_hash=corpus_hash,
            jsonl_path=jsonl_path,
            manifest_path=manifest_path,
        )

    with jsonl_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return RunFreezeResult(
        success=True,
        manifest=dict(manifest),
        freeze_block_reasons=[],
        corpus_hash=corpus_hash,
        jsonl_path=jsonl_path,
        manifest_path=manifest_path,
    )
