"""Stage-7 freeze CLI — stage6c-freeze entrypoint."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .freeze import run_freeze


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stage-7 deterministic freeze (stage6c-freeze)."
    )
    parser.add_argument(
        "--doctrine",
        type=Path,
        default=None,
        help="Path to STAGE4_VARIANT_GENERATION.md",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Output directory for JSONL + manifest",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        required=True,
        help="Path to stage6c_ledger.jsonl",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to harness config (for stage6c_suite_configuration_hash)",
    )
    parser.add_argument(
        "--split-seed",
        type=int,
        default=42,
        help="Seed for deterministic split",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing outputs")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, no write")
    args = parser.parse_args()

    default_doctrine = Path(__file__).parent.parent.parent.parent.parent / "pipeline" / "STAGE4_VARIANT_GENERATION.md"
    doctrine_path = args.doctrine if args.doctrine is not None else default_doctrine

    result = run_freeze(
        doctrine_path,
        args.out_dir,
        args.ledger,
        args.config,
        split_seed=args.split_seed,
        force=args.force,
        dry_run=args.dry_run,
    )

    if not result.success:
        reasons = sorted(result.freeze_block_reasons)
        print("FATAL: Freeze blocked. Reasons:", file=sys.stderr)
        for i, r in enumerate(reasons, 1):
            print(f"  {i}. {r}", file=sys.stderr)
        return 1

    print(f"Compiling doctrine from {doctrine_path}")
    print("Stage-6C full PASS verified (tier2, tier3, non-dummy)")
    if result.manifest:
        m = result.manifest
        total = m.get("total_rows", 0)
        bases = m.get("bases_count", 0)
        ch = m.get("corpus_hash", "")
        print(f"Corpus: {total} rows, {bases} bases, corpus_hash={ch}")
        sh = m.get("split_hashes", {})
        th = sh.get("train_hash", "")
        vh = sh.get("val_hash", "")
        print(f"Split: train_hash={th}, val_hash={vh}")
    if result.jsonl_path:
        print(f"Wrote {result.jsonl_path}")
    if result.manifest_path:
        print(f"Wrote {result.manifest_path}")
    print("FREEZE COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
