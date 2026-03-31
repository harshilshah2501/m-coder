package ai.motadata.plugin.bridge

import com.intellij.openapi.diagnostic.Logger

/**
 * Plugin-side metadata when Ask used a degraded HTTP path (evidence-first → /v0/ask).
 * See Action 11: compatibility path hardening.
 */
internal object AskPluginRouting {
    const val METADATA_KEY = "plugin_ask_routing"
    const val V0_AFTER_EVIDENCE_EXPORT_UNREACHABLE = "v0_after_evidence_export_unreachable"
    const val V0_AFTER_V1_HTTP_FALLBACK = "v0_after_v1_http_fallback"
}

/**
 * Structured, deterministic ROUTING_DECISION logs for traceability (Action 11).
 */
internal object AskRoutingDecisionLog {
    private val LOG = Logger.getInstance("ai.motadata.plugin.bridge.RoutingDecision")

    fun log(
        requestId: String,
        traceId: String,
        attempt: String,
        result: String,
        reason: String? = null,
        fallbackTo: String? = null,
    ) {
        val sb = StringBuilder()
        sb.appendLine("ROUTING_DECISION:")
        sb.append("request_id=").append(requestId).append('\n')
        sb.append("trace_id=").append(traceId).append('\n')
        sb.append("attempt=").append(attempt).append('\n')
        sb.append("result=").append(result).append('\n')
        reason?.let { sb.append("reason=").append(it).append('\n') }
        fallbackTo?.let { sb.append("fallback_to=").append(it).append('\n') }
        LOG.info(sb.toString().trimEnd())
    }
}
