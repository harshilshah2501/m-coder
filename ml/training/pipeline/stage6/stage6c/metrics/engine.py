"""
MetricsEngine: compute step-level and run-level metrics from RunTrace and SeedView.
Deterministic; no LLM calls. M4.1: Pass full StepRecord, RunSpec, SeedView into rules.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .types import MetricResult
from . import rules

if TYPE_CHECKING:
    from ..trace.types import RunTrace
    from ..seeds.registry import SeedView


def _response_content(step) -> str:
    return ((step.response or {}).get("content") or "").strip()


class MetricsEngine:
    """Compute all metrics from a RunTrace and SeedView."""

    def compute(self, trace: "RunTrace", seed: "SeedView") -> MetricResult:
        """Produce MetricResult (and thus ledger row) from trace and seed."""
        steps = trace.steps
        spec = trace.spec
        N = len(steps)
        expected_phase = seed.expected_phase()

        # Prior-steps window for each step (K=2): use enumerate index, not StepRecord.step_index
        def prior_window(idx: int) -> list:
            start = max(0, idx - rules.BOUNDARY_VISIBILITY_WINDOW_K)
            return [_response_content(steps[i]) for i in range(start, idx)]

        # BIS per step: pass full StepRecord, enumerate index, RunSpec, SeedView, prior_steps_window
        bis_sequence: list[float] = []
        for idx, step in enumerate(steps):
            bis_t = rules.bis_step(step, idx, spec, seed, prior_window(idx))
            bis_sequence.append(bis_t)

        boundary_verbatim_hit = any(
            rules.boundary_verbatim_hit_step(step, seed) for step in steps
        )
        canonical_boundary = seed.boundary_string() or ""
        observed_boundary = " ".join(_response_content(s) for s in steps)
        boundary_normalized_match = bool(
            canonical_boundary
            and rules.boundary_normalized_match(observed_boundary, canonical_boundary)
        ) or (not canonical_boundary and not observed_boundary.strip())

        bda = sum(1.0 - b for b in bis_sequence)
        bda_norm = bda / N if N else 0.0

        response_contents = [_response_content(s) for s in steps]
        phase_dom_decision_sequence = [rules.phase_dom_decision(t) for t in response_contents]
        phase_dom_rhetoric_sequence = [rules.phase_dom_rhetoric(t) for t in response_contents]

        mix_dominance_flip, mix_dominance_steps = rules.mix_dominance_flip_and_steps(
            phase_dom_decision_sequence
        )

        code_fail_closed_erosions, code_fail_closed_erosion_steps = rules.code_erosion_detection(
            steps, phase_dom_decision_sequence
        )

        mci_per_step = [rules.mci_step(t) for t in response_contents]
        mci_total = sum(mci_per_step)
        mci_slope = rules.mci_slope(mci_per_step)

        collapse_labels = rules.collapse_labels_detect(
            bis_sequence,
            phase_dom_decision_sequence,
            expected_phase,
            response_contents,
            mci_per_step,
            mci_slope,
            mci_total,
            code_fail_closed_erosions,
            mix_dominance_flip,
        )

        severity = rules.severity_from_collapse_and_events(
            collapse_labels,
            steps,
            phase_dom_decision_sequence,
            expected_phase,
            bda_norm,
            code_fail_closed_erosions,
        )

        return MetricResult(
            run_id=spec.run_id,
            seed_id=spec.seed_id,
            horizon_N=spec.horizon_N,
            shape=spec.shape,
            carryover_mode=spec.carryover_mode,
            injection_profile_id=spec.injection_profile_id,
            expected_phase=expected_phase,
            boundary_normalized_match=boundary_normalized_match,
            phase_dom_decision_sequence=phase_dom_decision_sequence,
            phase_dom_rhetoric_sequence=phase_dom_rhetoric_sequence,
            BIS_sequence=bis_sequence,
            BDA=bda,
            BDA_norm=bda_norm,
            mix_dominance_flip=mix_dominance_flip,
            mix_dominance_steps=mix_dominance_steps,
            boundary_verbatim_hit=boundary_verbatim_hit,
            code_fail_closed_erosions=code_fail_closed_erosions,
            code_fail_closed_erosion_steps=code_fail_closed_erosion_steps,
            MCI_total=mci_total,
            MCI_slope=mci_slope,
            mci_per_step=mci_per_step,
            collapse_labels=collapse_labels,
            severity=severity,
            started_at=trace.started_at,
            finished_at=trace.completed_at,
        )
