package ai.motadata.plugin.startup

import ai.motadata.plugin.assistant.HostContract
import ai.motadata.plugin.util.GitInfoUtil
import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import com.intellij.openapi.startup.StartupActivity

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
        val report = HostContract.validate()
        val planGateBase = report.planGateBase
        val contextBase = report.contextBase
        val localCommit = localGitShortCommit(project)
        val findings = report.findings.map {
            val severity = if (it.contains("missing", ignoreCase = true) || it.contains("mismatch", ignoreCase = true)) {
                Severity.ERROR
            } else {
                Severity.WARNING
            }
            Finding(severity, it)
        }

        val summary = buildString {
            appendLine("Plan-Gate: $planGateBase")
            appendLine("Context Layer: $contextBase")
            appendLine("Local plugin commit: ${localCommit ?: "unknown"}")
            if (findings.isNotEmpty()) {
                appendLine("Findings:")
                findings.take(6).forEach { appendLine("- ${it.message}") }
                if (findings.size > 6) {
                    appendLine("- ...and ${findings.size - 6} more")
                }
                appendLine()
                appendLine(report.guidance)
                appendLine()
                appendLine("Assistant actions are hard-gated until this host contract is fixed.")
            } else {
                appendLine("Host contract: PASS")
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

    private data class Finding(val severity: Severity, val message: String)

    private enum class Severity(val rank: Int) {
        INFO(0),
        WARNING(1),
        ERROR(2),
    }

    companion object {
        private val LOG = Logger.getInstance(MotadataStartupStackCheckActivity::class.java)
        private const val PROP_STARTUP_CHECK_ENABLED = "motadata.startup.stack.check.enabled"
        private const val ENV_STARTUP_CHECK_ENABLED = "MOTADATA_STARTUP_STACK_CHECK_ENABLED"
    }
}
