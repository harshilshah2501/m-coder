package ai.motadata.plugin.ask

import ai.motadata.plugin.bridge.*
import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.Messages
import git4idea.repo.GitRepositoryManager

/**
 * Ask Motadata AI Action — Plan-only query through runtime governance.
 *
 * M3.4 Architecture:
 * - Uses RuntimeBridge for all runtime communication
 * - Clearly marked as PLAN ONLY / no execution
 * - Surfaces runtime outcomes distinctly
 * - No local fallback planning
 *
 * This action demonstrates the governed Ask flow:
 * - Ask is planning-oriented, non-executing
 * - Response includes context bundle, plan summary
 * - Governance posture is always PLAN_ONLY
 */
class AskMotadataAiAction : AnAction() {

    private val bridge = RuntimeBridge()

    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return

        val question = Messages.showInputDialog(
            project,
            "Enter a question about this repository (PLAN ONLY, no execution):",
            "Ask Motadata AI",
            Messages.getQuestionIcon()
        ) ?: return

        if (question.isBlank()) {
            return
        }

        val repoManager = GitRepositoryManager.getInstance(project)
        val repo = repoManager.repositories.firstOrNull()
        val branch = repo?.currentBranchName ?: "unknown"
        val revision = repo?.currentRevision ?: "unknown-revision"

        val request = RuntimeRequest(
            actionType = RuntimeActionType.ASK_PLAN,
            repoRoot = project.basePath ?: "",
            revision = revision,
            branch = branch,
            payload = question,
            ideContext = IdeContext(projectName = project.name),
            clientPolicy = ClientPolicy(
                failClosedIfUnreachable = false,
                mode = "shadow"
            )
        )

        val response = bridge.askPlan(request)

        handleResponse(project, question, response)
    }

    private fun handleResponse(project: Project, question: String, response: RuntimeResponse) {
        when (response.outcome) {
            RuntimeOutcome.RUNTIME_UNAVAILABLE -> {
                notify(
                    project,
                    "Ask Motadata AI — Runtime Unavailable",
                    "Runtime service could not be reached.\n${response.error ?: "No error details."}",
                    NotificationType.WARNING
                )
            }

            RuntimeOutcome.UNKNOWN -> {
                notify(
                    project,
                    "Ask Motadata AI — Unknown Response",
                    "Runtime returned an unexpected response.\n${response.error ?: "No error details."}",
                    NotificationType.WARNING
                )
            }

            else -> {
                showPlanOnlyResult(project, question, response)
            }
        }
    }

    private fun showPlanOnlyResult(project: Project, question: String, response: RuntimeResponse) {
        val sb = StringBuilder()
        sb.appendLine("═══════════════════════════════════════════")
        sb.appendLine("  PLAN ONLY — No execution performed")
        sb.appendLine("═══════════════════════════════════════════")
        sb.appendLine()

        sb.appendLine("Query: $question")
        sb.appendLine()

        sb.appendLine("Governance Outcome: ${response.outcome.toHumanReadable()}")
        sb.appendLine()

        val contextBundle = response.metadata["context_bundle"] as? Map<*, *>
        if (contextBundle != null) {
            val revision = contextBundle["revision"]
            sb.appendLine("Context bundle @ ${revision ?: "unknown-revision"}")

            val files = contextBundle["files"] as? List<*>
            if (files.isNullOrEmpty()) {
                sb.appendLine("(no files selected)")
            } else {
                sb.appendLine("Files:")
                files.forEach { f ->
                    val fileMap = f as? Map<*, *>
                    val path = fileMap?.get("path")
                    val reason = fileMap?.get("selection_reason")
                    sb.appendLine("  - $path (reason: $reason)")
                }
            }
            sb.appendLine()

            val selectors = contextBundle["selectors_used"] as? List<*>
            if (!selectors.isNullOrEmpty()) {
                sb.appendLine("Selectors used: ${selectors.joinToString(", ")}")
                sb.appendLine()
            }
        }

        val planSummary = response.metadata["plan_summary"] as? Map<*, *>
        if (planSummary != null) {
            sb.appendLine("Plan:")
            val steps = planSummary["steps"] as? List<*>
            if (steps.isNullOrEmpty()) {
                sb.appendLine("  (no steps returned)")
            } else {
                steps.forEachIndexed { idx, step ->
                    sb.appendLine("  ${idx + 1}. $step")
                }
            }
        }

        sb.appendLine()
        sb.appendLine("───────────────────────────────────────────")
        sb.appendLine("This is a PLAN ONLY response.")
        sb.appendLine("No code was executed. No sandbox was invoked.")
        sb.appendLine("To execute actions, use 'Submit to Runtime'.")
        sb.appendLine("───────────────────────────────────────────")

        Messages.showInfoMessage(
            project,
            sb.toString(),
            "Ask Motadata AI — PLAN ONLY"
        )
    }

    private fun notify(project: Project, title: String, content: String, type: NotificationType) {
        val group = NotificationGroupManager.getInstance().getNotificationGroup("Motadata AI")
        group.createNotification(title, content, type).notify(project)
    }
}
