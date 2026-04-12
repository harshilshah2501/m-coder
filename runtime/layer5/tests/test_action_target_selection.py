"""Tests for deterministic plan/action target selection."""

from __future__ import annotations

from runtime.layer5.retrieval.action_target_selection import select_plan_action_target


def test_select_prefers_log_collector_over_ui_handler_when_query_names_collector():
    ranked = [
        "motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java",
        "motadata/src/main/java/com/mindarray/api/APIServer.java",
        "motadata/src/main/java/com/mindarray/log/LogParser.java",
        "motadata/src/main/java/com/mindarray/log/LogCollector.java",
    ]
    q = (
        "Plan the impact of changing scheduled log collection intervals and "
        "event-bus request timeout behavior for collector execution"
    )
    assert select_plan_action_target(ranked, q) == ranked[3]


def test_select_prefers_metric_enricher_over_config_store_for_metric_poll_migration():
    ranked = [
        "motadata/src/main/java/com/mindarray/store/ObjectConfigStore.java",
        "motadata/src/main/java/com/mindarray/integration/LAMAIntegration.java",
        "motadata/src/main/java/com/mindarray/nms/MetricEnricher.java",
        "motadata/src/main/java/com/mindarray/nms/MetricPoller.java",
    ]
    q = (
        "Plan a migration for the event-driven component that processes raw metric poll results, "
        "computes derived metrics, and formats them for datastore write"
    )
    sel = select_plan_action_target(ranked, q)
    assert sel in (ranked[2], ranked[3])
    assert "ObjectConfigStore" not in sel


def test_select_keeps_rank_one_when_it_clearly_wins():
    ranked = [
        "motadata/src/main/java/com/mindarray/store/TopologyCacheStore.java",
        "motadata/src/main/java/com/mindarray/nms/TopologyEngine.java",
    ]
    q = "Rollout plan for topology cache store changes"
    assert select_plan_action_target(ranked, q) == ranked[0]
