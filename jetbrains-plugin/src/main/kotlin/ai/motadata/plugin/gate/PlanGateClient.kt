package ai.motadata.plugin.gate

import com.google.gson.Gson
import com.google.gson.JsonObject
import com.intellij.openapi.project.Project
import git4idea.repo.GitRepositoryManager
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.nio.charset.StandardCharsets
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.util.UUID

/**
 * Thin HTTP client for the local Plan-Gate service.
 *
 * Shadow mode only for this MVP: never blocks IDE actions, only reports what
 * the runtime would do.
 */
class PlanGateClient(
    private val gson: Gson = Gson(),
    private val baseUrl: String = "http://127.0.0.1:8089"
) {

    data class DecisionUi(
        val title: String? = null,
        val message: String? = null,
        val severity: String? = null
    )

    enum class DecisionType {
        APPROVE,
        CONDITIONAL_BLOCK,
        REFUSAL,
        BOUNDING,
        UNKNOWN
    }

    data class DecisionResult(
        val decision: DecisionType,
        val ui: DecisionUi?,
        val error: String? = null
    )

    /**
     * Build and send a PlanRequest for a commit intent in the given project.
     * Returns a parsed DecisionResult, or an error result if the gate is unavailable.
     */
    fun evaluateCommit(project: Project): DecisionResult {
        return try {
            val requestJson = buildPlanRequestJson(project)
            val responseJson = postJson("$baseUrl/v0/plan", requestJson)
            parseDecisionResponse(responseJson)
        } catch (e: Exception) {
            DecisionResult(
                decision = DecisionType.UNKNOWN,
                ui = null,
                error = e.message ?: "Unknown error calling Plan-Gate"
            )
        }
    }

    /**
     * Exposed for tests: build the PlanRequest JSON string without performing HTTP.
     */
    fun buildPlanRequestJson(project: Project, now: Instant = Instant.now()): String {
        val requestId = "req-${UUID.randomUUID()}"
        val timestamp = now.atOffset(ZoneOffset.UTC).format(DateTimeFormatter.ISO_INSTANT)

        val repoManager = GitRepositoryManager.getInstance(project)
        val repo = repoManager.repositories.firstOrNull()
        val branch = repo?.currentBranchName ?: "unknown"
        val revision = repo?.currentRevision ?: "unknown-revision"

        val ideEvent = mapOf(
            "schema_version" to "ide_event.v0.1",
            "event_id" to UUID.randomUUID().toString(),
            "timestamp_utc" to timestamp,
            "ide_context" to mapOf(
                "product" to "jetbrains",
                "ide" to "intellij",
                "project" to project.name,
                "repo_root" to (project.basePath ?: ""),
                "branch" to branch,
                "revision" to revision,
                "user" to (System.getProperty("user.name") ?: "unknown-user")
            ),
            "action" to mapOf(
                "action_type" to "VCS_COMMIT_INTENT",
                "target" to "vcs_commit"
            )
        )

        val planRequest = mapOf(
            "schema_version" to "plan_request.v0.1",
            "request_id" to requestId,
            "timestamp_utc" to timestamp,
            "mode" to "shadow",
            "ide_event" to ideEvent,
            "requested_capabilities" to listOf("plan_and_decide"),
            "client_policy" to mapOf(
                "fail_closed_if_gate_unreachable" to false
            )
        )

        return gson.toJson(planRequest)
    }

    /**
     * Exposed for tests: parse a DecisionResponse JSON string into a DecisionResult.
     */
    fun parseDecisionResponse(json: String): DecisionResult {
        val root = gson.fromJson(json, JsonObject::class.java)

        val decisionStr = root.getAsJsonPrimitive("decision")?.asString
        val decision = when (decisionStr) {
            "APPROVE" -> DecisionType.APPROVE
            "CONDITIONAL_BLOCK" -> DecisionType.CONDITIONAL_BLOCK
            "REFUSAL" -> DecisionType.REFUSAL
            "BOUNDING" -> DecisionType.BOUNDING
            else -> DecisionType.UNKNOWN
        }

        val uiObj = root.getAsJsonObject("ui")
        val ui = if (uiObj != null) {
            DecisionUi(
                title = uiObj.getAsJsonPrimitive("title")?.asString,
                message = uiObj.getAsJsonPrimitive("message")?.asString,
                severity = uiObj.getAsJsonPrimitive("severity")?.asString
            )
        } else {
            null
        }

        return DecisionResult(decision = decision, ui = ui, error = null)
    }

    private fun postJson(url: String, body: String): String {
        val connection = URL(url).openConnection() as HttpURLConnection
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
            throw RuntimeException("Plan-Gate HTTP $status: $response")
        }

        return response.toString()
    }
}

