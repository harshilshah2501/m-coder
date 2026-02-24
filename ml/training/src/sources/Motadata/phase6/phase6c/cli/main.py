"""
CLI: phase6c-smoke-run --config <path> --seeds-dir <dir> --out <dir>
Runs small grid: 1-2 seeds, N in {3,6}, shapes linear/retry_biased, carryover cold_start/full_transcript.
Uses DummyModelAdapter; writes JSONL traces and prints summary.
"""
from __future__ import annotations

import argparse
import uuid
from pathlib import Path

from ..config.loader import load_config
from ..config.schema import HarnessConfig
from ..seeds.file_registry import FileSeedRegistry
from ..trace.types import RunSpec
from ..trace.serialization import append_run_trace_jsonl
from ..loop.runner import LoopRunner
from ..model.dummy import DummyModelAdapter
from ..metrics.engine import MetricsEngine
from ..metrics.ledger import append_ledger_row


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase-6C smoke run (M2)")
    parser.add_argument("--config", type=str, help="Path to harness config (YAML or JSON)")
    parser.add_argument("--seeds-dir", type=str, help="Directory of seed JSON files (overrides config if set)")
    parser.add_argument("--out", type=str, required=True, help="Output directory for traces")
    args = parser.parse_args()

    if args.config:
        config = load_config(args.config)
        seeds_dir = args.seeds_dir or config.seeds_dir
    else:
        if not args.seeds_dir:
            parser.error("Either --config or --seeds-dir must be provided")
        seeds_dir = args.seeds_dir
        config = HarnessConfig(seeds_dir=seeds_dir)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    registry = FileSeedRegistry(seeds_dir)
    seed_ids = registry.list_seed_ids()
    if not seed_ids:
        print("No seeds found in", seeds_dir)
        return
    # Use at most 2 seeds for smoke
    seeds_to_run = seed_ids[:2]
    horizons = [3, 6] if 3 in config.horizons and 6 in config.horizons else config.horizons[:2]
    if 3 not in horizons and 6 not in horizons:
        horizons = [3, 6]
    shapes = list(config.shapes)[:2]  # linear, retry_biased
    carryover_modes = [m for m in config.carryover_modes if m != "summary_compressed"]
    if not carryover_modes:
        carryover_modes = ["cold_start", "full_transcript"]

    # Use config.injection_profiles for grid (e.g. ["none", "deadline_squeeze", "tool_failure"] for smoke with 1-2 profiles)
    injection_profiles = list(config.injection_profiles)
    if not injection_profiles:
        injection_profiles = ["none"]

    model = DummyModelAdapter()
    runner = LoopRunner(
        registry,
        model,
        max_transcript_chars=config.max_transcript_chars,
        full_transcript_policy=config.full_transcript_policy,
    )
    metrics_engine = MetricsEngine()
    output_file = out_dir / "smoke_traces.jsonl"
    ledger_file = out_dir / "phase6c_ledger.jsonl"
    run_count = 0
    for seed_id in seeds_to_run:
        for N in horizons:
            for shape in shapes:
                for carryover in carryover_modes:
                    for injection_profile_id in injection_profiles:
                        run_id = f"smoke-{uuid.uuid4().hex[:8]}"
                        spec = RunSpec(
                            run_id=run_id,
                            seed_id=seed_id,
                            horizon_N=N,
                            shape=shape,
                            carryover_mode=carryover,
                            injection_profile_id=injection_profile_id,
                        )
                        try:
                            trace = runner.run_loop(spec)
                            append_run_trace_jsonl(trace, output_file)
                            seed_view = registry.get(seed_id)
                            severity_str = "—"
                            collapse_str = "—"
                            if seed_view:
                                result = metrics_engine.compute(trace, seed_view)
                                row = result.to_ledger_row()
                                append_ledger_row(row, ledger_file)
                                severity_str = result.severity
                                collapse_str = ",".join(result.collapse_labels) if result.collapse_labels else "none"
                            run_count += 1
                            wrapper_note = ""
                            if injection_profile_id != "none":
                                n_wrapper = sum(
                                    1 for s in trace.steps for m in s.prompt_messages if m.get("origin") == "wrapper"
                                )
                                wrapper_note = f" wrappers={n_wrapper}"
                            print(f"  {run_id} seed={seed_id} N={N} shape={shape} carryover={carryover} profile={injection_profile_id}{wrapper_note} -> {len(trace.steps)} steps | severity={severity_str} collapses=[{collapse_str}]")
                        except NotImplementedError as e:
                            print(f"  SKIP {run_id}: {e}")
                        except Exception as e:
                            print(f"  FAIL {run_id}: {e}")
    print(f"\nDone: {run_count} runs written to {output_file}")


if __name__ == "__main__":
    main()
