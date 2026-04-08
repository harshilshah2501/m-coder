package ai.motadata.plugin.ask

import ai.motadata.plugin.bridge.AskPluginRouting
import ai.motadata.plugin.bridge.RuntimeOutcome
import ai.motadata.plugin.bridge.RuntimeResponse
import ai.motadata.plugin.bridge.RuntimeUi
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class AskResultDialogMessageTest {

    private fun planTruthMeta(requestId: String = "r1", traceId: String = "trace-plan-1"): Map<String, Any?> = mapOf(
        "trace_id" to traceId,
        "routing_mode" to "plan_only",
        "plugin_ask_routing" to AskPluginRouting.V1_SUCCESS,
        "plugin_ask_routing_decision" to mapOf(
            "attempt" to "v1",
            "result" to "success",
            "trace_id" to traceId,
            "request_id" to requestId,
        ),
    )

    private fun explainTruthMeta(): Map<String, Any?> = mapOf(
        "trace_id" to "trace-explain-1",
        "routing_mode" to "explain_debug",
        "plugin_ask_routing" to AskPluginRouting.V1_SUCCESS,
        "plugin_ask_routing_decision" to mapOf(
            "attempt" to "v1",
            "result" to "success",
            "trace_id" to "trace-explain-1",
            "request_id" to "r2",
        ),
    )

    @Test
    fun `plan only message includes evidence quality and reasons`() {
        val response = RuntimeResponse(
            outcome = RuntimeOutcome.BOUNDED_ALLOW,
            requestId = "r1",
            ui = RuntimeUi(title = "T", message = "M", severity = "info"),
            metadata = planTruthMeta() + mapOf(
                "backend_metadata" to mapOf(
                    "evidence_quality" to "WEAK",
                    "intent_type" to "CODE_INTENT",
                    "quality_reasons" to listOf("NO_SYMBOL_MATCH", "OTHER"),
                    "dominance_metrics" to mapOf("noise_in_top_k_pct" to 0.1),
                    "policy_version" to "quality_gate.v1",
                ),
                "context_resolution" to mapOf(
                    "requested_repo_root" to "/x",
                    "effective_repo_root" to "/y",
                    "fallback_used" to true,
                ),
                "plan_summary" to mapOf("steps" to listOf("step a")),
                "context_bundle" to mapOf(
                    "revision" to "rev",
                    "files" to emptyList<Any>(),
                    "selectors_used" to emptyList<Any>(),
                ),
            )
        )
        val full = buildAskResultDialogMessage("q?", response)
        val summary = buildAskResultSummaryMessage("q?", response)
        assertTrue(!summary.contains("Response provenance (backend)"), summary)
        assertTrue(!summary.contains("Dominance metrics (backend):"), summary)
        assertTrue(summary.contains("Query: q?"), summary)
        assertTrue(summary.contains("quality=WEAK"), summary)
        assertTrue(summary.contains("request_id: r1"), summary)

        val msg = full
        assertTrue(msg.startsWith("request_id: r1"), msg)
        assertTrue(msg.contains("Evidence quality: WEAK"), msg)
        assertTrue(msg.contains("intent_type: CODE_INTENT"), msg)
        assertTrue(msg.indexOf("intent_type: CODE_INTENT") < msg.indexOf("Quality reasons"), msg)
        assertTrue(msg.contains("NO_SYMBOL_MATCH"), msg)
        assertTrue(msg.contains("Dominance metrics (backend):"), msg)
        assertTrue(msg.contains("Context resolution:"), msg)
        assertTrue(msg.contains("effective_repo_root: /y"), msg)
        assertTrue(msg.indexOf("Evidence quality: WEAK") < msg.indexOf("Response provenance"), msg)
        assertTrue(msg.indexOf("Response provenance") < msg.indexOf("PLAN ONLY"), msg)
    }

    @Test
    fun `explain debug message includes evidence quality before summary`() {
        val response = RuntimeResponse(
            outcome = RuntimeOutcome.BOUNDED_ALLOW,
            requestId = "r2",
            ui = null,
            metadata = explainTruthMeta() + mapOf(
                "backend_metadata" to mapOf(
                    "evidence_quality" to "STRONG",
                    "intent_type" to "EXPLAIN_DEBUG",
                    "quality_reasons" to listOf("OK"),
                ),
                "explain_debug" to mapOf(
                    "summary" to "Model says things.",
                ),
                "evidence_first_meta" to mapOf(
                    "ask_path" to "v1_evidence",
                    "context_source" to "layer5.evidence_bundle.v1",
                ),
            )
        )
        val msg = buildAskResultDialogMessage("q?", response)
        assertTrue(msg.startsWith("request_id: r2"), msg)
        assertTrue(msg.contains("Evidence quality: STRONG"), msg)
        assertTrue(msg.contains("intent_type: EXPLAIN_DEBUG"), msg)
        assertTrue(msg.contains("Model says things."), msg)
        assertTrue(msg.contains("ask_path: v1_evidence"), msg)
        assertTrue(msg.indexOf("intent_type: EXPLAIN_DEBUG") < msg.indexOf("Response provenance"), msg)
        assertTrue(msg.indexOf("Evidence quality: STRONG") < msg.indexOf("Response provenance"), msg)
        assertTrue(msg.indexOf("Response provenance") < msg.indexOf("Explain/Debug"), msg)
        assertTrue(msg.indexOf("Response provenance") < msg.indexOf("Summary"), msg)
    }

    @Test
    fun `explain debug message order is calibration then provenance then body`() {
        val response = RuntimeResponse(
            outcome = RuntimeOutcome.BOUNDED_ALLOW,
            requestId = "r2b",
            ui = null,
            metadata = explainTruthMeta() + mapOf(
                "backend_metadata" to mapOf(
                    "evidence_quality" to "WEAK",
                    "intent_type" to "CODE_INTENT",
                    "quality_reasons" to listOf("LOW_CORE_RATIO"),
                    "dominance_metrics" to mapOf("code_in_top_k_pct" to 0.5),
                    "policy_version" to "quality_gate.v1",
                ),
                "context_resolution" to mapOf(
                    "context_source" to "layer5.evidence_bundle.v1",
                    "no_repo_filesystem" to true,
                ),
                "evidence_first_meta" to mapOf(
                    "ask_path" to "v1_evidence",
                    "no_context_engine" to true,
                ),
                "explain_debug" to mapOf(
                    "summary" to "BODY_ANCHOR_EXPLAIN_DEBUG",
                    "confidence_limits" to "CAL_LIMITS_ANCHOR",
                ),
            ),
        )
        val msg = buildAskResultDialogMessage("q?", response)
        val iCal = msg.indexOf("Grounding calibration (backend)")
        val iProv = msg.indexOf("Response provenance (backend)")
        val iExplainHeader = msg.indexOf("Explain/Debug — PLAN ONLY")
        val iSummary = msg.indexOf("BODY_ANCHOR_EXPLAIN_DEBUG")
        assertTrue(iCal >= 0, msg)
        assertTrue(iProv > iCal, msg)
        assertTrue(iExplainHeader > iProv, msg)
        assertTrue(iSummary > iExplainHeader, msg)
        assertTrue(msg.contains("Evidence quality: WEAK"), msg)
        assertTrue(msg.contains("Quality reasons:"), msg)
        assertTrue(msg.contains("LOW_CORE_RATIO"), msg)
        assertTrue(msg.contains("context_source: layer5.evidence_bundle.v1"), msg)
        assertTrue(msg.contains("ask_path: v1_evidence"), msg)
        assertTrue(msg.contains("CAL_LIMITS_ANCHOR"), msg)
    }

    @Test
    fun `plan only includes v1 ask_path and bundle from backend fields`() {
        val response = RuntimeResponse(
            outcome = RuntimeOutcome.BOUNDED_ALLOW,
            requestId = "r3",
            ui = null,
            metadata = planTruthMeta(requestId = "r3", traceId = "trace-r3") + mapOf(
                "backend_metadata" to mapOf("evidence_quality" to "STRONG", "quality_reasons" to emptyList<String>()),
                "evidence_bundle" to mapOf("schema_version" to "layer5.evidence_bundle.v1", "entries" to emptyList<Any>()),
                "evidence_first_meta" to mapOf(
                    "ask_path" to "v1_evidence",
                    "context_source" to "layer5.evidence_bundle.v1",
                    "no_context_engine" to true,
                ),
                "plan_summary" to mapOf("steps" to listOf("one")),
                "context_bundle" to mapOf(
                    "revision" to "r",
                    "files" to emptyList<Any>(),
                    "selectors_used" to emptyList<Any>(),
                ),
            )
        )
        val msg = buildAskResultDialogMessage("q", response)
        assertTrue(msg.contains("evidence_bundle: present in response"), msg)
        assertTrue(msg.contains("ask_path: v1_evidence"), msg)
        assertTrue(msg.indexOf("Grounding calibration") < msg.indexOf("Response provenance"), msg)
        assertTrue(msg.indexOf("Response provenance") < msg.indexOf("PLAN ONLY"), msg)
    }

    @Test
    fun `v0 server evidence_first_meta is echoed without inference`() {
        val response = RuntimeResponse(
            outcome = RuntimeOutcome.BOUNDED_ALLOW,
            requestId = "r4",
            ui = null,
            metadata = planTruthMeta(requestId = "r4", traceId = "trace-r4") + mapOf(
                "evidence_first_meta" to mapOf(
                    "used_layer5" to true,
                    "workspace_input_path" to "/tmp/ws",
                ),
                "plan_summary" to mapOf("steps" to listOf("s")),
                "context_bundle" to mapOf("revision" to "r", "files" to emptyList<Any>(), "selectors_used" to emptyList<Any>()),
            )
        )
        val msg = buildAskResultDialogMessage("q", response)
        assertTrue(msg.contains("used_layer5: true"), msg)
        assertTrue(msg.contains("workspace_input_path: /tmp/ws"), msg)
    }

    @Test
    fun `plan summary notes are rendered when backend provides them`() {
        val response = RuntimeResponse(
            outcome = RuntimeOutcome.BOUNDED_ALLOW,
            requestId = "r5",
            ui = null,
            metadata = planTruthMeta(requestId = "r5", traceId = "trace-r5") + mapOf(
                "plan_summary" to mapOf(
                    "steps" to listOf("step-1"),
                    "notes" to listOf("note A", "note B"),
                ),
                "context_bundle" to mapOf(
                    "revision" to "rev5",
                    "files" to emptyList<Any>(),
                    "selectors_used" to emptyList<Any>(),
                ),
            ),
        )
        val msg = buildAskResultDialogMessage("q", response)
        assertTrue(msg.contains("Plan notes:"), msg)
        assertTrue(msg.contains("  - note A"), msg)
        assertTrue(msg.contains("  - note B"), msg)
    }

    @Test
    fun `empty context files wording is backend-truthful`() {
        val response = RuntimeResponse(
            outcome = RuntimeOutcome.BOUNDED_ALLOW,
            requestId = "r6",
            ui = null,
            metadata = planTruthMeta(requestId = "r6", traceId = "trace-r6") + mapOf(
                "plan_summary" to mapOf("steps" to listOf("s")),
                "context_bundle" to mapOf(
                    "revision" to "rev6",
                    "files" to emptyList<Any>(),
                    "selectors_used" to emptyList<Any>(),
                ),
            ),
        )
        val msg = buildAskResultDialogMessage("q", response)
        assertTrue(msg.contains("(backend returned context_bundle.files: empty)"), msg)
        assertTrue(!msg.contains("(no files selected)"), msg)
    }
}
