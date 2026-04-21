from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

ALLOWED_CONTEXT_KEYS = ("stage", "failure_mode", "mechanism", "graph_path", "playbook_step")
_CORE_CONTEXT_KEYS = ("stage", "failure_mode", "mechanism")
_ANCHOR_OVERLAP_THRESHOLD = 0.34


@dataclass(frozen=True)
class ResolverOutput:
    source: str
    anchors: list[str]
    context: dict[str, str]
    provenance_weight: float
    confidence: float
    evidence_kind: str
    conflict: bool
    chain: list[str]

    def __post_init__(self) -> None:
        bad = sorted(set(self.context) - set(ALLOWED_CONTEXT_KEYS))
        if bad:
            raise ValueError(f"ResolverOutput.context has unsupported keys: {bad}")
        if self.evidence_kind not in {"anchor", "stage", "failure_mode", "playbook", "graph_path", "supporting"}:
            raise ValueError(f"Unsupported evidence_kind: {self.evidence_kind}")


@dataclass
class ComposedEvidence:
    anchors: list[str]
    context: dict[str, str]
    confidence: float
    conflict: bool
    chain: list[str]
    provenance: list[dict[str, Any]]
    metadata: dict[str, Any]
    resolver_outputs: list[ResolverOutput] = field(default_factory=list)


@dataclass
class QualityAssessment:
    evidence_quality: str
    quality_reasons: list[str]
    metadata: dict[str, Any]


class C1SignalCollectors:
    def collect(self, query: str, route: str, answer: str | None, metadata: dict[str, Any]) -> list[ResolverOutput]:
        lower_query = query.lower()
        route_meta = dict(metadata or {})
        if route == "identity":
            return [
                ResolverOutput(
                    source="identity_router",
                    anchors=["Motadata Coder", "constitutional AI framework"],
                    context={"stage": "identity_resolution", "mechanism": "identity_trigger"},
                    provenance_weight=0.99,
                    confidence=0.99,
                    evidence_kind="anchor",
                    conflict=False,
                    chain=["identity", "router"],
                )
            ]
        if route == "structural":
            graph_result = route_meta.get("graph_result") if isinstance(route_meta.get("graph_result"), dict) else {}
            fqcn = str((graph_result or {}).get("qualified_name") or "")
            graph_error = str(route_meta.get("graph_error") or "")
            anchors = [v for v in (fqcn, str((graph_result or {}).get("file_path") or "")) if v]
            if fqcn:
                return [
                    ResolverOutput(
                        source="structural_graph",
                        anchors=anchors,
                        context={
                            "stage": "structural_resolution",
                            "mechanism": "neo4j_base_class_lookup",
                            "graph_path": fqcn,
                        },
                        provenance_weight=0.95,
                        confidence=0.95,
                        evidence_kind="graph_path",
                        conflict=False,
                        chain=["structural", "graph_lookup"],
                    )
                ]
            return [
                ResolverOutput(
                    source="structural_router_unavailable",
                    anchors=[],
                    context={
                        "stage": "structural_resolution",
                        "failure_mode": graph_error or "graph_unavailable",
                        "mechanism": "graph_required_no_semantic_fallback",
                    },
                    provenance_weight=0.9,
                    confidence=0.9,
                    evidence_kind="failure_mode",
                    conflict=False,
                    chain=["structural", "graph_lookup"],
                )
            ]
        lexical = "token" in lower_query
        return [
            ResolverOutput(
                source="lexical_fallback" if lexical else "semantic_fallback",
                anchors=[],
                context={"stage": "semantic_resolution", "mechanism": "default_semantic"},
                provenance_weight=0.6,
                confidence=0.5,
                evidence_kind="supporting",
                conflict=False,
                chain=["semantic", "fallback"],
            )
        ]


class C2EvidenceComposer:
    def compose(self, outputs: Iterable[ResolverOutput]) -> ComposedEvidence:
        ordered = sorted(outputs, key=lambda x: (x.provenance_weight, x.confidence), reverse=True)
        if not ordered:
            return ComposedEvidence([], {}, 0.0, False, [], [], {"conflict_markers": [], "policy": "preserve_highest"}, [])

        anchors: list[str] = []
        seen_anchors: set[str] = set()
        context: dict[str, str] = {}
        resolved_source: dict[str, str] = {}
        conflict_markers: list[dict[str, str]] = []
        chain: list[str] = []
        provenance: list[dict[str, Any]] = []
        confidence = ordered[0].confidence

        for output in ordered:
            for anchor in output.anchors:
                norm = anchor.strip().lower()
                if norm and norm not in seen_anchors:
                    seen_anchors.add(norm)
                    anchors.append(anchor)
            for key, value in output.context.items():
                if key not in ALLOWED_CONTEXT_KEYS or not value:
                    continue
                if key not in context:
                    context[key] = value
                    resolved_source[key] = output.source
                    continue
                if context[key] != value:
                    conflict_markers.append(
                        {
                            "key": key,
                            "kept_value": context[key],
                            "kept_source": resolved_source.get(key, ""),
                            "rejected_value": value,
                            "rejected_source": output.source,
                        }
                    )
                    if key in _CORE_CONTEXT_KEYS:
                        confidence *= 0.85
            for item in output.chain:
                if item and item not in chain:
                    chain.append(item)
            provenance.append(
                {
                    "source": output.source,
                    "provenance_weight": output.provenance_weight,
                    "confidence": output.confidence,
                    "evidence_kind": output.evidence_kind,
                    "conflict": output.conflict,
                    "anchors": list(output.anchors),
                    "context": dict(output.context),
                    "chain": list(output.chain),
                }
            )

        has_conflict = bool(conflict_markers) or any(output.conflict for output in ordered)
        return ComposedEvidence(
            anchors=anchors,
            context=context,
            confidence=max(0.0, min(1.0, confidence)),
            conflict=has_conflict,
            chain=chain,
            provenance=provenance,
            metadata={
                "conflict_markers": conflict_markers,
                "policy": "preserve_highest+mark_conflicts+downgrade_confidence_if_core_disagreement",
            },
            resolver_outputs=ordered,
        )


class C3QualityEvaluator:
    def evaluate(self, composed: ComposedEvidence, mode: str = "ask") -> QualityAssessment:
        families = self._families(composed.resolver_outputs)
        meta: dict[str, Any] = {"signal_families": sorted(families)}
        if families == {"structural"}:
            return QualityAssessment("STRONG", ["STRUCTURAL_ONLY"], meta)
        if families == {"lexical"}:
            return QualityAssessment("WEAK", ["LEXICAL_ONLY"], meta)
        if families == {"behavior_flow"}:
            required = self._required_file_anchors(composed)
            meta["required_file_anchors"] = required
            if mode in {"debug", "plan"} and required:
                return QualityAssessment("MODERATE", ["BEHAVIOR_FLOW_ONLY_REQUIRED_ANCHOR"], meta)
            return QualityAssessment("WEAK", ["BEHAVIOR_FLOW_ONLY"], meta)
        if families == {"behavior_flow", "structural"}:
            return QualityAssessment("STRONG", ["STRUCTURAL_PLUS_BEHAVIOR_FLOW"], meta)
        if "behavior_flow" in families and "graph" in families:
            overlap = self._anchor_overlap(
                self._anchors_for_family(composed.resolver_outputs, "behavior_flow"),
                self._anchors_for_family(composed.resolver_outputs, "graph"),
            )
            validated = self._has_validated_flow(composed.resolver_outputs)
            meta.update(
                {
                    "anchor_overlap": overlap,
                    "anchor_overlap_threshold": _ANCHOR_OVERLAP_THRESHOLD,
                    "validated_flow": validated,
                    "chain": list(composed.chain),
                }
            )
            if validated and overlap >= _ANCHOR_OVERLAP_THRESHOLD:
                return QualityAssessment("STRONG", ["BEHAVIOR_FLOW_PLUS_GRAPH_VALIDATED"], meta)
            return QualityAssessment("MODERATE", ["BEHAVIOR_FLOW_PLUS_GRAPH_PARTIAL"], meta)
        return QualityAssessment("MODERATE", ["MIXED_SIGNALS"], meta)

    def _families(self, outputs: list[ResolverOutput]) -> set[str]:
        families: set[str] = set()
        for output in outputs:
            src = output.source.lower()
            chain = " ".join(output.chain).lower()
            if "structural" in src or "structural" in chain:
                families.add("structural")
            if "lexical" in src:
                families.add("lexical")
            if "behavior_flow" in src or "behavior_flow" in chain or output.evidence_kind in {"stage", "failure_mode", "playbook"}:
                families.add("behavior_flow")
            if "graph" in src or output.evidence_kind == "graph_path" or output.context.get("graph_path"):
                families.add("graph")
        return families

    def _required_file_anchors(self, composed: ComposedEvidence) -> list[str]:
        return [a for a in composed.anchors if "/" in a or a.endswith((".py", ".java"))]

    def _anchors_for_family(self, outputs: list[ResolverOutput], family: str) -> set[str]:
        out: set[str] = set()
        for output in outputs:
            if family in self._families([output]):
                out.update(a.strip().lower() for a in output.anchors if a.strip())
        return out

    def _anchor_overlap(self, left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        return len(left & right) / len(left | right)

    def _has_validated_flow(self, outputs: list[ResolverOutput]) -> bool:
        for output in outputs:
            if "behavior_flow" not in self._families([output]):
                continue
            if output.confidence < 0.6:
                continue
            if output.context.get("stage") or output.context.get("mechanism") or output.context.get("failure_mode"):
                return True
        return False


class AnswerAssembler:
    def assemble(
        self,
        *,
        route_answer: str,
        composed: ComposedEvidence,
        quality: QualityAssessment,
        default_fallback_step: str,
    ) -> list[str]:
        has_anchor = bool(composed.anchors)
        has_context = any(composed.context.get(key) for key in ALLOWED_CONTEXT_KEYS)
        summary = route_answer.strip()
        if quality.evidence_quality in {"STRONG", "MODERATE"} and has_anchor and has_context:
            summary = f"{summary} Anchored by `{composed.anchors[0]}` with context: {self._context_text(composed.context)}."
        elif quality.evidence_quality == "WEAK":
            summary = f"{summary} Available evidence remains weak, so no fabricated precision is added."
        return [summary, self._next_step(composed, quality, default_fallback_step)]

    def _context_text(self, context: dict[str, str]) -> str:
        return ", ".join(f"{k}={context[k]}" for k in ALLOWED_CONTEXT_KEYS if context.get(k))

    def _next_step(self, composed: ComposedEvidence, quality: QualityAssessment, fallback: str) -> str:
        if quality.evidence_quality == "STRONG":
            owner = composed.anchors[0] if composed.anchors else (composed.context.get("graph_path") or "owner anchor")
            return f"Inspect `{owner}` first, then validate downstream callers touched by this routed answer."
        if quality.evidence_quality == "MODERATE":
            target = self._diagnostic_anchor(composed) or composed.context.get("failure_mode") or "required anchor"
            return f"Run a constrained diagnostic around `{target}` and verify required file anchors before changes."
        return fallback

    def _diagnostic_anchor(self, composed: ComposedEvidence) -> str | None:
        for anchor in composed.anchors:
            if "/" in anchor or anchor.endswith((".py", ".java")):
                return anchor
        return composed.anchors[0] if composed.anchors else None


class LaneCOrchestrator:
    def __init__(self) -> None:
        self.collectors = C1SignalCollectors()
        self.composer = C2EvidenceComposer()
        self.quality_evaluator = C3QualityEvaluator()
        self.answer_assembler = AnswerAssembler()

    def orchestrate(
        self,
        *,
        query: str,
        route: str,
        route_answer: str,
        metadata: dict[str, Any],
        mode: str,
        default_fallback_step: str,
    ) -> dict[str, Any]:
        resolver_outputs = self.collectors.collect(query, route, route_answer, metadata)
        composed = self.composer.compose(resolver_outputs)
        quality = self.quality_evaluator.evaluate(composed, mode=mode)
        steps = self.answer_assembler.assemble(
            route_answer=route_answer,
            composed=composed,
            quality=quality,
            default_fallback_step=default_fallback_step,
        )
        return {
            "resolver_outputs": [self._resolver_to_dict(item) for item in resolver_outputs],
            "composed_evidence": {
                "anchors": list(composed.anchors),
                "context": dict(composed.context),
                "confidence": composed.confidence,
                "conflict": composed.conflict,
                "chain": list(composed.chain),
                "provenance": list(composed.provenance),
                "metadata": dict(composed.metadata),
            },
            "quality": {
                "evidence_quality": quality.evidence_quality,
                "quality_reasons": list(quality.quality_reasons),
                "metadata": dict(quality.metadata),
            },
            "plan_steps": steps,
        }

    def _resolver_to_dict(self, output: ResolverOutput) -> dict[str, Any]:
        return {
            "source": output.source,
            "anchors": list(output.anchors),
            "context": {key: output.context.get(key, "") for key in ALLOWED_CONTEXT_KEYS if output.context.get(key, "")},
            "provenance_weight": output.provenance_weight,
            "confidence": output.confidence,
            "evidence_kind": output.evidence_kind,
            "conflict": output.conflict,
            "chain": list(output.chain),
        }
