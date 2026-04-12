package ai.motadata.plugin.bridge

import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.JsonParser

/**
 * Frozen [ask_request.v1.0] envelope for evidence-first Ask → [POST /v1/ask].
 * Classifies Plan-Gate errors so contract failures never trigger silent v0 fallback.
 */
internal object AskV1Contract {

    /** v1 400 responses that must surface as hard failures (no legacy fallback). */
    private val NO_FALLBACK_ERROR_CODES = setOf(
        "evidence_schema_invalid",
        "identity_mismatch",
        "empty_evidence_bundle",
        "ask_envelope_invalid",
    )

    fun isContractClientFailure(statusCode: Int, responseBody: String): Boolean {
        if (statusCode != 400) return false
        return parseErrorCode(responseBody) in NO_FALLBACK_ERROR_CODES
    }

    fun shouldFallbackV1ToV0(statusCode: Int): Boolean =
        statusCode == 404 || statusCode == 405

    fun parseErrorCode(responseBody: String): String? =
        try {
            val o = JsonParser.parseString(responseBody).asJsonObject
            o.get("error")?.asString
        } catch (_: Exception) {
            null
        }

    fun formatV1FailureMessage(statusCode: Int, responseBody: String): String {
        val code = parseErrorCode(responseBody)
        val msg = try {
            JsonParser.parseString(responseBody).asJsonObject.get("message")?.asString
        } catch (_: Exception) {
            null
        }
        return buildString {
            append("Runtime HTTP $statusCode")
            if (code != null) append(" [").append(code).append("]")
            append(": ")
            append(msg ?: responseBody.take(500))
        }
    }

    fun buildAskRequestV1Json(
        gson: Gson,
        request: RuntimeRequest,
        evidenceBundle: JsonObject,
        traceId: String,
    ): String {
        val root = JsonObject()
        root.addProperty("schema_version", "ask_request.v1.0")
        root.addProperty("request_id", request.requestId)
        root.addProperty("timestamp_utc", request.timestampUtc)
        root.addProperty("query", request.payload ?: "")
        root.add("evidence_bundle", evidenceBundle.deepCopy())
        if (traceId.isNotBlank()) {
            root.addProperty("trace_id", traceId)
        }

        request.revision?.takeIf { it.isNotBlank() }?.let { root.addProperty("revision", it) }
        request.branch?.takeIf { it.isNotBlank() }?.let { root.addProperty("branch", it) }
        request.selectedFile?.takeIf { it.isNotBlank() }?.let { root.addProperty("selected_file", it) }
        request.taskType?.takeIf { it.isNotBlank() }?.let { root.addProperty("task_type", it) }

        if (!request.selection.isNullOrBlank()) {
            val cc = JsonObject()
            cc.addProperty("selection", request.selection)
            root.add("client_context", cc)
        }

        val hash = evidenceBundle.get("workspace_identity_hash")?.asString
        if (!hash.isNullOrBlank()) {
            root.addProperty("expected_workspace_identity_hash", hash)
        }

        return gson.toJson(root)
    }
}
