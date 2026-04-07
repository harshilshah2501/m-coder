package ai.motadata.plugin.startup

import ai.motadata.plugin.bridge.Layer5EvidenceExporter
import ai.motadata.plugin.bridge.MotadataRuntimeConfig
import ai.motadata.plugin.util.GitInfoUtil
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import com.intellij.openapi.startup.StartupActivity
import java.net.HttpURLConnection
import java.net.URL
import java.nio.charset.StandardCharsets

/**
 * Runs a lightweight stack check when a project loads so plugin operators get immediate
 * visibility into health/version/compatibility drift before using Ask/Execute actions.
 */
class MotadataStartupStackCheckActivity : StartupActivity.DumbAware {

    override fun runActivity(project: Project) {
        if (!isStartupCheckEnabled()) {
            return
        }
        ApplicationManager.getApplication().executeOnPooledThread {
            runCatching { runChecks(project) }
                .onFailure {
                    LOG.warn("Motadata startup stack check failed unexpectedly", it)
                    notify(
                        project,
                        "Motadata Stack Check Failed",
                        "Startup stack check crashed: ${it.message ?: "unknown error"}",
                        NotificationType.WARNING,
                    )
                }
        }
    }

    private fun runChecks(project: Project) {
        val planGateBase = MotadataRuntimeConfig.planGateBaseUrl().trimEnd('/')
        val contextBase = Layer5EvidenceExporter.contextLayerBaseUrl().trimEnd('/')

        val findings = mutableListOf<Finding>()

        val contextHealth = getStatus("$contextBase/healthz")
        val planHealth = getStatus("$planGateBase/healthz")

        if (contextHealth != 200) {
            findings += Finding(Severity.ERROR, "Context Layer /healthz returned $contextHealth ($contextBase)")
        }
        if (planHealth != 200) {
            findings += Finding(Severity.ERROR, "Plan-Gate /healthz returned $planHealth ($planGateBase)")
        }

        val contextVersion = getJson("$contextBase/version")
        val planVersion = getJson("$planGateBase/version")

        if (contextVersion == null) {
            findings += Finding(Severity.WARNING, "Context Layer /version unavailable or invalid JSON")
        }
        if (planVersion == null) {
            findings += Finding(Severity.ERROR, "Plan-Gate /version unavailable or invalid JSON")
        }

        val contextCommit = contextVersion?.get("git_commit")?.takeIf { it.isNotBlank() }
        val planCommit = planVersion?.get("git_commit")?.takeIf { it.isNotBlank() }
        val localCommit = localGitShortCommit(project)

        if (planCommit == null) {
            findings += Finding(Severity.ERROR, "Plan-Gate /version has no git_commit")
        }
        if (contextCommit == null) {
            findings += Finding(Severity.WARNING, "Context Layer /version has no git_commit")
        }
        if (contextCommit != null && planCommit != null && contextCommit != planCommit) {
            findings += Finding(
                Severity.ERROR,
                "Service commit mismatch: Context=$contextCommit vs Plan-Gate=$planCommit",
            )
        }
        if (localCommit != null && planCommit != null && localCommit != planCommit) {
            findings += Finding(
                Severity.WARNING,
                "Plugin workspace commit ($localCommit) differs from Plan-Gate commit ($planCommit)",
            )
        }

        val contextExportCode = postStatus("$contextBase/v1/export_evidence", "{}")
        val planV1AskCode = postStatus("$planGateBase/v1/ask", "{}")
        val planV0AskCode = postStatus("$planGateBase/v0/ask", "{}")

        if (isMissingRoute(contextExportCode)) {
            findings += Finding(Severity.ERROR, "Context Layer route missing: POST /v1/export_evidence ($contextExportCode)")
        }
        if (isMissingRoute(planV1AskCode)) {
            findings += Finding(Severity.ERROR, "Plan-Gate route missing: POST /v1/ask ($planV1AskCode)")
        }
        if (isMissingRoute(planV0AskCode)) {
            findings += Finding(Severity.ERROR, "Plan-Gate route missing: POST /v0/ask ($planV0AskCode)")
        }

        val summary = buildString {
            appendLine("Plan-Gate: $planGateBase")
            appendLine("Context Layer: $contextBase")
            appendLine("Health: context=$contextHealth, plan_gate=$planHealth")
            appendLine("Compatibility: export=$contextExportCode, v1_ask=$planV1AskCode, v0_ask=$planV0AskCode")
            appendLine("Commits: local=${localCommit ?: "unknown"}, context=${contextCommit ?: "missing"}, plan_gate=${planCommit ?: "missing"}")
            if (findings.isNotEmpty()) {
                appendLine("Findings:")
                findings.take(6).forEach { appendLine("- ${it.message}") }
                if (findings.size > 6) {
                    appendLine("- ...and ${findings.size - 6} more")
                }
            }
        }

        val severity = findings.maxOfOrNull { it.severity.rank } ?: Severity.INFO.rank
        val type = when (severity) {
            Severity.ERROR.rank -> NotificationType.ERROR
            Severity.WARNING.rank -> NotificationType.WARNING
            else -> NotificationType.INFORMATION
        }
        val title = when (type) {
            NotificationType.ERROR -> "Motadata Stack Check: FAIL"
            NotificationType.WARNING -> "Motadata Stack Check: WARN"
            else -> "Motadata Stack Check: OK"
        }

        notify(project, title, summary, type)
    }

    private fun isStartupCheckEnabled(): Boolean {
        val prop = System.getProperty(PROP_STARTUP_CHECK_ENABLED)?.trim()?.lowercase()
        if (prop == "0" || prop == "false" || prop == "no") return false
        val env = System.getenv(ENV_STARTUP_CHECK_ENABLED)?.trim()?.lowercase()
        if (env == "0" || env == "false" || env == "no") return false
        return true
    }

    private fun notify(project: Project, title: String, content: String, type: NotificationType) {
        if (project.isDisposed) return
        val group = NotificationGroupManager.getInstance().getNotificationGroup("Motadata AI")
        group.createNotification(title, content, type).notify(project)
    }

    private fun localGitShortCommit(project: Project): String? {
        val revision = GitInfoUtil.getGitInfo(project).revision
        if (revision.isBlank() || revision == "unknown-revision") return null
        return revision.take(7)
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

    private data class Finding(val severity: Severity, val message: String)

    private enum class Severity(val rank: Int) {
        INFO(0),
        WARNING(1),
        ERROR(2),
    }

    companion object {
        private val LOG = Logger.getInstance(MotadataStartupStackCheckActivity::class.java)
        private const val TIMEOUT_MS = 5000
        private const val PROP_STARTUP_CHECK_ENABLED = "motadata.startup.stack.check.enabled"
        private const val ENV_STARTUP_CHECK_ENABLED = "MOTADATA_STARTUP_STACK_CHECK_ENABLED"
    }
}
