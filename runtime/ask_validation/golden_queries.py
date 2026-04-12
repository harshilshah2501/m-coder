"""
Golden query suite for Layer-5 grounded Ask validation.

Defines deterministic grouped suites for:
- AIOps grounding
- debug
- plan/change
- no-match
- adversarial ambiguity probes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class QueryExpectation(Enum):
    """Expected outcome type for a golden query."""
    GROUNDED = "grounded"  # Files MUST be found
    NO_MATCH_VALID = "no_match_valid"  # No files expected; justification required
    EITHER_WITH_JUSTIFICATION = "either"  # Either grounded OR valid no-match


@dataclass
class GoldenQuery:
    """
    A golden query definition for validation.
    
    Attributes:
        id: Unique identifier for the query
        query: The natural language query text
        expectation: Expected outcome type
        expected_file_patterns: Substrings that should appear in found file paths (if grounded)
        expected_selectors: Selectors that should contribute (if grounded)
        repo_files: Files to create in test repo for this query
        description: Human-readable description of what this tests
        no_match_keywords: Keywords that should appear in no-match justification
    """
    id: str
    query: str
    expectation: QueryExpectation
    suite: Literal["aiops_grounding", "debug", "plan_change", "no_match", "adversarial"]
    expected_intent_type: str
    expected_quality_set: list[str]
    expected_core_presence: bool
    expected_subsystem: str | None = None
    repo_files: dict[str, str] = field(default_factory=dict)
    expected_file_patterns: list[str] = field(default_factory=list)
    expected_selectors: list[str] = field(default_factory=list)
    description: str = ""
    no_match_keywords: list[str] = field(default_factory=list)


GOLDEN_QUERY_SUITE: list[GoldenQuery] = [
    # === AIOPS GROUNDING QUERIES ===
    GoldenQuery(
        id="aiops_alert_correlation_impl",
        query="Where is alert correlation implemented?",
        expectation=QueryExpectation.GROUNDED,
        suite="aiops_grounding",
        expected_intent_type="CODE_INTENT",
        expected_quality_set=["STRONG", "WEAK"],
        expected_core_presence=True,
        expected_subsystem="correlation",
        repo_files={
            "src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java": "class AlertCorrelationEngine {}\n",
            "src/main/java/com/mindarray/aiops/correlation/CorrelationService.java": "class CorrelationService {}\n",
            "tests/correlation_test.py": "def test_alert_correlation():\n    pass\n",
        },
        expected_file_patterns=["correlation"],
        description="AIOps grounding should prefer correlation implementation files.",
    ),
    GoldenQuery(
        id="aiops_topology_anomaly",
        query="How does topology anomaly detection work?",
        expectation=QueryExpectation.GROUNDED,
        suite="aiops_grounding",
        expected_intent_type="CODE_INTENT",
        expected_quality_set=["STRONG", "WEAK"],
        expected_core_presence=True,
        expected_subsystem="topology",
        repo_files={
            "src/main/java/com/mindarray/aiops/topology/TopologyAnomalyDetector.java": "class TopologyAnomalyDetector {}\n",
            "src/main/java/com/mindarray/aiops/topology/TopologyGraphService.java": "class TopologyGraphService {}\n",
            "logs/topology.log": "anomaly detected\n",
        },
        expected_file_patterns=["topology"],
        description="Topology query should prefer topology subsystem implementation files.",
    ),
    GoldenQuery(
        id="aiops_incident_correlation",
        query="Where is incident correlation handled?",
        expectation=QueryExpectation.GROUNDED,
        suite="aiops_grounding",
        expected_intent_type="CODE_INTENT",
        expected_quality_set=["STRONG", "WEAK"],
        expected_core_presence=True,
        expected_subsystem="correlation",
        repo_files={
            "src/main/java/com/mindarray/aiops/correlation/IncidentCorrelationHandler.java": "class IncidentCorrelationHandler {}\n",
            "src/main/java/com/mindarray/aiops/alerting/AlertProcessor.java": "class AlertProcessor {}\n",
            "vendor/highcharts.js": "/* vendor */\n",
        },
        expected_file_patterns=["incident", "correlation"],
        description="Incident correlation query should ground in core correlation handlers.",
    ),
    GoldenQuery(
        id="aiops_event_ingestion_pipeline",
        query="How does event ingestion pipeline work?",
        expectation=QueryExpectation.GROUNDED,
        suite="aiops_grounding",
        expected_intent_type="CODE_INTENT",
        expected_quality_set=["STRONG", "WEAK"],
        expected_core_presence=True,
        expected_subsystem="ingestion",
        repo_files={
            "src/main/java/com/mindarray/aiops/ingestion/EventIngestionPipeline.java": "class EventIngestionPipeline {}\n",
            "src/main/java/com/mindarray/aiops/ingestion/EventParser.java": "class EventParser {}\n",
            "test-plugin-metrics/ingestion_metrics.json": "{\"metric\":1}\n",
        },
        expected_file_patterns=["ingestion"],
        description="Event ingestion query should prioritize ingestion pipeline implementation.",
    ),

    # === DEBUG QUERIES ===
    GoldenQuery(
        id="debug_retry_policy_ingestion",
        query="Why retry policy not applied in ingestion?",
        expectation=QueryExpectation.EITHER_WITH_JUSTIFICATION,
        suite="debug",
        expected_intent_type="DEBUG_INTENT",
        expected_quality_set=["STRONG", "WEAK", "INSUFFICIENT"],
        expected_core_presence=True,
        expected_subsystem="ingestion",
        repo_files={
            "src/main/java/com/mindarray/aiops/ingestion/RetryPolicy.java": "class RetryPolicy {}\n",
            "src/main/java/com/mindarray/aiops/ingestion/IngestionRunner.java": "class IngestionRunner {}\n",
            "logs/retry.log": "retry not applied\n",
        },
        expected_file_patterns=["retry", "ingestion"],
        description="Debug query should map to ingestion retry policy code when available.",
    ),
    GoldenQuery(
        id="debug_null_handling_device_payload",
        query="Where is null handling for device health payload?",
        expectation=QueryExpectation.EITHER_WITH_JUSTIFICATION,
        suite="debug",
        expected_intent_type="DEBUG_INTENT",
        expected_quality_set=["STRONG", "WEAK", "INSUFFICIENT"],
        expected_core_presence=True,
        repo_files={
            "src/main/java/com/mindarray/aiops/ingestion/DeviceHealthPayloadParser.java": "class DeviceHealthPayloadParser {}\n",
            "src/main/java/com/mindarray/aiops/ingestion/NullSafeUtils.java": "class NullSafeUtils {}\n",
            "tests/device_payload_test.py": "def test_null_payload():\n    pass\n",
        },
        expected_file_patterns=["device", "payload"],
        description="Null handling debug query should locate relevant ingestion parser/utils.",
    ),
    GoldenQuery(
        id="debug_empty_event_list_failure",
        query="Why correlation engine may fail on empty event list?",
        expectation=QueryExpectation.EITHER_WITH_JUSTIFICATION,
        suite="debug",
        expected_intent_type="DEBUG_INTENT",
        expected_quality_set=["STRONG", "WEAK", "INSUFFICIENT"],
        expected_core_presence=True,
        expected_subsystem="correlation",
        repo_files={
            "src/main/java/com/mindarray/aiops/correlation/CorrelationEngine.java": "class CorrelationEngine {}\n",
            "src/main/java/com/mindarray/aiops/correlation/EventListValidator.java": "class EventListValidator {}\n",
            "logs/correlation.log": "empty event list\n",
        },
        expected_file_patterns=["correlation", "event"],
        description="Debug failure query should find correlation engine and validators.",
    ),

    # === PLAN/CHANGE QUERIES ===
    GoldenQuery(
        id="plan_timeout_event_processor",
        query="Plan change to add timeout to event processor",
        expectation=QueryExpectation.GROUNDED,
        suite="plan_change",
        expected_intent_type="PLAN_INTENT",
        expected_quality_set=["STRONG", "WEAK"],
        expected_core_presence=True,
        expected_subsystem="ingestion",
        repo_files={
            "src/main/java/com/mindarray/aiops/ingestion/EventProcessor.java": "class EventProcessor {}\n",
            "src/main/java/com/mindarray/aiops/ingestion/ProcessorConfig.java": "class ProcessorConfig {}\n",
            "test-plugin-metrics/processor_metrics.json": "{\"metric\":1}\n",
        },
        expected_file_patterns=["processor"],
        description="Plan query should ground in event processor code/config files.",
    ),
    GoldenQuery(
        id="plan_sla_breach_override",
        query="What files update for SLA breach override?",
        expectation=QueryExpectation.GROUNDED,
        suite="plan_change",
        expected_intent_type="PLAN_INTENT",
        expected_quality_set=["STRONG", "WEAK"],
        expected_core_presence=True,
        repo_files={
            "src/main/java/com/mindarray/aiops/alerting/SlaBreachOverrideService.java": "class SlaBreachOverrideService {}\n",
            "src/main/java/com/mindarray/aiops/alerting/SlaPolicyStore.java": "class SlaPolicyStore {}\n",
            "src/test/resources/sla.json": "{}\n",
        },
        expected_file_patterns=["sla", "override"],
        description="SLA override planning query should map to alerting policy code.",
    ),
    GoldenQuery(
        id="plan_add_dedup_window",
        query="Add deduplication window to alert pipeline",
        expectation=QueryExpectation.GROUNDED,
        suite="plan_change",
        expected_intent_type="PLAN_INTENT",
        expected_quality_set=["STRONG", "WEAK"],
        expected_core_presence=True,
        expected_subsystem="alerting",
        repo_files={
            "src/main/java/com/mindarray/aiops/alerting/AlertDedupService.java": "class AlertDedupService {}\n",
            "src/main/java/com/mindarray/aiops/alerting/DedupWindowConfig.java": "class DedupWindowConfig {}\n",
            "logs/alert_pipeline.log": "dedup\n",
        },
        expected_file_patterns=["dedup", "alert"],
        description="Deduplication change request should hit alerting subsystem code.",
    ),

    # === NO-MATCH QUERIES ===
    GoldenQuery(
        id="no_match_quantum_handler",
        query="Where is quantum entanglement handler implemented?",
        expectation=QueryExpectation.NO_MATCH_VALID,
        suite="no_match",
        expected_intent_type="CODE_INTENT",
        expected_quality_set=["NO_MATCH"],
        expected_core_presence=False,
        repo_files={
            "src/main/java/com/mindarray/aiops/ingestion/EventProcessor.java": "class EventProcessor {}\n",
        },
        no_match_keywords=["no grounded", "no context", "ungrounded", "insufficient"],
        # PR-5: concrete code-location ask with no selected context → quality gate NO_MATCH (not INSUFFICIENT).
        description="Out-of-domain handler should be flagged as no-match.",
    ),
    GoldenQuery(
        id="no_match_k8s_autoscaler",
        query="Kubernetes pod autoscaler recommender in this repo",
        expectation=QueryExpectation.NO_MATCH_VALID,
        suite="no_match",
        expected_intent_type="GENERIC_INTENT",
        # Empty bundle + generic intent → WEAK (under-grounded), not a strict NO_MATCH label.
        expected_quality_set=["INSUFFICIENT", "NO_MATCH", "WEAK"],
        expected_core_presence=False,
        repo_files={
            "src/main/java/com/mindarray/aiops/topology/TopologyService.java": "class TopologyService {}\n",
        },
        no_match_keywords=["no grounded", "no context", "ungrounded", "insufficient"],
        description="Out-of-scope infra query: valid empty context; quality may be WEAK/INSUFFICIENT/NO_MATCH.",
    ),
    GoldenQuery(
        id="no_match_nonexistent_symbol",
        query="Where is NonExistentCorrelationSymbol999() used?",
        expectation=QueryExpectation.NO_MATCH_VALID,
        suite="no_match",
        expected_intent_type="CODE_INTENT",
        expected_quality_set=["NO_MATCH"],
        expected_core_presence=False,
        repo_files={
            "src/main/java/com/mindarray/aiops/correlation/CorrelationService.java": "class CorrelationService {}\n",
        },
        no_match_keywords=["no grounded", "no context", "ungrounded", "insufficient"],
        description="Nonexistent symbol should produce no-match with explicit justification.",
    ),

    # === ADVERSARIAL AMBIGUITY PROBES ===
    GoldenQuery(
        id="adversarial_engine",
        query="engine",
        expectation=QueryExpectation.EITHER_WITH_JUSTIFICATION,
        suite="adversarial",
        expected_intent_type="GENERIC_INTENT",
        expected_quality_set=["WEAK", "INSUFFICIENT", "NO_MATCH"],
        expected_core_presence=False,
        repo_files={
            "logs/engine.log": "engine failure\n",
            "tests/engine_test.py": "def test_engine(): pass\n",
            "src/main/java/com/mindarray/aiops/correlation/CorrelationEngine.java": "class CorrelationEngine {}\n",
        },
        description="Ambiguous single-token query must not be marked strong confidently.",
    ),
    GoldenQuery(
        id="adversarial_fix_bug",
        query="fix bug",
        expectation=QueryExpectation.EITHER_WITH_JUSTIFICATION,
        suite="adversarial",
        expected_intent_type="GENERIC_INTENT",
        expected_quality_set=["WEAK", "INSUFFICIENT", "NO_MATCH"],
        expected_core_presence=False,
        repo_files={
            "logs/app.log": "bug found\n",
            "tests/test_bugfix.py": "def test_bugfix(): pass\n",
            "src/main/java/com/mindarray/aiops/alerting/AlertService.java": "class AlertService {}\n",
        },
        description="Vague bug-fix probe should avoid false strong confidence.",
    ),
    GoldenQuery(
        id="adversarial_this_not_working",
        query="this not working",
        expectation=QueryExpectation.EITHER_WITH_JUSTIFICATION,
        suite="adversarial",
        expected_intent_type="DEBUG_INTENT",
        expected_quality_set=["WEAK", "INSUFFICIENT", "NO_MATCH"],
        expected_core_presence=False,
        repo_files={
            "logs/runtime.log": "not working\n",
            "src/main/java/com/mindarray/aiops/ingestion/IngestionRunner.java": "class IngestionRunner {}\n",
        },
        description="Low-information debug phrasing should stay weak/insufficient unless evidence is strong.",
    ),
    GoldenQuery(
        id="adversarial_in_this_system",
        query="in this system",
        expectation=QueryExpectation.EITHER_WITH_JUSTIFICATION,
        suite="adversarial",
        expected_intent_type="GENERIC_INTENT",
        expected_quality_set=["WEAK", "INSUFFICIENT", "NO_MATCH"],
        expected_core_presence=False,
        repo_files={
            "docs/readme.md": "system overview\n",
            "logs/system.log": "system info\n",
        },
        description="Generic phrasing should not be promoted as strong grounded evidence.",
    ),
    GoldenQuery(
        id="adversarial_update_logic",
        query="update logic",
        expectation=QueryExpectation.EITHER_WITH_JUSTIFICATION,
        suite="adversarial",
        expected_intent_type="PLAN_INTENT",
        expected_quality_set=["WEAK", "INSUFFICIENT", "NO_MATCH", "STRONG"],
        expected_core_presence=False,
        repo_files={
            "tests/update_logic_test.py": "def test_update_logic(): pass\n",
            "logs/update.log": "update logic\n",
            "src/main/java/com/mindarray/aiops/metrics/MetricsUpdater.java": "class MetricsUpdater {}\n",
        },
        description="Ambiguous plan phrase should be penalized if noisy evidence dominates.",
    ),
]


def get_grounded_queries() -> list[GoldenQuery]:
    """Return only queries expected to be grounded."""
    return [q for q in GOLDEN_QUERY_SUITE if q.expectation == QueryExpectation.GROUNDED]


def get_no_match_queries() -> list[GoldenQuery]:
    """Return only queries expected to be valid no-match."""
    return [q for q in GOLDEN_QUERY_SUITE if q.expectation == QueryExpectation.NO_MATCH_VALID]


def get_queries_by_suite(suite: str) -> list[GoldenQuery]:
    return [q for q in GOLDEN_QUERY_SUITE if q.suite == suite]
