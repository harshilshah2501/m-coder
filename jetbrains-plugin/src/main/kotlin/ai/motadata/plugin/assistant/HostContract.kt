package ai.motadata.plugin.assistant

import ai.motadata.plugin.bridge.Layer5EvidenceExporter
import ai.motadata.plugin.bridge.MotadataRuntimeConfig
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.Messages
import java.net.HttpURLConnection
import java.net.URL
import java.nio.charset.StandardCharsets

object HostContract {

    data class CheckReport(
        val ok: Boolean,
        val findings: List<String>,
        val guidance: String,
        val planGateBase: String,
        val contextBase: String,
    )

    private const val TIMEOUT_MS = 5000

    fun validate(): CheckReport {
        val planGateBase = MotadataRuntimeConfig.planGateBaseUrl().trimEnd('/')
        val contextBase = Layer5EvidenceExporter.contextLayerBaseUrl().trimEnd('/')

        val findings = mutableListOf<String>()

        val contextHealth = getStatus("$contextBase/healthz")
        val planHealth = getStatus("$planGateBase/healthz")
        if (contextHealth != 200) findings += "Context Layer /healthz returned $contextHealth"
        if (planHealth != 200) findings += "Plan-Gate /healthz returned $planHealth"

        val contextVersion = getJson("$contextBase/version")
        val planVersion = getJson("$planGateBase/version")
        if (contextVersion == null) findings += "Context Layer /version unavailable or invalid JSON"
        if (planVersion == null) findings += "Plan-Gate /version unavailable or invalid JSON"

        val contextCommit = contextVersion?.get("git_commit")?.takeIf { it.isNotBlank() }
        val planCommit = planVersion?.get("git_commit")?.takeIf { it.isNotBlank() }

        if (contextCommit == null) findings += "Context Layer /version missing git_commit"
        if (planCommit == null) findings += "Plan-Gate /version missing git_commit"
        if (contextCommit != null && planCommit != null && contextCommit != planCommit) {
            findings += "Commit mismatch: Context=$contextCommit vs Plan-Gate=$planCommit"
        }

        val exportCode = postStatus("$contextBase/v1/export_evidence", "{}")
        val v1AskCode = postStatus("$planGateBase/v1/ask", "{}")
        val v0AskCode = postStatus("$planGateBase/v0/ask", "{}")
        val executeCode = postStatus("$planGateBase/v0/execute", "{}")

        if (isMissingRoute(exportCode)) findings += "Context Layer route missing: POST /v1/export_evidence ($exportCode)"
        if (isMissingRoute(v1AskCode)) findings += "Plan-Gate route missing: POST /v1/ask ($v1AskCode)"
        if (isMissingRoute(v0AskCode)) findings += "Plan-Gate route missing: POST /v0/ask ($v0AskCode)"
        if (isMissingRoute(executeCode)) findings += "Plan-Gate route missing: POST /v0/execute ($executeCode)"

        val ok = findings.isEmpty()
        return CheckReport(
            ok = ok,
            findings = findings,
            guidance = buildGuidance(planGateBase, contextBase),
            planGateBase = planGateBase,
            contextBase = contextBase,
        )
    }

    fun enforceOrShow(project: Project, modeLabel: String): Boolean {
        val report = validate()
        if (report.ok) return true

        val body = buildString {
            appendLine("Motadata Assistant blocked for mode: $modeLabel")
            appendLine()
            appendLine("Host contract failed:")
            report.findings.forEach { appendLine("- $it") }
            appendLine()
            appendLine(report.guidance)
        }
        Messages.showErrorDialog(project, body, "Motadata Host Contract FAIL")
        return false
    }

    private fun buildGuidance(planGateBase: String, contextBase: String): String = buildString {
        appendLine("Fix steps (deterministic):")
        appendLine("1) On GPU host (45.195.82.10): ./runtime/scripts/governed_services.sh restart")
        appendLine("2) On WSL client: ./scripts/wsl_plugin_mvp_stack.sh restart")
        appendLine("3) Verify endpoints:")
        appendLine("   - Plan-Gate: $planGateBase/healthz and /version")
        appendLine("   - Context Layer: $contextBase/healthz and /version")
        appendLine("4) Ensure Context and Plan-Gate git_commit values match before using Ask/Execute.")
        appendLine("No silent fallback is allowed in this mode.")
    }

    private fun isMissingRoute(code: Int): Boolean = code == 404 || code == 405

    private fun getStatus(url: String): Int {
        return try {
            val conn = URL(url).openConnection() as HttpURLConnection
            conn.requestMethod = "GET"
            conn.connectTimeout = TIMEOUT_MS
            conn.readTimeout = TIMEOUT_MS
            conn.responseCode
        } catch (_: Exception) {
            -1
        }
    }

    private fun postStatus(url: String, body: String): Int {
        return try {
            val conn = URL(url).openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.connectTimeout = TIMEOUT_MS
            conn.readTimeout = TIMEOUT_MS
            conn.doOutput = true
            conn.setRequestProperty("Content-Type", "application/json; charset=utf-8")
            conn.outputStream.use { out -> out.write(body.toByteArray(StandardCharsets.UTF_8)) }
            conn.responseCode
        } catch (_: Exception) {
            -1
        }
    }

    private fun getJson(url: String): Map<String, String>? {
        return try {
            val conn = URL(url).openConnection() as HttpURLConnection
            conn.requestMethod = "GET"
            conn.connectTimeout = TIMEOUT_MS
            conn.readTimeout = TIMEOUT_MS
            if (conn.responseCode !in 200..299) return null
            val text = conn.inputStream.use { String(it.readBytes(), StandardCharsets.UTF_8) }
            val root = JsonParser.parseString(text).asJsonObject
            rootToStringMap(root)
        } catch (_: Exception) {
            null
        }
    }

    private fun rootToStringMap(root: JsonObject): Map<String, String> {
        val out = mutableMapOf<String, String>()
        root.entrySet().forEach { (k, v) ->
            out[k] = if (v.isJsonPrimitive) v.asJsonPrimitive.toString().trim('"') else v.toString()
        }
        return out
    }
}
