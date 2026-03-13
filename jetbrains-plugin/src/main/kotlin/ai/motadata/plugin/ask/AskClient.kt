package ai.motadata.plugin.ask

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

data class AskContextFile(
    val path: String,
    val selectionReason: String
)

data class AskResult(
    val success: Boolean,
    val contextRevision: String?,
    val files: List<AskContextFile>,
    val selectorsUsed: List<String>,
    val planSteps: List<String>,
    val uiTitle: String?,
    val uiMessage: String?,
    val error: String?
)

class AskClient(
    private val gson: Gson = Gson(),
    private val baseUrl: String = "http://127.0.0.1:8089"
) {

    fun ask(project: Project, question: String): AskResult {
        return try {
            val requestJson = buildAskRequestJson(project, question)
            val responseJson = postJson("$baseUrl/v0/ask", requestJson)
            parsePlanOnlyResponse(responseJson)
        } catch (e: Exception) {
            AskResult(
                success = false,
                contextRevision = null,
                files = emptyList(),
                selectorsUsed = emptyList(),
                planSteps = emptyList(),
                uiTitle = null,
                uiMessage = null,
                error = e.message ?: "Unknown error calling /v0/ask"
            )
        }
    }

    private fun buildAskRequestJson(project: Project, question: String): String {
        val requestId = "req-ask-${UUID.randomUUID()}"
        val timestamp = Instant.now().atOffset(ZoneOffset.UTC).format(DateTimeFormatter.ISO_INSTANT)

        val repoManager = GitRepositoryManager.getInstance(project)
        val repo = repoManager.repositories.firstOrNull()
        val branch = repo?.currentBranchName ?: "unknown"
        val revision = repo?.currentRevision ?: "unknown-revision"

        val askRequest = mapOf(
            "schema_version" to "ask_request.v0.1",
            "request_id" to requestId,
            "timestamp_utc" to timestamp,
            "repo_root" to (project.basePath ?: ""),
            "revision" to revision,
            "query" to question,
            "branch" to branch
        )

        return gson.toJson(askRequest)
    }

    private fun parsePlanOnlyResponse(json: String): AskResult {
        val root = gson.fromJson(json, JsonObject::class.java)

        val posture = root.getAsJsonPrimitive("governance_posture")?.asString
        val execution = root.getAsJsonPrimitive("execution")?.asBoolean

        val contextBundle = root.getAsJsonObject("context_bundle")
        val revision = contextBundle?.getAsJsonPrimitive("revision")?.asString

        val filesJson = contextBundle?.getAsJsonArray("files")
        val files = filesJson?.mapNotNull { el ->
            val obj = el.asJsonObject
            val path = obj.getAsJsonPrimitive("path")?.asString
            val reason = obj.getAsJsonPrimitive("selection_reason")?.asString
            if (path != null && reason != null) AskContextFile(path, reason) else null
        } ?: emptyList()

        val selectorsJson = contextBundle?.getAsJsonArray("selectors_used")
        val selectors = selectorsJson?.mapNotNull { it.asString } ?: emptyList()

        val planSummary = root.getAsJsonObject("plan_summary")
        val stepsJson = planSummary?.getAsJsonArray("steps")
        val steps = stepsJson?.mapNotNull { it.asString } ?: emptyList()

        val ui = root.getAsJsonObject("ui")
        val uiTitle = ui?.getAsJsonPrimitive("title")?.asString
        val uiMessage = ui?.getAsJsonPrimitive("message")?.asString

        val postureOk = posture == "PLAN_ONLY"
        val executionOk = execution == false

        return AskResult(
            success = postureOk && executionOk,
            contextRevision = revision,
            files = files,
            selectorsUsed = selectors,
            planSteps = steps,
            uiTitle = uiTitle,
            uiMessage = uiMessage,
            error = if (postureOk && executionOk) null else "Invalid posture/execution in response"
        )
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
            throw RuntimeException("Ask service HTTP $status: $response")
        }

        return response.toString()
    }
}

