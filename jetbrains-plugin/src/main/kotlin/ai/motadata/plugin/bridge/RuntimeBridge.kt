package ai.motadata.plugin.bridge

import com.google.gson.Gson
import com.google.gson.JsonObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.nio.charset.StandardCharsets
import java.util.UUID

/**
 * Thrown when the runtime returns an HTTP error status (4xx/5xx).
 * Service was reachable; the request or server state was invalid.
 * Must NOT be mapped to RUNTIME_UNAVAILABLE.
 */
private class RuntimeHttpException(statusCode: Int, body: String) :
    RuntimeException("Runtime HTTP $statusCode: $body")

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
    private val baseUrl: String = "http://127.0.0.1:8089",
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
        val askRequest = buildAskRequest(request)
        return try {
            val responseJson = postJson("$baseUrl/v0/ask", askRequest)
            parseAskResponse(request.requestId, responseJson)
        } catch (e: RuntimeHttpException) {
            RuntimeResponse.unknown(request.requestId, e.message ?: "Bad request")
        } catch (e: Exception) {
            RuntimeResponse.runtimeUnavailable(request.requestId, e.message ?: "Unknown error")
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

    private fun buildAskRequest(request: RuntimeRequest): String {
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
        if (request.selectedFile != null) askRequest["selected_file"] = request.selectedFile
        if (request.taskType != null) askRequest["task_type"] = request.taskType
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

    private fun parseAskResponse(requestId: String, json: String): RuntimeResponse {
        val root = gson.fromJson(json, JsonObject::class.java)

        val posture = root.getAsJsonPrimitive("governance_posture")?.asString
        val execution = root.getAsJsonPrimitive("execution")?.asBoolean ?: false

        val outcome = when {
            posture == "PLAN_ONLY" && !execution -> RuntimeOutcome.BOUNDED_ALLOW
            execution -> RuntimeOutcome.EXECUTED
            else -> RuntimeOutcome.UNKNOWN
        }

        val ui = RuntimeUi(
            title = "Repo-Aware Plan (PLAN ONLY)",
            message = "Planning complete. No execution performed.",
            severity = "info"
        )

        val contextBundle = root.getAsJsonObject("context_bundle")
        val planSummary = root.getAsJsonObject("plan_summary")
        val explainDebugObj = root.getAsJsonObject("explain_debug")

        val metadata = mutableMapOf<String, Any?>()
        if (contextBundle != null) {
            metadata["context_bundle"] = gson.fromJson(contextBundle, Map::class.java)
        }
        if (planSummary != null) {
            metadata["plan_summary"] = gson.fromJson(planSummary, Map::class.java)
        }
        if (explainDebugObj != null) {
            metadata["explain_debug"] = gson.fromJson(explainDebugObj, Map::class.java)
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

    private fun parseExecuteResponse(requestId: String, json: String): RuntimeResponse {
        val root = gson.fromJson(json, JsonObject::class.java)

        val outcomeStr = root.getAsJsonPrimitive("outcome")?.asString
        val posture = root.getAsJsonPrimitive("posture")?.asString

        val outcome = when (outcomeStr?.uppercase()) {
            "EXECUTED" -> RuntimeOutcome.EXECUTED
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
        val wasExecuted = root.getAsJsonPrimitive("executed")?.asBoolean ?: (outcome == RuntimeOutcome.EXECUTED)

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
