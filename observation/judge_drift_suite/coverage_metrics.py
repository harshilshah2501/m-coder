"""
Statistical coverage rigor — Judge Drift Suite v1.2.

Deterministic functions only. No LLM. No external heavy dependencies.
"""

from __future__ import annotations

import logging
from typing import Any

_logger = logging.getLogger(__name__)

TOTAL_PHASES = ("REF", "CONF", "DES", "MIX", "CODE")
TOTAL_GUARDS = ("CODE-01", "CODE-02", "CODE-04", "CODE-05", "CODE-06", "CODE-07", "CODE-08")
TOTAL_STRESS_SURFACES = (
    "Authority", "Classification", "Refusal", "Boundary", "Conditional", "Legitimacy",
    "Collision", "Dominance", "Execution", "Ownership", "Audit", "Enforcement", "Cross-tenant",
)
TOTAL_MUTATION_CLASSES = (
    "missing_authority", "misclassification", "refusal_erosion", "boundary_override",
    "conditional_skip", "legitimacy_gap", "dominance_violation", "ordering_violation",
    "collision_resolution", "escalation_on_collision", "guard_skip", "ownership_bypass",
    "audit_skip", "approval_gate", "cross_tenant_no_token", "cross_tenant_scope",
    "blast_radius", "refusal_integrity",
)


def _log_structured(event: str, payload: dict[str, Any]) -> None:
    _logger.info("%s", {"event": event, **payload})


def compute_phase_coverage(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    phase_coverage = exercised_phases / total_phases.
    total_phases = REF, CONF, DES, MIX, CODE.
    """
    if not results:
        _log_structured("phase_coverage", {"phase_coverage": 0.0, "phases_exercised": []})
        return {"phase_coverage": 0.0, "phases_exercised": []}
    exercised = set()
    for r in results:
        phase = r.get("phase")
        if phase and phase in TOTAL_PHASES:
            exercised.add(phase)
    phases_exercised = sorted(exercised)
    total = len(TOTAL_PHASES)
    ratio = len(exercised) / total if total else 0.0
    _log_structured("phase_coverage", {"phase_coverage": ratio, "phases_exercised": phases_exercised})
    return {"phase_coverage": ratio, "phases_exercised": phases_exercised}


def compute_guard_coverage(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    guard_coverage = exercised_guards / total_guards.
    Guard from result guard field (from case YAML). If not present, ignore.
    """
    if not results:
        _log_structured("guard_coverage", {"guard_coverage": 0.0, "guards_exercised": []})
        return {"guard_coverage": 0.0, "guards_exercised": []}
    exercised = set()
    for r in results:
        guard = r.get("guard")
        if guard and guard in TOTAL_GUARDS:
            exercised.add(guard)
    guards_exercised = sorted(exercised)
    total = len(TOTAL_GUARDS)
    ratio = len(exercised) / total if total else 0.0
    _log_structured("guard_coverage", {"guard_coverage": ratio, "guards_exercised": guards_exercised})
    return {"guard_coverage": ratio, "guards_exercised": guards_exercised}


def compute_surface_coverage(results: list[dict[str, Any]]) -> dict[str, Any]:
    """surface_coverage = exercised surfaces / total stress surfaces."""
    if not results:
        _log_structured("surface_coverage", {"surface_coverage": 0.0, "surfaces_exercised": []})
        return {"surface_coverage": 0.0, "surfaces_exercised": []}
    exercised = set()
    for r in results:
        surface = r.get("stress_surface")
        if surface and surface in TOTAL_STRESS_SURFACES:
            exercised.add(surface)
    surfaces_exercised = sorted(exercised)
    total = len(TOTAL_STRESS_SURFACES)
    ratio = len(exercised) / total if total else 0.0
    _log_structured("surface_coverage", {"surface_coverage": ratio, "surfaces_exercised": surfaces_exercised})
    return {"surface_coverage": ratio, "surfaces_exercised": surfaces_exercised}


def compute_mutation_coverage(results: list[dict[str, Any]]) -> dict[str, Any]:
    """mutation_coverage = exercised mutation classes / total mutation classes."""
    if not results:
        _log_structured("mutation_coverage", {"mutation_coverage": 0.0, "mutation_classes_exercised": []})
        return {"mutation_coverage": 0.0, "mutation_classes_exercised": []}
    exercised = set()
    for r in results:
        mutation = r.get("mutation_class")
        if mutation and mutation in TOTAL_MUTATION_CLASSES:
            exercised.add(mutation)
    mutation_classes_exercised = sorted(exercised)
    total = len(TOTAL_MUTATION_CLASSES)
    ratio = len(exercised) / total if total else 0.0
    _log_structured("mutation_coverage", {"mutation_coverage": ratio, "mutation_classes_exercised": mutation_classes_exercised})
    return {"mutation_coverage": ratio, "mutation_classes_exercised": mutation_classes_exercised}


def compute_min_case_density(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Min count among exercised guards; min count among exercised mutation classes.
    If none exercised, return 0.
    """
    if not results:
        _log_structured("min_case_density", {"min_cases_per_guard": 0, "min_cases_per_mutation": 0})
        return {"min_cases_per_guard": 0, "min_cases_per_mutation": 0}
    guard_counts: dict[str, int] = {}
    mutation_counts: dict[str, int] = {}
    for r in results:
        guard = r.get("guard")
        if guard and guard in TOTAL_GUARDS:
            guard_counts[guard] = guard_counts.get(guard, 0) + 1
        mutation = r.get("mutation_class")
        if mutation and mutation in TOTAL_MUTATION_CLASSES:
            mutation_counts[mutation] = mutation_counts.get(mutation, 0) + 1
    min_guard = min(guard_counts.values()) if guard_counts else 0
    min_mutation = min(mutation_counts.values()) if mutation_counts else 0
    _log_structured("min_case_density", {"min_cases_per_guard": min_guard, "min_cases_per_mutation": min_mutation})
    return {"min_cases_per_guard": min_guard, "min_cases_per_mutation": min_mutation}
