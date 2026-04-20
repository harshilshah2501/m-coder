"""
Golden queries, determinism, and latency smoke for A5 lexical retrieval.
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

import pytest

from runtime.layer5.index import WorkspaceFileIndex, build_file_index
from runtime.layer5.retrieval import LexicalRetrievalConfig, normalize_query, retrieve_lexical
from runtime.layer5.retrieval.intent import CODE_INTENT
from runtime.layer5.retrieval.lexical import (
    _apply_engineering_intent_top_k_composition,
    _apply_top_k_core_correction,
    _is_core_aiops_hit,
    global_lexical_sorted_hits,
)
from runtime.layer5.retrieval.models import RetrievalHit
from runtime.layer5.workspace.identity import WorkspaceIdentity


def _touch(path: Path, text: str = "", mtime_ns: int = 1_000_000_000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    os.utime(path, ns=(mtime_ns, mtime_ns))


def _identity_for(root: Path) -> WorkspaceIdentity:
    root_s = str(root.resolve())
    return WorkspaceIdentity(
        canonical_root=root_s,
        identity_hash=WorkspaceIdentity.compute_identity_hash(root_s),
        original_input=root_s,
        path_type="posix",
        is_git_repo=False,
    )


def _index_fixture() -> tuple[tempfile.TemporaryDirectory[str], WorkspaceFileIndex]:
    """Synthetic tree mimicking discoverable Layer-5-ish paths."""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    _touch(
        root / "runtime" / "layer5" / "workspace" / "resolver.py",
        "class WorkspaceResolver resolves the canonical workspace root for callers.",
    )
    _touch(
        root / "runtime" / "layer5" / "index" / "builder.py",
        "def build_file_index walks the tree and returns WorkspaceFileIndex.",
    )
    _touch(
        root / "runtime" / "layer5" / "workspace" / "path_normalizer.py",
        "PathNormalizer converts windows paths to normalized posix forms.",
    )
    _touch(
        root / "runtime" / "layer5" / "api" / "skeleton.py",
        "Layer5ApiSkeleton serves healthz and workspace resolve endpoints.",
    )
    ident = _identity_for(root)
    idx = build_file_index(ident)
    return tmp, idx


class TestQueryNormalization:
    def test_normalize_query_sorted_and_filtered(self):
        assert normalize_query("Workspace  RESOLVER!") == ("resolver", "workspace")
        assert normalize_query("a b") == ()  # min len 2
        assert normalize_query("") == ()

    def test_normalize_query_recall_stem_expansions(self):
        t = set(normalize_query("metric poll process"))
        assert "polling" in t and "poller" in t
        assert "processor" in t and "processing" in t
        t2 = set(normalize_query("log collection"))
        assert "collect" in t2 and "collector" in t2


class TestGoldenQueries:
    @pytest.fixture
    def golden_index(self):
        tmp, idx = _index_fixture()
        yield idx
        tmp.cleanup()

    def test_workspace_resolver_ranks_resolver_py(self, golden_index):
        r = retrieve_lexical(golden_index, "workspace resolver", top_k=3)
        paths = [h.relative_path for h in r.hits]
        assert "runtime/layer5/workspace/resolver.py" in paths
        assert paths[0] == "runtime/layer5/workspace/resolver.py"

    def test_file_index_builder_ranks_builder(self, golden_index):
        r = retrieve_lexical(golden_index, "file index build", top_k=2)
        assert r.hits[0].relative_path == "runtime/layer5/index/builder.py"

    def test_path_normalizer_query(self, golden_index):
        r = retrieve_lexical(golden_index, "path normalizer windows", top_k=2)
        assert r.hits[0].relative_path == "runtime/layer5/workspace/path_normalizer.py"

    def test_breakdown_sums_to_score(self, golden_index):
        cfg = LexicalRetrievalConfig(enable_deterministic_rank_nudge=False)
        r = retrieve_lexical(golden_index, "resolver", top_k=1, config=cfg)
        h = r.hits[0]
        assert h.score == sum(h.breakdown.values())


class TestDeterminism:
    def test_identical_results_across_runs(self):
        tmp, idx = _index_fixture()
        try:
            cfg = LexicalRetrievalConfig(read_file_contents=True)
            a = retrieve_lexical(idx, "workspace resolver", 4, cfg)
            b = retrieve_lexical(idx, "workspace resolver", 4, cfg)
            assert [h.relative_path for h in a.hits] == [h.relative_path for h in b.hits]
            assert [h.score for h in a.hits] == [h.score for h in b.hits]
        finally:
            tmp.cleanup()

    def test_tie_break_by_relative_path(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(root / "z" / "match.txt", "alpha beta gamma repeat repeat")
            _touch(root / "a" / "match.txt", "alpha beta gamma repeat repeat")
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(idx, "repeat gamma", top_k=2)
            paths = [h.relative_path for h in r.hits]
            assert paths == sorted(paths)
            assert paths[0] == "a/match.txt"

    def test_empty_query_returns_first_k_by_path_order(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(root / "b.txt", "x")
            _touch(root / "a.txt", "x")
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(idx, "   ", top_k=1)
            assert r.hits[0].relative_path == "a.txt"


class TestLexicalRetrievalLatencySmoke:
    """
    Latency snapshot (honest, coarse): on a small tree, repeated retrieval stays cheap.

    Last local run target: well under 100ms total for 40 calls (path+content).
    """

    def test_lexical_retrieval_latency_smoke(self):
        tmp, idx = _index_fixture()
        try:
            cfg = LexicalRetrievalConfig(read_file_contents=True)
            n = 40
            t0 = time.perf_counter()
            for _ in range(n):
                retrieve_lexical(idx, "workspace resolver endpoints", top_k=4, config=cfg)
            elapsed = time.perf_counter() - t0
            per_ms = (elapsed / n) * 1000.0
            assert elapsed < 2.0, f"40 retrievals took {elapsed:.3f}s (~{per_ms:.2f}ms each)"
        finally:
            tmp.cleanup()


class TestPolicyRanking:
    def test_noise_suppression_engine_query(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(root / "tests" / "engine_test.py", "engine engine")
            _touch(root / "logs" / "engine.log", "engine failure")
            _touch(
                root / "src" / "main" / "java" / "com" / "mindarray" / "aiops" / "ingestion" / "EngineProcessor.java",
                "class EngineProcessor { void processEngine() {} }",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(idx, "engine", top_k=3, config=LexicalRetrievalConfig())
            top = [h.relative_path for h in r.hits]
            assert top[0].endswith("EngineProcessor.java")

    def test_core_dominance_for_alert_correlation_engine(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(root / "tests" / "alert_correlation_test.py", "alert correlation engine")
            _touch(
                root / "src" / "main" / "java" / "com" / "mindarray" / "aiops" / "alerting" / "AlertProcessor.java",
                "class AlertProcessor { void runCorrelationEngine() {} }",
            )
            _touch(
                root / "src" / "main" / "java" / "com" / "mindarray" / "aiops" / "correlation" / "AlertCorrelationEngine.java",
                "class AlertCorrelationEngine { void correlateAlerts() {} }",
            )
            _touch(
                root / "src" / "main" / "java" / "com" / "mindarray" / "aiops" / "correlation" / "CorrelationService.java",
                "class CorrelationService { void correlate() {} }",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(idx, "alert correlation engine", top_k=3, config=LexicalRetrievalConfig())
            top3 = [h.relative_path.lower() for h in r.hits[:3]]
            assert any("src/main/java/com/mindarray/aiops/" in p for p in top3)

    def test_subsystem_boost_topology_anomaly(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(
                root / "src" / "main" / "java" / "com" / "mindarray" / "aiops" / "topology" / "TopologyAnomalyDetector.java",
                "class TopologyAnomalyDetector { void detectAnomaly() {} }",
            )
            _touch(
                root / "src" / "main" / "java" / "com" / "mindarray" / "aiops" / "metrics" / "MetricWriter.java",
                "class MetricWriter { void anomalyMetric() {} }",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(idx, "topology anomaly", top_k=2, config=LexicalRetrievalConfig())
            assert r.hits[0].relative_path.endswith("TopologyAnomalyDetector.java")

    def test_policy_determinism_same_query_same_order(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(
                root / "src" / "main" / "java" / "com" / "mindarray" / "aiops" / "correlation" / "CorrelationService.java",
                "class CorrelationService { void correlate() {} }",
            )
            _touch(root / "tests" / "correlation_test.py", "correlation service")
            ident = _identity_for(root)
            idx = build_file_index(ident)
            cfg = LexicalRetrievalConfig()
            a = retrieve_lexical(idx, "correlation service", top_k=2, config=cfg)
            b = retrieve_lexical(idx, "correlation service", top_k=2, config=cfg)
            assert [h.relative_path for h in a.hits] == [h.relative_path for h in b.hits]

    def test_topology_anomaly_detection_phrase_prefers_core(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            core_path = (
                "src/main/java/com/mindarray/aiops/topology/TopologyAnomalyDetector.java"
            )
            _touch(
                root / core_path,
                "class TopologyAnomalyDetector { void detectAnomaly() {} }",
            )
            _touch(
                root / "src/main/java/com/mindarray/aiops/metrics/MetricWriter.java",
                "class MetricWriter { void anomalyMetric() {} }",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(
                idx,
                "How does topology anomaly detection work?",
                top_k=2,
                config=LexicalRetrievalConfig(),
            )
            assert r.hits[0].relative_path.endswith("TopologyAnomalyDetector.java")

    def test_global_lexical_sorted_hits_prefix_matches_retrieve_lexical_order(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(root / "a.py", "alpha beta gamma")
            _touch(root / "b.py", "alpha delta")
            ident = _identity_for(root)
            idx = build_file_index(ident)
            cfg = LexicalRetrievalConfig()
            full = global_lexical_sorted_hits(idx, "alpha beta", cfg)
            r = retrieve_lexical(idx, "alpha beta", top_k=2, config=cfg)
            assert [h.relative_path for h in full[:2]] == [h.relative_path for h in r.hits]

    def test_top_k_core_correction_unit_swap(self):
        """Direct test: correction inserts a core hit into the top-3 window."""
        hits = [
            RetrievalHit("logs/a.log", 100, {"path_substrings": 0, "basename_substrings": 0, "content_substrings": 0}, None),
            RetrievalHit("tests/b.py", 90, {"path_substrings": 0, "basename_substrings": 0, "content_substrings": 0}, None),
            RetrievalHit("vendor/c.js", 80, {"path_substrings": 0, "basename_substrings": 0, "content_substrings": 0}, None),
            RetrievalHit(
                "src/main/java/com/mindarray/aiops/topology/Core.java",
                10,
                {"path_substrings": 0, "basename_substrings": 0, "content_substrings": 0},
                None,
            ),
        ]
        out = _apply_top_k_core_correction(hits, top_k=4)
        top3 = [h.relative_path for h in out[:3]]
        assert "src/main/java/com/mindarray/aiops/topology/Core.java" in top3

    def test_top_k_core_correction_noise_dominated_query(self):
        """Heavy noise token overlap cannot keep core out of the top-3 window when correction is on."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            blob = "topology anomaly detection " * 80
            _touch(root / "logs" / "noise.log", blob)
            _touch(root / "tests" / "t.py", blob)
            _touch(root / "vendor" / "v.js", blob)
            core_rel = (
                "src/main/java/com/mindarray/aiops/topology/TopologyAnomalyDetector.java"
            )
            _touch(root / core_rel, "class TopologyAnomalyDetector {}\n")
            ident = _identity_for(root)
            idx = build_file_index(ident)
            q = "topology anomaly detection"
            without = retrieve_lexical(
                idx,
                q,
                top_k=4,
                config=LexicalRetrievalConfig(
                    enable_top_k_core_correction=False,
                    code_debug_intent=False,
                ),
            )
            with_corr = retrieve_lexical(
                idx,
                q,
                top_k=4,
                config=LexicalRetrievalConfig(
                    enable_top_k_core_correction=True,
                    code_debug_intent=False,
                ),
            )
            assert not any(
                h.relative_path.endswith("TopologyAnomalyDetector.java") for h in without.hits[:3]
            )
            assert any(
                h.relative_path.endswith("TopologyAnomalyDetector.java") for h in with_corr.hits[:3]
            )


class TestSlice3CodeIntentContentGating:
    def test_repeated_tokens_in_log_do_not_outrank_main_java_under_code_intent(self):
        """Noise-class files must not win top-1 on raw content repetition (PR-6 Slice 3)."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            blob = "topology anomaly graph node edge metric collector pipeline " * 120
            _touch(root / "motadata" / "logs" / "noise.log", blob)
            _touch(
                root
                / "motadata"
                / "test-plugin-metrics"
                / "oracle_index_poll.json",
                '{"topology": "' + ("anomaly " * 200) + '"}',
            )
            java_rel = (
                "motadata/src/main/java/com/mindarray/nms/TopologyEngine.java"
            )
            _touch(
                root / java_rel,
                "package com.mindarray.nms;\n"
                "public class TopologyEngine { void refreshTopologyGraph() {} }\n",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(
                idx,
                "Trace topology anomaly false positives in node graph",
                top_k=3,
                config=LexicalRetrievalConfig(include_score_diagnostics=True),
            )
            assert r.hits[0].relative_path.endswith("TopologyEngine.java")
            d0 = r.hits[0].diagnostics or {}
            assert d0.get("code_intent") == 1
            assert d0.get("main_java_bonus", 0) > 0

    def test_code_intent_gating_off_preserves_content_rich_noise_leading(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            blob = "foobarxy " * 200
            _touch(root / "motadata" / "logs" / "huge.log", blob)
            java_rel = "motadata/src/main/java/com/mindarray/nms/TopologyEngine.java"
            _touch(root / java_rel, "package com.mindarray.nms;\npublic class TopologyEngine {}\n")
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(
                idx,
                "foobarxy",
                top_k=2,
                config=LexicalRetrievalConfig(code_debug_intent=False),
            )
            assert r.hits[0].relative_path.endswith(".log")

    def test_classify_db_files_as_generated_metrics_data(self):
        from runtime.layer5.retrieval import classify_file

        p = classify_file("motadata/db-files/template-widgets/oceanstor.json")
        assert p.file_class == "generated_metrics_data"

    def test_diagnostics_include_gating_fields_when_enabled(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(root / "motadata" / "logs" / "x.log", "debug engine failure " * 50)
            _touch(
                root / "motadata/src/main/java/com/mindarray/aiops/EngineX.java",
                "package com.mindarray.aiops;\npublic class EngineX { void debugEngine() {} }\n",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(
                idx,
                "debug engine failure",
                top_k=8,
                config=LexicalRetrievalConfig(include_score_diagnostics=True),
            )
            log_hit = next(h for h in r.hits if h.relative_path.endswith(".log"))
            assert (log_hit.diagnostics or {}).get("noise_content_suppressed") == 1
            assert (log_hit.diagnostics or {}).get("content") == 0


class TestSlice4OwnerDisambiguation:
    """PR-6 Slice 4: support-style basenames + basename/query specificity."""

    def test_constants_java_does_not_outrank_behavioral_owner(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            blob = "topology anomaly graph node edge metric trace detector false positive " * 80
            _touch(
                root / "motadata/src/main/java/com/mindarray/viz/VisualizationConstants.java",
                "package com.mindarray.viz;\npublic class VisualizationConstants {\n" + blob + "\n}\n",
            )
            _touch(
                root / "motadata/src/main/java/com/mindarray/nms/TopologyEngine.java",
                "package com.mindarray.nms;\n"
                "public class TopologyEngine {\n"
                "  void refreshTopologyGraph() { /* topology anomaly */ }\n"
                "}\n",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(
                idx,
                "Trace topology anomaly detector false positives in node graph",
                top_k=2,
                config=LexicalRetrievalConfig(include_score_diagnostics=True),
            )
            assert r.hits[0].relative_path.endswith("TopologyEngine.java")
            d0 = r.hits[0].diagnostics or {}
            assert d0.get("basename_specificity", 0) >= 0
            const_hit = next(
                h for h in r.hits if "VisualizationConstants" in h.relative_path
            )
            assert (const_hit.diagnostics or {}).get("support_file_demotion", 0) > 0

    def test_alert_correlation_beats_availability_when_query_emphasizes_alert(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(
                root
                / "motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java",
                "package com.mindarray.aiops.correlation;\n"
                "public class AlertCorrelationEngine {\n"
                "  public void correlateDuplicateIncidents() {}\n"
                "}\n",
            )
            _touch(
                root
                / "motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java",
                "package com.mindarray.aiops;\n"
                "public class AvailabilityCorrelationEngine {\n"
                "  public void correlateDuplicateIncidents() {}\n"
                "}\n",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(
                idx,
                "Debug alert correlation engine failing to correlate duplicate incidents",
                top_k=2,
                config=LexicalRetrievalConfig(include_score_diagnostics=True),
            )
            assert r.hits[0].relative_path.endswith("AlertCorrelationEngine.java")
            d0 = r.hits[0].diagnostics or {}
            assert d0.get("basename_specificity", 0) > 0

    def test_support_style_basename_is_detected(self):
        from runtime.layer5.retrieval import is_support_style_java_basename

        assert is_support_style_java_basename("NMSConstants.java") is True
        assert is_support_style_java_basename("MotadataConfigUtil.java") is True
        assert is_support_style_java_basename("TopologyEngine.java") is False


class TestSlice5MandatoryTop1Closure:
    """PR-6 Slice 5: topic-gated generic facade content cap + duplicate-incident owner signals."""

    def test_topology_focus_caps_generic_eventbus_handler_content(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            blob = "topology anomaly graph node edge detector false positive trace metric " * 120
            _touch(
                root / "motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java",
                "package com.mindarray.eventbus;\npublic class UIActionEventHandler {\n" + blob + "\n}\n",
            )
            te_body = "topology anomaly graph node detector false positive trace metric edge " * 25
            _touch(
                root / "motadata/src/main/java/com/mindarray/nms/TopologyEngine.java",
                "package com.mindarray.nms;\n"
                "public class TopologyEngine {\n"
                f"  void refreshTopologyGraph() {{ {te_body} }}\n"
                "}\n",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(
                idx,
                "Trace topology anomaly detector false positives in node graph",
                top_k=2,
                config=LexicalRetrievalConfig(
                    include_score_diagnostics=True,
                    code_intent_generic_facade_content_cap=100,
                ),
            )
            assert r.hits[0].relative_path.endswith("TopologyEngine.java")
            uia = next(h for h in r.hits if "UIActionEventHandler" in h.relative_path)
            assert (uia.diagnostics or {}).get("generic_facade_content_trimmed", 0) > 0
            assert (uia.diagnostics or {}).get("facade_cap_basename_or_symbol_owner_signal", 0) == 0

    def test_ingestion_focus_caps_generic_eventbus_handler_content(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            blob = "ingestion pipeline parser metrics collector timeout poll ingest " * 80
            _touch(
                root / "motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java",
                "package com.mindarray.eventbus;\npublic class UIActionEventHandler {\n" + blob + "\n}\n",
            )
            mp_body = "ingestion pipeline parser metrics collector timeout poll ingest " * 25
            _touch(
                root / "motadata/src/main/java/com/mindarray/aiops/ingestion/MetricsParser.java",
                "package com.mindarray.aiops.ingestion;\n"
                "public class MetricsParser {\n"
                f"  void parseMetricsPipeline() {{ {mp_body} }}\n"
                "}\n",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(
                idx,
                "Investigate ingestion pipeline parser timeout for metrics collector",
                top_k=2,
                config=LexicalRetrievalConfig(
                    include_score_diagnostics=True,
                    code_intent_generic_facade_content_cap=100,
                ),
            )
            assert r.hits[0].relative_path.endswith("MetricsParser.java")
            uia = next(h for h in r.hits if "UIActionEventHandler" in h.relative_path)
            assert (uia.diagnostics or {}).get("generic_facade_content_trimmed", 0) > 0

    def test_duplicate_incident_query_prefers_core_aiops_over_integration(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(
                root / "motadata/src/main/java/com/mindarray/integration/ServiceNowIntegration.java",
                "package com.mindarray.integration;\n"
                "public class ServiceNowIntegration {\n"
                "  void duplicate() { incident incident incident handling handling handling }\n"
                "}\n",
            )
            _touch(
                root / "motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java",
                "package com.mindarray.aiops;\n"
                "public class DependencyQueryProcessor {\n"
                "  void onIncident() {}\n"
                "}\n",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(
                idx,
                "duplicate incident handling",
                top_k=2,
                config=LexicalRetrievalConfig(include_score_diagnostics=True),
            )
            assert r.hits[0].relative_path.endswith("DependencyQueryProcessor.java")
            d0 = r.hits[0].diagnostics or {}
            assert d0.get("duplicate_incident_core_boost", 0) > 0
            sni = next(h for h in r.hits if "ServiceNowIntegration" in h.relative_path)
            assert (sni.diagnostics or {}).get("generic_integration_demotion", 0) > 0

    def test_ingestion_focus_applies_log_parser_demotion_diagnostic(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            lp_blob = "parser metrics collector pipeline ingestion timeout ingest " * 40
            _touch(
                root / "motadata/src/main/java/com/mindarray/log/LogParser.java",
                "package com.mindarray.log;\npublic class LogParser {\n" + lp_blob + "\n}\n",
            )
            dqp_body = "ingestion pipeline parser metrics collector timeout " * 15
            _touch(
                root / "motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java",
                "package com.mindarray.aiops;\npublic class DependencyQueryProcessor {\n"
                + dqp_body
                + "\n}\n",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(
                idx,
                "Investigate ingestion pipeline parser timeout for metrics collector",
                top_k=5,
                config=LexicalRetrievalConfig(include_score_diagnostics=True),
            )
            lp_hit = next(h for h in r.hits if "LogParser" in h.relative_path)
            assert (lp_hit.diagnostics or {}).get("ingestion_log_parser_demotion", 0) > 0

    def test_correlation_only_query_does_not_apply_facade_cap_to_event_handler(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            blob = "topology graph anomaly correlation alert " * 40
            _touch(
                root / "motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java",
                "package com.mindarray.eventbus;\npublic class UIActionEventHandler {\n" + blob + "\n}\n",
            )
            _touch(
                root / "motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java",
                "package com.mindarray.aiops;\npublic class AvailabilityCorrelationEngine {}\n",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(
                idx,
                "Correlation issue in alerts",
                top_k=2,
                config=LexicalRetrievalConfig(include_score_diagnostics=True),
            )
            assert r.hits[0].relative_path.endswith("UIActionEventHandler.java")
            assert (r.hits[0].diagnostics or {}).get("generic_facade_content_trimmed", 0) == 0

    def test_topology_named_class_query_prefers_owner_over_metric_manager_keyword_mass(self):
        """B1: *Metric* in a basename must not exempt broad supporting files from topic caps."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            noise = "topology graph engine node edge cache store " * 200
            _touch(
                root
                / "motadata/src/main/java/com/mindarray/visualization/VisualizationMetricManager.java",
                "package com.mindarray.visualization;\npublic class VisualizationMetricManager {\n"
                + noise
                + "\n}\n",
            )
            _touch(
                root / "motadata/src/main/java/com/mindarray/store/TopologyCacheStore.java",
                "package com.mindarray.store;\npublic class TopologyCacheStore {\n"
                "  // small owner body\n}\n",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(
                idx,
                "Where is TopologyCacheStore used by topology graph engine?",
                top_k=4,
                config=LexicalRetrievalConfig(include_score_diagnostics=True),
            )
            assert r.hits[0].relative_path.endswith("TopologyCacheStore.java")
            mm = next(h for h in r.hits if "VisualizationMetricManager" in h.relative_path)
            assert (mm.diagnostics or {}).get("topic_focus_supporting_content_trimmed", 0) > 0

    def test_class_relationship_api_query_prefers_api_declaration_owner(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            heavy = "which class base all apis is the for " * 280
            _touch(
                root / "motadata/src/main/java/com/mindarray/visualization/VisualizationConstants.java",
                "package com.mindarray.visualization;\npublic final class VisualizationConstants {\n"
                + heavy
                + "\n}\n",
            )
            _touch(
                root / "motadata/src/main/java/com/mindarray/api/APIServer.java",
                "package com.mindarray.api;\npublic class APIServer extends AbstractVerticle {\n}\n",
            )
            _touch(
                root / "motadata/src/main/java/com/mindarray/nms/DiscoveryEngine.java",
                "package com.mindarray.nms;\npublic class DiscoveryEngine extends Verticle {\n}\n",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(
                idx,
                "Which class is the base class for all APIs?",
                top_k=3,
                config=LexicalRetrievalConfig(include_score_diagnostics=True),
            )
            assert r.hits[0].relative_path.endswith("APIServer.java")
            assert (r.hits[0].diagnostics or {}).get("class_relationship_boost", 0) > 0

    def test_non_relationship_api_query_does_not_apply_class_relationship_boost(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(
                root / "motadata/src/main/java/com/mindarray/api/APIServer.java",
                "package com.mindarray.api;\npublic class APIServer extends AbstractVerticle {\n}\n",
            )
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(
                idx,
                "How does API server request routing work?",
                top_k=1,
                config=LexicalRetrievalConfig(include_score_diagnostics=True),
            )
            assert (r.hits[0].diagnostics or {}).get("class_relationship_boost", 0) == 0


def test_engineering_intent_top_k_composition_promotes_cores_without_touching_rank0():
    """Deterministic composition: pull core_aiops_code from below top-k into slots 1..k-1 up to target."""

    def H(p: str, s: int) -> RetrievalHit:
        return RetrievalHit(
            p,
            s,
            {"path_substrings": s, "basename_substrings": 0, "content_substrings": 0},
        )

    support = "motadata/src/main/java/com/mindarray/api/Support{}.java"
    core = "motadata/src/main/java/com/mindarray/aiops/Core{}.java"
    # Lexical order: 12 high-scoring supporting files first, then cores (weaker scores).
    full: list[RetrievalHit] = [H(support.format(i), 5000 - i) for i in range(12)]
    full.extend(H(core.format(i), 100 - i) for i in range(6))
    tops = list(full[:12])
    assert sum(1 for h in tops if _is_core_aiops_hit(h)) == 0

    out = _apply_engineering_intent_top_k_composition(
        tops,
        full,
        12,
        CODE_INTENT,
        target_core=4,
    )
    assert out[0].relative_path == tops[0].relative_path
    assert sum(1 for h in out if _is_core_aiops_hit(h)) == 4
