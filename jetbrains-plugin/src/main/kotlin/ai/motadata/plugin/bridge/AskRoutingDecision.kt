package ai.motadata.plugin.bridge

import com.intellij.openapi.diagnostic.Logger

/**
 * In-memory ROUTING_DECISION attached to Ask [RuntimeResponse.metadata] (not only logs).
 */
data class AskRoutingDecision(
    val requestId: String,
    val traceId: String,
    val attempt: String,
    val result: String,
    val reason: String? = null,
    val fallbackTo: String? = null,
) {
    fun toMetadataMap(): Map<String, Any?> = buildMap {
        put("request_id", requestId)
        put("trace_id", traceId)
        put("attempt", attempt)
        put("result", result)
        reason?.let { put("reason", it) }
        fallbackTo?.let { put("fallback_to", it) }
    }
}

/**
 * Plugin-side label for which Ask HTTP path produced the response.
 */
object AskPluginRouting {
    const val METADATA_KEY = "plugin_ask_routing"
    const val V1_SUCCESS = "v1_success"
    const val V0_DIRECT = "v0_direct"
    const val V0_AFTER_V1_HTTP_FALLBACK = "v0_after_v1_http_fallback"
    const val CONTEXT_EXPORT_THEN_V0 = "context_export_then_v0"
}

/**
 * Structured, deterministic ROUTING_DECISION logs for traceability (Action 11).
 * Every log line has a matching [AskRoutingDecision] carried on the response.
 */
internal object AskRoutingDecisionLog {
    private val LOG = Logger.getInstance("ai.motadata.plugin.bridge.RoutingDecision")

    fun log(decision: AskRoutingDecision) {
        LOG.info(formatLog(decision))
    }

    fun formatLog(decision: AskRoutingDecision): String {
        val sb = StringBuilder()
        sb.appendLine("ROUTING_DECISION:")
        sb.append("request_id=").append(decision.requestId).append('\n')
        sb.append("trace_id=").append(decision.traceId).append('\n')
        sb.append("attempt=").append(decision.attempt).append('\n')
        sb.append("result=").append(decision.result).append('\n')
        decision.reason?.let { sb.append("reason=").append(it).append('\n') }
        decision.fallbackTo?.let { sb.append("fallback_to=").append(it).append('\n') }
        return sb.toString().trimEnd()
    }
}
