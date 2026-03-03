from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from ..config.loader import load_config
from ..config.schema import HarnessConfig
from ..loop.runner import LoopRunner
from ..model.dummy import DummyModelAdapter
from ..model.qwen25_14b import Qwen25_14B_InstructAdapter
from ..seeds.file_registry import FileSeedRegistry
from .amplifier import AmplificationPlan, analyze_ledger_for_amplification
from .config import ExperimentConfig
from .executor import execute_plan
from .planner import PlanItem, apply_repeats, generate_base_plan, validate_coverage


def _build_experiment_config(hcfg: HarnessConfig, seeds: List[str], args) -> ExperimentConfig:
    """
    Build ExperimentConfig from HarnessConfig + CLI flags.

    Suite mapping and min_runs_per_profile_carryover may be optionally present
    on the harness config; if absent, fall back to safe defaults.
    """
    canonical_profiles = getattr(hcfg, "canonical_profiles", []) or []
    stress_profiles = getattr(hcfg, "stress_profiles", []) or []
    min_runs_per_profile_carryover = getattr(
        hcfg, "min_runs_per_profile_carryover", 20
    )

    return ExperimentConfig(
        seeds=seeds,
        horizons=hcfg.horizons,
        shapes=hcfg.shapes,
        carryovers=hcfg.carryover_modes,
        injection_profiles=hcfg.injection_profiles,
        repeats_per_cluster=args.repeats_per_cluster,
        amplification_k=args.amplify_k,
        max_runs_per_cluster=args.max_runs_per_cluster,
        canonical_profiles=list(canonical_profiles),
        stress_profiles=list(stress_profiles),
        min_runs_per_profile_carryover=int(min_runs_per_profile_carryover),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage-6C suite runner (M6 orchestrator).")
    parser.add_argument("--config", type=str, help="Path to harness config (YAML or JSON)")
    parser.add_argument("--seeds-dir", type=str, help="Directory of seed JSON files (overrides config if set)")
    parser.add_argument("--out", type=str, required=True, help="Output directory for traces + ledger + reports")
    parser.add_argument("--mode", type=str, choices=["plan", "execute"], default="plan")
    parser.add_argument(
        "--model",
        type=str,
        default="dummy",
        choices=["dummy", "openai", "local", "qwen25_14b"],
        help="Model adapter name (dummy supported; others are placeholders)",
    )
    parser.add_argument("--model-path", type=str, default=None, help="Path to local HF model")
    parser.add_argument("--max-new-tokens", type=int, default=None, help="Max new tokens per generation")
    parser.add_argument("--repeats-per-cluster", type=int, default=5)
    parser.add_argument("--amplify", type=str, default="true", choices=["true", "false"])
    parser.add_argument("--amplify-k", type=int, default=10)
    parser.add_argument("--max-runs-per-cluster", type=int, default=50)
    parser.add_argument("--suite", type=str, choices=["canonical", "stress", "both"], default="both")
    parser.add_argument("--resume", type=str, default="true", choices=["true", "false"])
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load harness config + seeds
    if args.config:
        hcfg = load_config(args.config)
        seeds_dir = args.seeds_dir or hcfg.seeds_dir
    else:
        if not args.seeds_dir:
            parser.error("Either --config or --seeds-dir must be provided")
        seeds_dir = args.seeds_dir
        hcfg = HarnessConfig(seeds_dir=seeds_dir)

    registry = FileSeedRegistry(seeds_dir)
    seed_ids = registry.list_seed_ids()
    if not seed_ids:
        print("No seeds found in", seeds_dir)
        return

    exp_cfg = _build_experiment_config(hcfg, seed_ids, args)

    # Base plan + coverage validation
    base_plan = generate_base_plan(exp_cfg, suite_filter=args.suite)
    full_plan = apply_repeats(base_plan, exp_cfg.repeats_per_cluster)
    coverage = validate_coverage(full_plan, exp_cfg)

    print(f"Planned runs: {len(full_plan)} (base clusters={len(base_plan)})")
    print(f"Coverage OK: {coverage.passed}")
    if coverage.deficits:
        print("Coverage deficits:")
        for d in coverage.deficits:
            print(f"  - axis={d.axis} key={d.key} required={d.required} actual={d.actual}")

    if args.mode == "plan":
        return

    # Block summary_compressed in execute mode (stubbed in M2/M6).
    if "summary_compressed" in exp_cfg.carryovers:
        raise SystemExit(
            "summary_compressed carryover is not supported yet (stubbed in M2). "
            "Remove it from config or implement summarizer before running execute mode."
        )

    # Execute mode
    if args.model == "dummy":
        model = DummyModelAdapter()
    elif args.model == "qwen25_14b":
        if not args.model_path:
            raise ValueError("Provide --model-path for qwen25_14b")
        model = Qwen25_14B_InstructAdapter(
            model_path=args.model_path,
            max_tokens=args.max_new_tokens or 512,
        )
    else:
        raise SystemExit(
            f"Model adapter '{args.model}' not implemented yet. "
            "Implement stage6c/model/{args.model}.py and wire it into the orchestrator CLI."
        )
    runner = LoopRunner(
        registry,
        model,
        max_transcript_chars=hcfg.max_transcript_chars,
        full_transcript_policy=hcfg.full_transcript_policy,
    )

    resume_flag = args.resume == "true"
    amplify_flag = args.amplify == "true"

    print("\nExecuting base plan...")
    summary = execute_plan(full_plan, registry, runner, model, out_dir, resume=resume_flag)
    print(
        f"Executed {summary.runs_executed} / {summary.runs_planned} runs "
        f"(skipped={summary.runs_skipped}, resume={resume_flag})"
    )

    if not amplify_flag:
        return

    # Amplification based on current ledger
    ledger_path = out_dir / "stage6c_ledger.jsonl"
    print("\nAnalyzing ledger for amplification opportunities...")
    amp_plan = analyze_ledger_for_amplification(ledger_path, exp_cfg)

    # Write amplification plan for inspection
    amp_json = {
        "base_repeats": [
            {
                "seed_id": p.seed_id,
                "injection_profile_id": p.injection_profile_id,
                "carryover_mode": p.carryover_mode,
                "shape": p.shape,
                "horizon_N": p.horizon_N,
                "suite": p.suite,
            }
            for p in amp_plan.base_repeats
        ],
        "adjacent_repeats": [
            {
                "seed_id": p.seed_id,
                "injection_profile_id": p.injection_profile_id,
                "carryover_mode": p.carryover_mode,
                "shape": p.shape,
                "horizon_N": p.horizon_N,
                "suite": p.suite,
            }
            for p in amp_plan.adjacent_repeats
        ],
    }
    (out_dir / "amplification_plan.json").write_text(json.dumps(amp_json, indent=2), encoding="utf-8")

    amp_total = len(amp_plan.base_repeats) + len(amp_plan.adjacent_repeats)
    print(f"Amplification scheduled additional runs: {amp_total}")
    if amp_total == 0:
        return

    print("Executing amplification runs...")
    amp_full_plan: List[PlanItem] = []
    amp_full_plan.extend(amp_plan.base_repeats)
    amp_full_plan.extend(amp_plan.adjacent_repeats)
    amp_summary = execute_plan(amp_full_plan, registry, runner, model, out_dir, resume=True)
    print(
        f"Amplification executed {amp_summary.runs_executed} / {amp_summary.runs_planned} runs "
        f"(skipped={amp_summary.runs_skipped}, resume=True)"
    )
    print(
        "Next move: implement a real ModelAdapter and rerun the suite; "
        "the Stage-6C report will evaluate non-dummy gates separately."
    )


if __name__ == "__main__":
    main()

