package ai.motadata.plugin.bridge

import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.nio.charset.StandardCharsets
import java.util.UUID

/**
 * Merges plugin-side Ask truth into [RuntimeResponse.metadata] for UI and tests.
 * UI mode must use backend [routing_mode] only; this adds trace and routing labels.
 */
internal fun mergeAskPluginRoutingMetadata(
    response: RuntimeResponse,
    traceId: String,
    pluginAskRouting: String,
    decision: AskRoutingDecision,
): RuntimeResponse {
    val md = response.metadata.toMutableMap()
    val existingTrace = md["trace_id"] as? String
    if (existingTrace.isNullOrBlank()) {
        md["trace_id"] = traceId
    }
    md[AskPluginRouting.METADATA_KEY] = pluginAskRouting
    md["plugin_ask_routing_decision"] = decision.toMetadataMap()
    return response.copy(metadata = md)
}

/**
 * Thrown when the runtime returns an HTTP error status (4xx/5xx).
 * Service was reachable; the request or server state was invalid.
 * Must NOT be mapped to RUNTIME_UNAVAILABLE.
 */
internal class RuntimeHttpException(val statusCode: Int, val responseBody: String) :
    RuntimeException("Runtime HTTP $statusCode: $responseBody")

/**
 * RuntimeBridge — The single integration point between IDE plugin and runtime.
 *
 * Architectural Principles (M3.4):
 * - The plugin is a client, NOT a governor.
 * - The plugin MUST NOT make governance decisions itself.
 * - The plugin MUST NOT reinterpret posture semantics.
 * - The plugin MUST NOT execute protected actions locally as fallback.
 * - The plugin MUST NOT silently bypass runtime when unavailable.
 * - The plugin MUST NOT collapse distinct outcomes into generic states.
 *
 * The runtime remains the source of truth.
 * This bridge packages requests, calls runtime, and displays governed outcomes.
 */
class RuntimeBridge(
    private val gson: Gson = Gson(),
    private val baseUrl: String = MotadataRuntimeConfig.planGateBaseUrl(),
    private val timeoutMs: Int = 5000
) {

    /**
     * Evaluate a governance request for VCS commit.
     *
     * Flow: commit attempt → plugin intercept → runtime request → LoopController →
     *       Plan-Gate → governed response → plugin displays result
     *
     * No silent local bypass if runtime is unavailable.
     */
    fun evaluateCommit(request: RuntimeRequest): RuntimeResponse {
        require(request.actionType == RuntimeActionType.VCS_COMMIT) {
            "evaluateCommit requires VCS_COMMIT action type"
        }
        return callPlanEndpoint(request)
    }

    /**
     * Execute an Ask/Plan request (planning only, no execution).
     *
     * The Ask flow remains planning-oriented, non-executing, governance-aware.
     */
    fun askPlan(request: RuntimeRequest): RuntimeResponse {
        require(request.actionType == RuntimeActionType.ASK_PLAN) {
            "askPlan requires ASK_PLAN action type"
        }
        return callAskEndpoint(request)
    }

    /**
     * Request governed execution of a command or action.
     *
     * This routes through the runtime for Plan-Gate approval before any execution.
     * Only safe_execute posture may result in actual execution.
     */
    fun requestExecution(request: RuntimeRequest): RuntimeResponse {
        require(request.actionType == RuntimeActionType.EXECUTE) {
            "requestExecution requires EXECUTE action type"
        }
        return callExecuteEndpoint(request)
    }

    /**
     * Validate whether an action would be allowed without executing.
     *
     * Useful for UI hints (e.g., showing whether commit would be allowed).
     */
    fun validateAction(request: RuntimeRequest): RuntimeResponse {
        require(request.actionType == RuntimeActionType.VALIDATE) {
            "validateAction requires VALIDATE action type"
        }
        return callPlanEndpoint(request, validateOnly = true)
    }

    /**
     * Check if runtime is reachable.
     */
    fun isRuntimeAvailable(): Boolean {
        return try {
            val connection = URL("$baseUrl/healthz").openConnection() as HttpURLConnection
            connection.connectTimeout = timeoutMs
            connection.readTimeout = timeoutMs
            connection.requestMethod = "GET"
            val status = connection.responseCode
            status == 200
        } catch (e: Exception) {
            false
        }
    }

    /**
     * Get runtime version info.
     */
    fun getRuntimeVersion(): Map<String, Any>? {
        return try {
            val connection = URL("$baseUrl/version").openConnection() as HttpURLConnection
            connection.connectTimeout = timeoutMs
            connection.readTimeout = timeoutMs
            connection.requestMethod = "GET"
            if (connection.responseCode == 200) {
                val response = connection.inputStream.bufferedReader().readText()
                gson.fromJson(response, Map::class.java) as Map<String, Any>
            } else {
                null
            }
        } catch (e: Exception) {
            null
        }
    }

    // ─────────────────────────────────────────────────────────────────────────────
    // Private implementation
    // ─────────────────────────────────────────────────────────────────────────────

    private fun callPlanEndpoint(request: RuntimeRequest, validateOnly: Boolean = false): RuntimeResponse {
        val planRequest = buildPlanRequest(request, validateOnly)
        return try {
            val responseJson = postJson("$baseUrl/v0/plan", planRequest)
            parsePlanResponse(request.requestId, responseJson)
        } catch (e: RuntimeHttpException) {
            RuntimeResponse.unknown(request.requestId, e.message ?: "Bad request")
        } catch (e: Exception) {
            RuntimeResponse.runtimeUnavailable(request.requestId, e.message ?: "Unknown error")
        }
    }

    private fun callAskEndpoint(request: RuntimeRequest): RuntimeResponse {
        val traceId = "trace-" + UUID.randomUUID().toString()
        if (!request.evidenceFirst) {
            val decision = AskRoutingDecision(
                requestId = request.requestId,
                traceId = traceId,
                attempt = "v0",
                result = "direct",
            )
            AskRoutingDecisionLog.log(decision)
            return postV0Ask(
                request.requestId,
                buildAskRequestV0(request, includeEvidenceFirstFlag = false, traceId = traceId),
                traceId = traceId,
                pluginAskRouting = AskPluginRouting.V0_DIRECT,
                decision = decision,
            )
        }

        val exportOutcome = Layer5EvidenceExporter.tryExportEvidenceBundle(
            request.repoRoot,
            request.payload ?: "",
            request.requestId,
        )
        val localEvidenceJson = when (exportOutcome) {
            is EvidenceExportOutcome.ServiceFailure ->
                return RuntimeResponse.unknown(
                    request.requestId,
                    formatContextLayerServiceFailure(exportOutcome),
                )
            is EvidenceExportOutcome.Unreachable -> {
                val decision = AskRoutingDecision(
                    requestId = request.requestId,
                    traceId = traceId,
                    attempt = "context_export",
                    result = "unreachable",
                    fallbackTo = "v0",
                )
                AskRoutingDecisionLog.log(decision)
                return postV0Ask(
                    request.requestId,
                    buildAskRequestV0(request, includeEvidenceFirstFlag = true, traceId = traceId),
                    traceId = traceId,
                    pluginAskRouting = AskPluginRouting.CONTEXT_EXPORT_THEN_V0,
                    decision = decision,
                )
            }
            is EvidenceExportOutcome.Success -> exportOutcome.bundleJson
        }

        val evidenceObj = try {
            JsonParser.parseString(localEvidenceJson).asJsonObject
        } catch (_: Exception) {
            return RuntimeResponse.unknown(
                request.requestId,
                "Context Layer returned evidence that is not valid JSON; evidence-first path aborted (no silent /v0/ask fallback).",
            )
        }

        val v1Body = AskV1Contract.buildAskRequestV1Json(gson, request, evidenceObj, traceId)
        return try {
            val responseJson = postJson("$baseUrl/v1/ask", v1Body)
            val v1Decision = AskRoutingDecision(
                requestId = request.requestId,
                traceId = traceId,
                attempt = "v1",
                result = "success",
            )
            AskRoutingDecisionLog.log(v1Decision)
            val parsed = parseAskResponse(request.requestId, responseJson)
            mergeAskPluginRoutingMetadata(
                parsed,
                traceId,
                AskPluginRouting.V1_SUCCESS,
                v1Decision,
            )
        } catch (e: RuntimeHttpException) {
            when {
                AskV1Contract.isContractClientFailure(e.statusCode, e.responseBody) ->
                    RuntimeResponse.unknown(
                        request.requestId,
                        AskV1Contract.formatV1FailureMessage(e.statusCode, e.responseBody),
                    )
                AskV1Contract.shouldFallbackV1ToV0(e.statusCode) -> {
                    val decision = AskRoutingDecision(
                        requestId = request.requestId,
                        traceId = traceId,
                        attempt = "v1",
                        result = "failed",
                        reason = e.statusCode.toString(),
                        fallbackTo = "v0",
                    )
                    AskRoutingDecisionLog.log(decision)
                    postV0Ask(
                        request.requestId,
                        buildAskRequestV0(request, includeEvidenceFirstFlag = true, traceId = traceId),
                        traceId = traceId,
                        pluginAskRouting = AskPluginRouting.V0_AFTER_V1_HTTP_FALLBACK,
                        decision = decision,
                    )
                }
                else ->
                    RuntimeResponse.unknown(request.requestId, e.message ?: "Bad request")
            }
        } catch (e: Exception) {
            RuntimeResponse.runtimeUnavailable(request.requestId, e.message ?: "Unknown error")
        }
    }

    private fun formatContextLayerServiceFailure(out: EvidenceExportOutcome.ServiceFailure): String {
        val preview = out.responseBody.take(1200)
        return if (out.httpStatus > 0) {
            "Context Layer HTTP ${out.httpStatus}: $preview"
        } else {
            "Context Layer provider failure: $preview"
        }
    }

    private fun postV0Ask(
        requestId: String,
        body: String,
        traceId: String,
        pluginAskRouting: String,
        decision: AskRoutingDecision,
    ): RuntimeResponse {
        return try {
            val responseJson = postJson("$baseUrl/v0/ask", body)
            val parsed = parseAskResponse(requestId, responseJson)
            mergeAskPluginRoutingMetadata(parsed, traceId, pluginAskRouting, decision)
        } catch (e: RuntimeHttpException) {
            RuntimeResponse.unknown(requestId, e.message ?: "Bad request")
        } catch (e: Exception) {
            RuntimeResponse.runtimeUnavailable(requestId, e.message ?: "Unknown error")
        }
    }

    private fun callExecuteEndpoint(request: RuntimeRequest): RuntimeResponse {
        val executeRequest = buildExecuteRequest(request)
        return try {
            val responseJson = postJson("$baseUrl/v0/execute", executeRequest)
            parseExecuteResponse(request.requestId, responseJson)
        } catch (e: RuntimeHttpException) {
            RuntimeResponse.unknown(request.requestId, e.message ?: "Bad request")
        } catch (e: Exception) {
            RuntimeResponse.runtimeUnavailable(request.requestId, e.message ?: "Unknown error")
        }
    }

    private fun buildPlanRequest(request: RuntimeRequest, validateOnly: Boolean): String {
        val ideEvent = mapOf(
            "schema_version" to "ide_event.v0.1",
            "event_id" to UUID.randomUUID().toString(),
            "timestamp_utc" to request.timestampUtc,
            "ide_context" to mapOf(
                "product" to request.ideContext.product,
                "ide" to request.ideContext.ide,
                "project" to request.ideContext.projectName,
                "repo_root" to request.repoRoot,
                "branch" to (request.branch ?: "unknown"),
                "revision" to (request.revision ?: "unknown-revision"),
                "user" to request.ideContext.user
            ),
            "action" to mapOf(
                "action_type" to request.actionType.toActionTypeString(),
                "target" to (if (request.actionType == RuntimeActionType.VCS_COMMIT) "vcs_commit" else "unknown")
            )
        )

        val planRequest = mapOf(
            "schema_version" to "plan_request.v0.1",
            "request_id" to request.requestId,
            "timestamp_utc" to request.timestampUtc,
            "mode" to request.clientPolicy.mode,
            "ide_event" to ideEvent,
            "requested_capabilities" to listOf("plan_and_decide"),
            "client_policy" to mapOf(
                "fail_closed_if_gate_unreachable" to request.clientPolicy.failClosedIfUnreachable,
                "validate_only" to validateOnly
            ),
            "task_id" to request.taskId,
            "plan_hash" to request.planHash
        ).filterValues { it != null }

        return gson.toJson(planRequest)
    }

    /** Legacy AskRequest v0.1 for [POST /v0/ask] only. */
    private fun buildAskRequestV0(
        request: RuntimeRequest,
        includeEvidenceFirstFlag: Boolean,
        traceId: String,
    ): String {
        val clientContext = mutableMapOf<String, Any?>()
        request.selection?.let { clientContext["selection"] = it }

        val askRequest = mutableMapOf<String, Any?>(
            "schema_version" to "ask_request.v0.1",
            "request_id" to request.requestId,
            "timestamp_utc" to request.timestampUtc,
            "repo_root" to request.repoRoot,
            "revision" to (request.revision ?: "unknown-revision"),
            "query" to (request.payload ?: ""),
            "branch" to request.branch
        )
        if (traceId.isNotBlank()) {
            askRequest["trace_id"] = traceId
        }
        if (request.selectedFile != null) askRequest["selected_file"] = request.selectedFile
        if (request.taskType != null) askRequest["task_type"] = request.taskType
        if (includeEvidenceFirstFlag) askRequest["evidence_first"] = true
        if (clientContext.isNotEmpty()) askRequest["client_context"] = clientContext

        return gson.toJson(askRequest.filterValues { it != null })
    }

    private fun buildExecuteRequest(request: RuntimeRequest): String {
        val executeRequest = mapOf(
            "schema_version" to "execute_request.v0.1",
            "request_id" to request.requestId,
            "timestamp_utc" to request.timestampUtc,
            "repo_root" to request.repoRoot,
            "revision" to (request.revision ?: "unknown-revision"),
            "branch" to request.branch,
            "command" to (request.payload ?: ""),
            "task_id" to request.taskId,
            "plan_hash" to request.planHash,
            "ide_context" to request.ideContext.toMap(),
            "client_policy" to request.clientPolicy.toMap()
        ).filterValues { it != null }

        return gson.toJson(executeRequest)
    }

    private fun parsePlanResponse(requestId: String, json: String): RuntimeResponse {
        val root = gson.fromJson(json, JsonObject::class.java)

        val decisionStr = root.getAsJsonPrimitive("decision")?.asString
        val posture = root.getAsJsonPrimitive("posture")?.asString

        val outcome = if (posture != null) {
            RuntimeOutcome.fromPosture(posture)
        } else {
            RuntimeOutcome.fromLegacyDecision(decisionStr)
        }

        val uiObj = root.getAsJsonObject("ui")
        val ui = if (uiObj != null) {
            RuntimeUi(
                title = uiObj.getAsJsonPrimitive("title")?.asString,
                message = uiObj.getAsJsonPrimitive("message")?.asString,
                severity = uiObj.getAsJsonPrimitive("severity")?.asString
            )
        } else {
            null
        }

        val reason = root.getAsJsonPrimitive("reason")?.asString
        val planHash = root.getAsJsonPrimitive("plan_hash")?.asString
        val ledgerRowId = root.getAsJsonPrimitive("ledger_row_id")?.asString

        return RuntimeResponse(
            outcome = outcome,
            requestId = requestId,
            ui = ui,
            reason = reason,
            wasExecuted = outcome == RuntimeOutcome.EXECUTED,
            ledgerRowId = ledgerRowId,
            planHash = planHash
        )
    }

    internal fun parseAskResponse(requestId: String, json: String): RuntimeResponse {
        val root = gson.fromJson(json, JsonObject::class.java)

        val posture = root.getAsJsonPrimitive("governance_posture")?.asString
        val execution = root.getAsJsonPrimitive("execution")?.asBoolean ?: false

        val outcome = when {
            posture == "PLAN_ONLY" && !execution -> RuntimeOutcome.BOUNDED_ALLOW
            execution -> RuntimeOutcome.EXECUTED
            else -> RuntimeOutcome.UNKNOWN
        }

        val uiObj = root.getAsJsonObject("ui")
        val ui = if (uiObj != null) {
            RuntimeUi(
                title = uiObj.getAsJsonPrimitive("title")?.asString,
                message = uiObj.getAsJsonPrimitive("message")?.asString,
                severity = uiObj.getAsJsonPrimitive("severity")?.asString,
            )
        } else {
            null
        }

        val contextBundle = root.getAsJsonObject("context_bundle")
        val planSummary = root.getAsJsonObject("plan_summary")
        val explainDebugObj = root.getAsJsonObject("explain_debug")

        val metadata = mutableMapOf<String, Any?>()
        root.getAsJsonPrimitive("request_id")?.asString?.let { metadata["backend_request_id"] = it }
        root.getAsJsonPrimitive("routing_mode")?.asString?.let { metadata["routing_mode"] = it }
        root.getAsJsonPrimitive("trace_id")?.asString?.let { metadata["trace_id"] = it }
        posture?.let { metadata["governance_posture"] = it }
        metadata["execution"] = execution
        if (contextBundle != null) {
            metadata["context_bundle"] = gson.fromJson(contextBundle, Map::class.java)
        }
        if (planSummary != null) {
            metadata["plan_summary"] = gson.fromJson(planSummary, Map::class.java)
        }
        if (explainDebugObj != null) {
            metadata["explain_debug"] = gson.fromJson(explainDebugObj, Map::class.java)
        }

        val evidenceBundleObj = root.getAsJsonObject("evidence_bundle")
        if (evidenceBundleObj != null) {
            @Suppress("UNCHECKED_CAST")
            metadata["evidence_bundle"] = gson.fromJson(evidenceBundleObj, Map::class.java) as Map<String, Any?>
        }
        val evidenceMetaObj = root.getAsJsonObject("evidence_first_meta")
        if (evidenceMetaObj != null) {
            @Suppress("UNCHECKED_CAST")
            metadata["evidence_first_meta"] = gson.fromJson(evidenceMetaObj, Map::class.java) as Map<String, Any?>
        }

        val backendMetadataObj = root.getAsJsonObject("metadata")
        if (backendMetadataObj != null) {
            @Suppress("UNCHECKED_CAST")
            metadata["backend_metadata"] = gson.fromJson(backendMetadataObj, Map::class.java) as Map<String, Any?>
        }

        val contextResolutionObj = root.getAsJsonObject("context_resolution")
        if (contextResolutionObj != null) {
            @Suppress("UNCHECKED_CAST")
            metadata["context_resolution"] = gson.fromJson(contextResolutionObj, Map::class.java) as Map<String, Any?>
        }

        return RuntimeResponse(
            outcome = outcome,
            requestId = requestId,
            ui = ui,
            reason = "Plan-only response (no execution)",
            wasExecuted = false,
            metadata = metadata
        )
    }

    internal fun parseExecuteResponse(requestId: String, json: String): RuntimeResponse {
        val root = gson.fromJson(json, JsonObject::class.java)

        val outcomeStr = root.getAsJsonPrimitive("outcome")?.asString
        val posture = root.getAsJsonPrimitive("posture")?.asString

        val outcome = when (outcomeStr?.uppercase()) {
            "EXECUTED" -> RuntimeOutcome.EXECUTED
            "EXECUTED_FAILED" -> RuntimeOutcome.EXECUTED_FAILED
            "REFUSED" -> RuntimeOutcome.REFUSED
            "BLOCKED" -> RuntimeOutcome.BLOCKED
            "DEFERRED" -> RuntimeOutcome.DEFERRED
            "BOUNDED_ALLOW" -> RuntimeOutcome.BOUNDED_ALLOW
            else -> posture?.let { RuntimeOutcome.fromPosture(it) } ?: RuntimeOutcome.UNKNOWN
        }

        val uiObj = root.getAsJsonObject("ui")
        val ui = if (uiObj != null) {
            RuntimeUi(
                title = uiObj.getAsJsonPrimitive("title")?.asString,
                message = uiObj.getAsJsonPrimitive("message")?.asString,
                severity = uiObj.getAsJsonPrimitive("severity")?.asString
            )
        } else {
            null
        }

        val reason = root.getAsJsonPrimitive("reason")?.asString
        val ledgerRowId = root.getAsJsonPrimitive("ledger_row_id")?.asString
        val planHash = root.getAsJsonPrimitive("plan_hash")?.asString
        val wasExecuted = root.getAsJsonPrimitive("executed")?.asBoolean
            ?: (outcome == RuntimeOutcome.EXECUTED || outcome == RuntimeOutcome.EXECUTED_FAILED)

        return RuntimeResponse(
            outcome = outcome,
            requestId = requestId,
            ui = ui,
            reason = reason,
            wasExecuted = wasExecuted,
            ledgerRowId = ledgerRowId,
            planHash = planHash
        )
    }

    private fun postJson(url: String, body: String): String {
        val connection = URL(url).openConnection() as HttpURLConnection
        connection.connectTimeout = timeoutMs
        connection.readTimeout = timeoutMs
        connection.requestMethod = "POST"
        connection.doOutput = true
        connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")

        OutputStreamWriter(connection.outputStream, StandardCharsets.UTF_8).use { writer ->
            writer.write(body)
        }

        val status = connection.responseCode
        val stream = if (status in 200..299) {
            connection.inputStream
        } else {
            connection.errorStream ?: connection.inputStream
        }

        val response = StringBuilder()
        BufferedReader(InputStreamReader(stream, StandardCharsets.UTF_8)).use { reader ->
            var line: String? = reader.readLine()
            while (line != null) {
                response.append(line)
                line = reader.readLine()
            }
        }

        if (status !in 200..299) {
            throw RuntimeHttpException(status, response.toString())
        }

        return response.toString()
    }
}
