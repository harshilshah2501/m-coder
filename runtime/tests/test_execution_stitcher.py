from __future__ import annotations

from datetime import datetime, timezone

from runtime.ask_service.execution_stitcher import stitch_first_hop
from runtime.context.contracts import ContextBundle, ContextBundleLimits, ContextBundleProvenance, ContextItem


def _bundle(items: list[ContextItem]) -> ContextBundle:
    return ContextBundle(
        task_id="t",
        revision="r",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        items=items,
        limits=ContextBundleLimits(max_files=10, max_bytes=100_000, truncated=False),
        provenance=ContextBundleProvenance(
            root_path="/repo",
            selectors=["test"],
            requested_files=[],
            symbol_hints=[],
        ),
    )


def test_stitch_first_hop_resolves_same_file_helper():
    b = _bundle(
        [
            ContextItem(
                path="src/main/java/com/mindarray/api/APIServer.java",
                content=(
                    "public class APIServer {\n"
                    "  public void start() {\n"
                    "    registerRoutes();\n"
                    "  }\n"
                    "  private void registerRoutes() {\n"
                    "    router.route(\"/\").handler(this::run);\n"
                    "  }\n"
                    "}\n"
                ),
                byte_size=0,
                selection_reason="query_token_substring_anchor",
            )
        ]
    )
    out = stitch_first_hop(
        bundle=b,
        owner_file="src/main/java/com/mindarray/api/APIServer.java",
        owner_class="APIServer",
        owner_method="start",
        owner_method_window="public void start() {\n registerRoutes();\n}",
        collaborator_paths=[],
    )
    assert out.stitched is True
    assert out.edge_type == "direct_call"
    assert out.target_method == "registerRoutes"
    assert out.stitched_edge_count == 1
    assert out.call_site_candidates_detected is True
    assert out.call_site_candidate_count >= 1
    assert out.call_site_resolution_state == "resolved_visible"
    assert out.resolved_from_method == "start"
    assert out.resolved_to_method == "registerRoutes"


def test_stitch_first_hop_reports_partial_when_no_target_method_visible():
    b = _bundle(
        [
            ContextItem(
                path="src/main/java/com/mindarray/notification/NotificationEngine.java",
                content="public class NotificationEngine { public void start() { EmailNotification.send(\"x\"); } }",
                byte_size=0,
                selection_reason="query_token_substring_anchor",
            )
        ]
    )
    out = stitch_first_hop(
        bundle=b,
        owner_file="src/main/java/com/mindarray/notification/NotificationEngine.java",
        owner_class="NotificationEngine",
        owner_method="start",
        owner_method_window="public void start() { EmailNotification.send(\"x\"); }",
        collaborator_paths=["src/main/java/com/mindarray/notification/EmailNotification.java"],
    )
    assert out.stitched is False
    assert out.edge_type == "none"
    assert out.confidence == "partial"
    assert out.call_site_candidates_detected is True
    assert out.call_site_candidate_count >= 1
    assert out.call_site_resolution_state == "unresolved"


def test_stitch_first_hop_reports_none_when_no_call_sites():
    b = _bundle(
        [
            ContextItem(
                path="src/main/java/com/mindarray/store/AbstractConfigStore.java",
                content="public class AbstractConfigStore { public JsonObject getItem(long id) { return null; } }",
                byte_size=0,
                selection_reason="query_token_substring_anchor",
            )
        ]
    )
    out = stitch_first_hop(
        bundle=b,
        owner_file="src/main/java/com/mindarray/store/AbstractConfigStore.java",
        owner_class="AbstractConfigStore",
        owner_method="getItem",
        owner_method_window="public JsonObject getItem(long id) { return null; }",
        collaborator_paths=[],
    )
    assert out.stitched is False
    assert out.call_site_candidates_detected is False
    assert out.call_site_candidate_count == 0
    assert out.call_site_resolution_state == "none"
