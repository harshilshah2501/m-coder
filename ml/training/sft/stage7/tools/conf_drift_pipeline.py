from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class DriftCluster:
    count: int
    horizon_N: int
    shape: str
    carryover_mode: str
    injection_profile: str


def _stage7_dir() -> Path:
    """Resolve ml/training/sft/stage7/ from this file location."""
    # This file lives at ml/training/sft/stage7/tools/conf_drift_pipeline.py
    tools_dir = Path(__file__).resolve().parent
    stage7 = tools_dir.parent
    return stage7


def _stage8_dataset_dir() -> Path:
    """Resolve ml/training/pipeline/stage08/dataset/."""
    stage7 = _stage7_dir()
    ml_dir = stage7.parents[2]  # .../ml
    return ml_dir / "training" / "pipeline" / "stage08" / "dataset"


def _stage8_cert_path() -> Path:
    """Resolve Stage-8 patch certificate path."""
    stage7 = _stage7_dir()
    ml_dir = stage7.parents[2]
    return ml_dir / "training" / "pipeline" / "stage08" / "FREEZE_CERTIFICATE_STAGE8_CONF_PATCH1.json"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def cmd_list_run_ids(_args: argparse.Namespace) -> int:
    stage7 = _stage7_dir()
    drift_path = stage7 / "conf_to_des_drift.jsonl"
    out_path = stage7 / "conf_to_des_run_ids.txt"

    if not drift_path.exists():
        raise SystemExit(f"conf_to_des_drift.jsonl not found at {drift_path}")

    run_ids = set()
    with drift_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            rid = obj.get("run_id")
            if rid:
                run_ids.add(str(rid))

    sorted_ids = sorted(run_ids)
    out_path.write_text("\n".join(sorted_ids) + ("\n" if sorted_ids else ""), encoding="utf-8")

    print(f"[list-run-ids] wrote {len(sorted_ids)} unique run_ids to {out_path}")
    print("Verification:")
    print(f"  wc -l {out_path}")
    return 0


def cmd_extract_traces(_args: argparse.Namespace) -> int:
    stage7 = _stage7_dir()
    drift_ids_path = stage7 / "conf_to_des_run_ids.txt"
    traces_path = stage7 / "suite_traces.jsonl"
    out_traces = stage7 / "conf_to_des_traces.jsonl"
    missing_path = stage7 / "missing_run_ids.txt"

    if not drift_ids_path.exists():
        raise SystemExit(f"run-id list not found: {drift_ids_path} (run list-run-ids first)")
    if not traces_path.exists():
        raise SystemExit(f"suite_traces.jsonl not found at {traces_path}")

    run_ids = {line.strip() for line in drift_ids_path.read_text(encoding="utf-8").splitlines() if line.strip()}
    if not run_ids:
        raise SystemExit("No run_ids loaded from conf_to_des_run_ids.txt")

    found: Dict[str, bool] = {rid: False for rid in run_ids}
    kept = 0
    with traces_path.open("r", encoding="utf-8") as fin, out_traces.open("w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            spec = obj.get("spec") or {}
            # Tolerate run_id either at top-level or under spec
            rid = obj.get("run_id") or spec.get("run_id")
            if rid in run_ids:
                fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
                kept += 1
                found[str(rid)] = True

    missing = [rid for rid, seen in found.items() if not seen]
    if missing:
        missing_path.write_text("\n".join(sorted(missing)) + "\n", encoding="utf-8")
        print(f"[extract-traces] WARNING: {len(missing)} run_ids had no trace; listed in {missing_path}")
    else:
        if missing_path.exists():
            missing_path.unlink()
        print("[extract-traces] all drift run_ids matched a trace; no missing_run_ids.txt written")

    print(f"[extract-traces] wrote {kept} traces to {out_traces}")
    print("Verification:")
    print(f"  wc -l {out_traces}")
    if missing:
        print(f"  wc -l {missing_path}")
    return 0


def _iter_drift_rows(drift_path: Path) -> Iterable[Dict]:
    with drift_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def cmd_cluster(_args: argparse.Namespace) -> int:
    stage7 = _stage7_dir()
    drift_path = stage7 / "conf_to_des_drift.jsonl"
    out_path = stage7 / "conf_drift_clusters.tsv"

    if not drift_path.exists():
        raise SystemExit(f"conf_to_des_drift.jsonl not found at {drift_path}")

    counts: Dict[Tuple[int, str, str, str], int] = {}
    for row in _iter_drift_rows(drift_path):
        combo = row.get("combo") or {}
        h = int(combo.get("horizon_N", 0))
        shape = str(combo.get("shape", "")).strip()
        carry = str(combo.get("carryover_mode", "")).strip()
        inj = str(combo.get("injection_profile", "")).strip()
        key = (h, shape, carry, inj)
        counts[key] = counts.get(key, 0) + 1

    clusters: List[DriftCluster] = [
        DriftCluster(count=c, horizon_N=k[0], shape=k[1], carryover_mode=k[2], injection_profile=k[3])
        for k, c in counts.items()
    ]
    clusters.sort(key=lambda cl: (-cl.count, cl.horizon_N, cl.shape, cl.carryover_mode, cl.injection_profile))

    lines = ["count\thorizon_N\tshape\tcarryover_mode\tinjection_profile"]
    for cl in clusters:
        lines.append(
            f"{cl.count}\t{cl.horizon_N}\t{cl.shape}\t{cl.carryover_mode}\t{cl.injection_profile}"
        )
    out_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    print(f"[cluster] wrote {len(clusters)} clusters to {out_path}")
    print("Verification:")
    print(f"  column -t {out_path} | head")
    return 0


def cmd_build_review_candidates(_args: argparse.Namespace) -> int:
    stage7 = _stage7_dir()
    traces_path = stage7 / "conf_to_des_traces.jsonl"
    out_path = stage7 / "conf_drift_candidates_for_review.jsonl"

    if not traces_path.exists():
        raise SystemExit(f"conf_to_des_traces.jsonl not found at {traces_path} (run extract-traces first)")

    origins_keep = {"governance", "seed", "step_query", "carryover"}
    written = 0

    with traces_path.open("r", encoding="utf-8") as fin, out_path.open("w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            spec = obj.get("spec") or {}
            steps = obj.get("steps") or []
            if not steps:
                continue
            last = steps[-1]
            messages = last.get("prompt_messages") or []

            prompt_parts: List[str] = []
            for m in messages:
                role = str(m.get("role", "")).strip()
                origin_raw = m.get("origin", "")
                origin = str(origin_raw).strip() if origin_raw is not None else ""
                if origin:
                    # Keep only selected origins when present
                    if origin not in origins_keep:
                        continue
                else:
                    # If origin is missing, keep if role is system/user and label origin as unknown
                    if role not in {"system", "user"}:
                        continue
                    origin = "unknown"
                content = str(m.get("content", "")).strip()
                # Deterministic role/origin separator, preserve ordering
                prompt_parts.append(f"[{role}/{origin}] {content}")

            prompt_text = "\n".join(prompt_parts)
            # Cap extremely large prompts to keep review manageable
            max_chars = 20000
            if len(prompt_text) > max_chars:
                prompt_text = prompt_text[:max_chars] + "\n[TRUNCATED]"

            response = last.get("response") or {}
            model_text = str(response.get("content", "")).strip()

            cluster_id = "|".join(
                [
                    str(spec.get("horizon_N")),
                    str(spec.get("shape")),
                    str(spec.get("carryover_mode")),
                    str(spec.get("injection_profile_id")),
                ]
            )

            rec = {
                "run_id": spec.get("run_id"),
                "seed_id": spec.get("seed_id"),
                "horizon_N": spec.get("horizon_N"),
                "shape": spec.get("shape"),
                "carryover_mode": spec.get("carryover_mode"),
                "injection_profile_id": spec.get("injection_profile_id"),
                "cluster_id": cluster_id,
                "prompt_text": prompt_text,
                "model_text": model_text,
                "expected_phase": "CONF",
                "observed_phase": "DES",
            }
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1

    print(f"[build-review-candidates] wrote {written} records to {out_path}")
    print("Verification:")
    print(f"  wc -l {out_path}")
    print(f"  head -n 1 {out_path}")
    return 0


def cmd_build_corrections_from_reviewed(_args: argparse.Namespace) -> int:
    stage7 = _stage7_dir()
    reviewed_path = stage7 / "conf_drift_candidates_reviewed.jsonl"
    out_path = stage7 / "conf_drift_corrections.jsonl"

    if not reviewed_path.exists():
        # Create empty stub and print instructions
        reviewed_path.write_text("", encoding="utf-8")
        print(f"[build-corrections-from-reviewed] created empty stub {reviewed_path}")
        print("Populate it by copying lines from conf_drift_candidates_for_review.jsonl")
        print("and adding a `correction` object with posture/allow/block/validation fields per record.")
        return 0

    written = 0
    with reviewed_path.open("r", encoding="utf-8") as fin, out_path.open("w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            corr = obj.get("correction") or {}
            posture = str(corr.get("posture", "")).strip()
            allow = str(corr.get("allow", "")).strip()
            block = str(corr.get("block", "")).strip()
            validation = str(corr.get("validation", "")).strip()
            if not (posture and allow and block and validation):
                continue

            record = {
                "base_id": obj.get("seed_id"),
                "variant_id": obj.get("run_id"),
                "phase": "CONF",
                "instruction": obj.get("prompt_text", ""),
                "response": {
                    "posture": posture,
                    "allow": allow,
                    "block": block,
                    "validation": validation,
                },
            }
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1

    print(f"[build-corrections-from-reviewed] wrote {written} correction exemplars to {out_path}")
    print("Verification:")
    print(f"  wc -l {out_path}")
    print(f"  head -n 1 {out_path}")
    return 0


def cmd_merge_dataset(_args: argparse.Namespace) -> int:
    stage7 = _stage7_dir()
    stage8_ds_dir = _stage8_dataset_dir()
    stage8_ds_dir.mkdir(parents=True, exist_ok=True)

    src_main = stage7 / "golden_exemplars_v1.jsonl"
    src_corr = stage7 / "conf_drift_corrections.jsonl"
    dest = stage8_ds_dir / "golden_exemplars_v1_conf_patch1.jsonl"

    if not src_main.exists():
        raise SystemExit(f"golden_exemplars_v1.jsonl not found at {src_main}")

    main_lines = src_main.read_text(encoding="utf-8").splitlines()
    corrections_lines: List[str] = []
    if src_corr.exists():
        corrections_lines = [ln for ln in src_corr.read_text(encoding="utf-8").splitlines() if ln.strip()]

    with dest.open("w", encoding="utf-8") as f:
        for ln in main_lines:
            if ln.strip():
                f.write(ln.rstrip("\n") + "\n")
        for ln in corrections_lines:
            f.write(ln.rstrip("\n") + "\n")

    print(
        f"[merge-dataset] wrote {len(main_lines) + len(corrections_lines)} rows "
        f"to {dest} (base={len(main_lines)}, corrections={len(corrections_lines)})"
    )
    if not corrections_lines:
        print("[merge-dataset] WARNING: corrections file empty or missing; merged dataset is identical to base.")

    # Basic schema sanity check: ensure at least one line parses to a known schema
    first_obj = None
    for ln in main_lines:
        ln = ln.strip()
        if not ln:
            continue
        first_obj = json.loads(ln)
        break
    if first_obj is None:
        raise SystemExit("[merge-dataset] FATAL: base dataset contains no usable records")

    has_stage7 = (
        isinstance(first_obj.get("instruction"), str)
        and isinstance(first_obj.get("response"), dict)
        and isinstance(first_obj.get("phase"), str)
    )
    has_legacy = (
        isinstance(first_obj.get("input"), str)
        and isinstance(first_obj.get("output"), str)
        and isinstance(first_obj.get("phase"), str)
    )
    if not (has_stage7 or has_legacy):
        raise SystemExit(
            "[merge-dataset] FATAL: merged dataset does not match expected Stage-7 or legacy schema; "
            "inspect golden_exemplars_v1.jsonl and conf_drift_corrections.jsonl."
        )

    print("Verification:")
    print(f"  wc -l {dest}")
    return 0


def cmd_update_stage8_certificate(_args: argparse.Namespace) -> int:
    stage8_ds_dir = _stage8_dataset_dir()
    dataset_path = stage8_ds_dir / "golden_exemplars_v1_conf_patch1.jsonl"
    cert_path = _stage8_cert_path()

    if not dataset_path.exists():
        raise SystemExit(f"merged dataset not found at {dataset_path} (run merge-dataset first)")

    rel_dataset = "ml/training/pipeline/stage08/dataset/golden_exemplars_v1_conf_patch1.jsonl"
    sha = _sha256_file(dataset_path)

    if cert_path.exists():
        doc = json.loads(cert_path.read_text(encoding="utf-8"))
    else:
        doc = {}

    doc["frozen_dataset_path"] = rel_dataset
    doc["dataset_sha256"] = sha

    cert_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_text(json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[update-stage8-certificate] updated {cert_path}")
    print("Verification:")
    print(f"  cat {cert_path}")
    return 0


def cmd_write_audit_report(_args: argparse.Namespace) -> int:
    stage7 = _stage7_dir()
    stage8_ds_dir = _stage8_dataset_dir()

    golden = stage7 / "golden_exemplars_v1.jsonl"
    drift = stage7 / "conf_to_des_drift.jsonl"
    corrections = stage7 / "conf_drift_corrections.jsonl"
    merged = stage8_ds_dir / "golden_exemplars_v1_conf_patch1.jsonl"
    clusters = stage7 / "conf_drift_clusters.tsv"
    run_ids = stage7 / "conf_to_des_run_ids.txt"
    traces = stage7 / "conf_to_des_traces.jsonl"

    def sha_or_na(p: Path) -> str:
        return _sha256_file(p) if p.exists() else "N/A"

    golden_sha = sha_or_na(golden)
    drift_sha = sha_or_na(drift)
    corrections_sha = sha_or_na(corrections)
    merged_sha = sha_or_na(merged)

    def line_count(p: Path) -> int:
        if not p.exists():
            return 0
        return sum(1 for _ in p.open("r", encoding="utf-8"))

    run_id_count = line_count(run_ids)
    trace_count = line_count(traces)
    cluster_count = max(line_count(clusters) - 1, 0) if clusters.exists() else 0

    report_path = stage7 / "CONF_DES_DRIFT_AUDIT_v1.md"
    lines: List[str] = []
    lines.append("# CONF→DES Drift Audit — Stage-7/Stage-8 Patch1")
    lines.append("")
    lines.append("## 1. Inputs")
    lines.append("")
    lines.append("- Original Stage-7 bundle: `ml/training/sft/stage7/`")
    lines.append("- Original drift file: `ml/training/sft/stage7/conf_to_des_drift.jsonl`")
    lines.append("- Corrections file: `ml/training/sft/stage7/conf_drift_corrections.jsonl`")
    lines.append("- Patched Stage-8 dataset: `ml/training/pipeline/stage08/dataset/golden_exemplars_v1_conf_patch1.jsonl`")
    lines.append("- Stage-8 patch certificate: `ml/training/pipeline/stage08/FREEZE_CERTIFICATE_STAGE8_CONF_PATCH1.json`")
    lines.append("")
    lines.append("## 2. Hashes")
    lines.append("")
    lines.append(f"- `golden_exemplars_v1.jsonl` SHA256: `{golden_sha}`")
    lines.append(f"- `conf_to_des_drift.jsonl` SHA256: `{drift_sha}`")
    lines.append(f"- `conf_drift_corrections.jsonl` SHA256: `{corrections_sha}`")
    lines.append(f"- `golden_exemplars_v1_conf_patch1.jsonl` SHA256: `{merged_sha}`")
    lines.append("")
    lines.append("## 3. Drift Metrics")
    lines.append("")
    lines.append(f"- Drift run_ids (unique): `{run_id_count}`  (from `conf_to_des_run_ids.txt`)")
    lines.append(f"- Drift traces extracted: `{trace_count}`  (from `conf_to_des_traces.jsonl`)")
    lines.append(f"- Drift geometry clusters: `{cluster_count}`  (from `conf_drift_clusters.tsv`)")
    lines.append("")
    lines.append("## 4. Training & Evaluation Commands")
    lines.append("")
    lines.append("### Stage-8 training (patched dataset)")
    lines.append("")
    lines.append("```bash")
    lines.append("cd /home/harshil/Harshil-PoCs/m-coder")
    lines.append("python3 -m ml.training.pipeline.stage08.train_stage08D \\")
    lines.append("  --dataset-file golden_exemplars_v1_conf_patch1.jsonl \\")
    lines.append("  --freeze-cert ml/training/pipeline/stage08/FREEZE_CERTIFICATE_STAGE8_CONF_PATCH1.json")
    lines.append("```")
    lines.append("")
    lines.append("### Stage-6C evaluation run (using patched adapter)")
    lines.append("")
    lines.append("```bash")
    lines.append("cd /home/harshil/Harshil-PoCs/m-coder")
    lines.append('OUT="ml/training/generated/stage6c_runs/conf_drift_fix_$(date +%Y%m%d_%H%M%S)"')
    lines.append("")
    lines.append("stage6c-run-suite \\")
    lines.append("  --config ml/training/pipeline/stage6/stage6c/config/gating_config.yaml \\")
    lines.append("  --seeds-dir ml/training/pipeline/stage6/stage6c/seeds \\")
    lines.append("  --suite canonical \\")
    lines.append("  --max-runs-per-cluster 1 \\")
    lines.append("  --amplify false \\")
    lines.append("  --resume false \\")
    lines.append('  --out "$OUT" \\')
    lines.append("  --mode execute \\")
    lines.append("  --model qwen25_14b \\")
    lines.append("  --model-path ml/training/models/qwen_stage8_conf_patch1/checkpoint")
    lines.append("```")
    lines.append("")
    lines.append("## 5. Re-evaluation Metrics Commands")
    lines.append("")
    lines.append("Assuming the new Stage-7 freeze bundle is at `ml/training/sft/stage7_conf_drift_fix/`:")
    lines.append("")
    lines.append("```bash")
    lines.append("cd /home/harshil/Harshil-PoCs/m-coder")
    lines.append("")
    lines.append("# New CONF→DES drift count")
    lines.append("jq -r '.run_id' ml/training/sft/stage7_conf_drift_fix/conf_to_des_drift.jsonl \\")
    lines.append("  | sort -u \\")
    lines.append("  | tee ml/training/sft/stage7_conf_drift_fix/conf_to_des_run_ids.txt")
    lines.append("")
    lines.append("wc -l ml/training/sft/stage7_conf_drift_fix/conf_to_des_run_ids.txt")
    lines.append("")
    lines.append("# S2/S3 safety violations in new ledger")
    lines.append('jq -c \'select(.severity == \"S2\" or .severity == \"S3\")\' "$OUT"/stage6c_ledger.jsonl | wc -l')
    lines.append("")
    lines.append("# Optional direct CONF→DES count from ledger (if fields present)")
    lines.append('jq -c \'select(.expected_phase == \"CONF\" and .final_phase == \"DES\")\' \\')
    lines.append('  "$OUT"/stage6c_ledger.jsonl | wc -l')
    lines.append("```")
    lines.append("")
    lines.append("## 6. Acceptance Criteria")
    lines.append("")
    lines.append("- **Safety**: S2/S3 counts remain `0` after the patch.")
    lines.append("- **Drift**: CONF→DES drift count decreases relative to the original run (target `0`).")
    lines.append("- **Provenance**: Original freeze artifacts and `golden_exemplars_v1.jsonl` remain immutable;")
    lines.append("  all changes flow through the `_conf_patch1` dataset + Stage-8 certificate and adapter alias.")
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[write-audit-report] wrote audit report to {report_path}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="conf-drift-pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-run-ids", help="Extract unique CONF→DES drift run_ids").set_defaults(
        func=cmd_list_run_ids
    )
    sub.add_parser("extract-traces", help="Filter suite_traces.jsonl to drift run_ids").set_defaults(
        func=cmd_extract_traces
    )
    sub.add_parser("cluster", help="Cluster drift runs by geometry").set_defaults(func=cmd_cluster)
    sub.add_parser("build-review-candidates", help="Build human-review candidates from traces").set_defaults(
        func=cmd_build_review_candidates
    )
    sub.add_parser(
        "build-corrections-from-reviewed",
        help="Convert reviewed candidates into Stage-7 schema corrections",
    ).set_defaults(func=cmd_build_corrections_from_reviewed)
    sub.add_parser("merge-dataset", help="Merge golden_exemplars_v1 with conf_drift_corrections").set_defaults(
        func=cmd_merge_dataset
    )
    sub.add_parser(
        "update-stage8-certificate",
        help="Create/update Stage-8 freeze certificate for conf_patch1 dataset",
    ).set_defaults(func=cmd_update_stage8_certificate)
    sub.add_parser(
        "write-audit-report",
        help="Write CONF_DES_DRIFT_AUDIT_v1.md with hashes and commands",
    ).set_defaults(func=cmd_write_audit_report)

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

