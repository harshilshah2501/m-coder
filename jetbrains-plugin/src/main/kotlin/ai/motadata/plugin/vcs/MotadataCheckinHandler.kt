package ai.motadata.plugin.vcs

import ai.motadata.plugin.bridge.*
import ai.motadata.plugin.logging.DecisionLogger
import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.project.Project
import com.intellij.openapi.vcs.CheckinProjectPanel
import com.intellij.openapi.vcs.changes.CommitContext
import com.intellij.openapi.vcs.checkin.CheckinHandler
import com.intellij.openapi.vcs.checkin.CheckinHandlerFactory
import ai.motadata.plugin.util.GitInfoUtil

class MotadataCheckinHandlerFactory : CheckinHandlerFactory() {
    override fun createHandler(panel: CheckinProjectPanel, commitContext: CommitContext): CheckinHandler {
        return MotadataCheckinHandler(panel.project)
    }
}

/**
 * Governed commit interception handler.
 *
 * M3.4 Architecture:
 * - Uses RuntimeBridge as the single integration point
 * - Routes ALL commits through runtime governance
 * - Surfaces distinct outcomes (REFUSED, DEFERRED, BOUNDED_ALLOW, BLOCKED, EXECUTED)
 * - Fails closed if runtime unavailable in enforcing mode
 * - Shadow mode: logs decisions but allows commits to proceed
 * - Enforcing mode: blocks commits based on runtime decision
 *
 * NO BYPASS ALLOWED:
 * - Plugin does NOT make governance decisions
 * - Plugin does NOT reinterpret postures
 * - Plugin does NOT fallback to local execution
 */
class MotadataCheckinHandler(
    private val project: Project,
    private val bridge: RuntimeBridge = RuntimeBridge(),
    private val enforcingMode: Boolean = false
) : CheckinHandler() {

    override fun beforeCheckin(): ReturnResult {
        val gitInfo = GitInfoUtil.getGitInfo(project)
        val branch = gitInfo.branch
        val revision = gitInfo.revision
        val repoRoot = project.basePath ?: ""

        val request = RuntimeRequest(
            actionType = RuntimeActionType.VCS_COMMIT,
            repoRoot = repoRoot,
            revision = revision,
            branch = branch,
            ideContext = IdeContext(
                projectName = project.name
            ),
            clientPolicy = ClientPolicy(
                failClosedIfUnreachable = enforcingMode,
                mode = if (enforcingMode) "enforcing" else "shadow"
            )
        )

        val response = bridge.evaluateCommit(request)

        logDecision(response, repoRoot, branch, revision)
        showNotification(response)

        return determineResult(response)
    }

    private fun logDecision(response: RuntimeResponse, repoRoot: String, branch: String, revision: String) {
        val outcomeStr = buildOutcomeLogString(response)
        DecisionLogger.log(
            action = "commit",
            decision = outcomeStr,
            repoRoot = repoRoot,
            branch = branch,
            revision = revision
        )
    }

    private fun buildOutcomeLogString(response: RuntimeResponse): String {
        return buildString {
            append(response.outcome.name)
            if (enforcingMode) {
                append(" [ENFORCING]")
            } else {
                append(" [SHADOW]")
            }
            response.ledgerRowId?.let { append(" ledger=$it") }
            response.planHash?.let { append(" plan=${it.take(16)}...") }
        }
    }

    private fun showNotification(response: RuntimeResponse) {
        val (title, content, notificationType) = when (response.outcome) {
            RuntimeOutcome.RUNTIME_UNAVAILABLE -> {
                if (enforcingMode) {
                    Triple(
                        "Runtime unavailable — Commit blocked",
                        "Runtime service could not be reached. Commit cannot proceed in enforcing mode.\n${response.error ?: ""}",
                        NotificationType.ERROR
                    )
                } else {
                    Triple(
                        "Runtime unavailable (shadow mode)",
                        "Runtime service could not be reached. Proceeding without enforcement.\n${response.error ?: ""}",
                        NotificationType.WARNING
                    )
                }
            }

            RuntimeOutcome.REFUSED -> {
                val modeLabel = if (enforcingMode) "BLOCKED" else "shadow mode"
                Triple(
                    response.ui?.title ?: "Commit refused by runtime ($modeLabel)",
                    response.ui?.message
                        ?: "Runtime governance refused this commit.${if (!enforcingMode) " Would block in enforcing mode." else ""}",
                    NotificationType.ERROR
                )
            }

            RuntimeOutcome.DEFERRED -> {
                val modeLabel = if (enforcingMode) "BLOCKED" else "shadow mode"
                Triple(
                    response.ui?.title ?: "Commit deferred ($modeLabel)",
                    response.ui?.message
                        ?: "This commit requires additional approval. Deferred by runtime.${if (!enforcingMode) " Would block in enforcing mode." else ""}",
                    NotificationType.WARNING
                )
            }

            RuntimeOutcome.BOUNDED_ALLOW -> {
                Triple(
                    response.ui?.title ?: "Commit bounded-allowed (shadow mode)",
                    response.ui?.message
                        ?: "Runtime granted bounded allowance. No sandbox execution in this MVP path.",
                    NotificationType.WARNING
                )
            }

            RuntimeOutcome.BLOCKED -> {
                val modeLabel = if (enforcingMode) "BLOCKED" else "shadow mode"
                Triple(
                    response.ui?.title ?: "Commit blocked by policy ($modeLabel)",
                    response.ui?.message
                        ?: "Runtime/sandbox policy blocked this commit.${if (!enforcingMode) " Would block in enforcing mode." else ""}",
                    NotificationType.ERROR
                )
            }

            RuntimeOutcome.EXECUTED -> {
                Triple(
                    response.ui?.title ?: "Commit allowed by runtime",
                    response.ui?.message
                        ?: "Runtime governance approved this commit.",
                    NotificationType.INFORMATION
                )
            }

            RuntimeOutcome.UNKNOWN -> {
                Triple(
                    "Runtime returned unknown decision (shadow mode)",
                    "Decision could not be interpreted. Proceeding without enforcement.\n${response.error ?: ""}",
                    NotificationType.WARNING
                )
            }
        }

        notify(project, title, content, notificationType)
    }

    private fun determineResult(response: RuntimeResponse): ReturnResult {
        if (!enforcingMode) {
            return ReturnResult.COMMIT
        }

        return when (response.outcome) {
            RuntimeOutcome.EXECUTED -> ReturnResult.COMMIT
            RuntimeOutcome.BOUNDED_ALLOW -> ReturnResult.COMMIT
            RuntimeOutcome.RUNTIME_UNAVAILABLE -> ReturnResult.CANCEL
            RuntimeOutcome.REFUSED -> ReturnResult.CANCEL
            RuntimeOutcome.DEFERRED -> ReturnResult.CANCEL
            RuntimeOutcome.BLOCKED -> ReturnResult.CANCEL
            RuntimeOutcome.UNKNOWN -> ReturnResult.CANCEL
        }
    }

    private fun notify(project: Project, title: String, content: String, type: NotificationType) {
        val group = NotificationGroupManager.getInstance().getNotificationGroup("Motadata AI")
        group.createNotification(title, content, type).notify(project)
    }
}
