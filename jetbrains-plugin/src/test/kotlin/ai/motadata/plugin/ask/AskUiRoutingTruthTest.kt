package ai.motadata.plugin.ask

import ai.motadata.plugin.bridge.AskPluginRouting
import ai.motadata.plugin.bridge.AskRoutingDecision
import ai.motadata.plugin.bridge.RuntimeOutcome
import ai.motadata.plugin.bridge.RuntimeResponse
import ai.motadata.plugin.bridge.mergeAskPluginRoutingMetadata
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class AskUiRoutingTruthTest {

    @Test
    fun `routing_mode explain_debug maps to debug UI`() {
        val response = RuntimeResponse(
            outcome = RuntimeOutcome.BOUNDED_ALLOW,
            requestId = "a1",
            metadata = mapOf("routing_mode" to "explain_debug"),
        )
        assertTrue(isExplainDebugAskUi(response))
        val msg = buildAskResultDialogMessage("q", response)
        assertTrue(msg.contains("Explain/Debug — PLAN ONLY"), msg)
        assertFalse(msg.contains("  PLAN ONLY — No execution performed"), msg)
    }

    @Test
    fun `routing_mode plan_only maps to plan UI`() {
        val response = RuntimeResponse(
            outcome = RuntimeOutcome.BOUNDED_ALLOW,
            requestId = "a2",
            metadata = mapOf("routing_mode" to "plan_only"),
        )
        assertFalse(isExplainDebugAskUi(response))
        val msg = buildAskResultDialogMessage("q", response)
        assertTrue(msg.contains("  PLAN ONLY — No execution performed"), msg)
        assertFalse(msg.contains("Explain/Debug — PLAN ONLY"), msg)
    }

    @Test
    fun `plan UI even when explain_debug object is present if routing_mode is plan_only`() {
        val response = RuntimeResponse(
            outcome = RuntimeOutcome.BOUNDED_ALLOW,
            requestId = "a3",
            metadata = mapOf(
                "routing_mode" to "plan_only",
                "trace_id" to "t-deceptive",
                "plugin_ask_routing" to AskPluginRouting.V1_SUCCESS,
                "explain_debug" to mapOf("summary" to "must not drive UI mode"),
                "plan_summary" to mapOf("steps" to listOf("step")),
            ),
        )
        assertFalse(isExplainDebugAskUi(response))
        val msg = buildAskResultDialogMessage("q", response)
        assertTrue(msg.contains("  PLAN ONLY — No execution performed"), msg)
        assertFalse(msg.contains("Explain/Debug — PLAN ONLY"), msg)
    }

    @Test
    fun `explain_debug UI when routing_mode explain_debug even if explain_debug payload missing`() {
        val response = RuntimeResponse(
            outcome = RuntimeOutcome.BOUNDED_ALLOW,
            requestId = "a4",
            metadata = mapOf(
                "routing_mode" to "explain_debug",
                "trace_id" to "t-missing-payload",
                "plugin_ask_routing" to AskPluginRouting.V1_SUCCESS,
            ),
        )
        assertTrue(isExplainDebugAskUi(response))
        val msg = buildAskResultDialogMessage("q", response)
        assertTrue(msg.contains("routing_mode is explain_debug but explain_debug payload is absent"), msg)
    }

    @Test
    fun `mergeAskPluginRoutingMetadata exposes trace_id routing_mode plugin_ask_routing and decision`() {
        val base = RuntimeResponse(
            outcome = RuntimeOutcome.BOUNDED_ALLOW,
            requestId = "m1",
            metadata = mapOf(
                "routing_mode" to "plan_only",
            ),
        )
        val decision = AskRoutingDecision(
            requestId = "m1",
            traceId = "trace-merge",
            attempt = "v1",
            result = "failed",
            reason = "404",
            fallbackTo = "v0",
        )
        val merged = mergeAskPluginRoutingMetadata(
            base,
            traceId = "trace-merge",
            pluginAskRouting = AskPluginRouting.V0_AFTER_V1_HTTP_FALLBACK,
            decision = decision,
        )
        assertEquals("trace-merge", merged.metadata["trace_id"])
        assertEquals("plan_only", merged.metadata["routing_mode"])
        assertEquals(AskPluginRouting.V0_AFTER_V1_HTTP_FALLBACK, merged.metadata[AskPluginRouting.METADATA_KEY])
        @Suppress("UNCHECKED_CAST")
        val dm = merged.metadata["plugin_ask_routing_decision"] as Map<*, *>
        assertEquals("v1", dm["attempt"])
        assertEquals("failed", dm["result"])
        assertEquals("v0", dm["fallback_to"])
    }

    @Test
    fun `summary lists plugin routing fields`() {
        val response = RuntimeResponse(
            outcome = RuntimeOutcome.BOUNDED_ALLOW,
            requestId = "s1",
            metadata = mapOf(
                "trace_id" to "tr-s",
                "routing_mode" to "explain_debug",
                "plugin_ask_routing" to AskPluginRouting.V0_AFTER_V1_HTTP_FALLBACK,
            ),
        )
        val summary = buildAskResultSummaryMessage("q", response)
        assertTrue(summary.contains("trace_id: tr-s"), summary)
        assertTrue(summary.contains("routing_mode: explain_debug"), summary)
        assertTrue(summary.contains("plugin_ask_routing: ${AskPluginRouting.V0_AFTER_V1_HTTP_FALLBACK}"), summary)
        assertTrue(summary.contains("plugin fallback path"), summary)
    }

    @Test
    fun `summary uses one compact routing line when not fallback`() {
        val response = RuntimeResponse(
            outcome = RuntimeOutcome.BOUNDED_ALLOW,
            requestId = "s2",
            metadata = mapOf(
                "trace_id" to "tr-happy",
                "routing_mode" to "plan_only",
                "plugin_ask_routing" to AskPluginRouting.V1_SUCCESS,
            ),
        )
        val summary = buildAskResultSummaryMessage("q", response)
        assertTrue(summary.contains("Routing: trace=tr-happy · mode=plan_only · plugin=v1_success"), summary)
        assertFalse(summary.contains("trace_id: tr-happy"), summary)
    }
}
