package ai.motadata.plugin.ask

import ai.motadata.plugin.bridge.*
import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.Messages
import ai.motadata.plugin.util.GitInfoUtil

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

        val editor = e.getData(CommonDataKeys.EDITOR)
        val virtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE)
        val selectionText = editor?.selectionModel?.selectedText
        val basePath = project.basePath
        val selectedFileRepoRelative: String? = if (virtualFile != null && basePath != null && virtualFile.path.startsWith(basePath)) {
            virtualFile.path.removePrefix(basePath).trimStart('/', '\\')
        } else {
            virtualFile?.name
        }

        val promptMessage = if (selectionText.isNullOrBlank()) {
            "Enter a question about this repository (PLAN ONLY, no execution):"
        } else {
            "Explain/Debug selected code (PLAN ONLY). Optional: add a question or leave as-is:"
        }
        @Suppress("DialogTitleCapitalization")
        val question = Messages.showInputDialog(
            project,
            promptMessage,
            "Ask Motadata AI",
            Messages.getQuestionIcon()
        ) ?: return
        val q = question.takeIf { it.isNotBlank() } ?: return

        val gitInfo = GitInfoUtil.getGitInfo(project)
        val branch = gitInfo.branch
        val revision = gitInfo.revision

        val useExplainDebug = !selectionText.isNullOrBlank() && !selectedFileRepoRelative.isNullOrBlank()

        val request = RuntimeRequest(
            actionType = RuntimeActionType.ASK_PLAN,
            repoRoot = project.basePath ?: "",
            revision = revision,
            branch = branch,
            payload = q,
            ideContext = IdeContext(projectName = project.name),
            clientPolicy = ClientPolicy(
                failClosedIfUnreachable = false,
                mode = "shadow"
            ),
            selectedFile = selectedFileRepoRelative,
            selection = selectionText,
            taskType = if (useExplainDebug) "EXPLAIN_DEBUG" else null,
            evidenceFirst = MotadataAskFlags.isEvidenceFirstAskEnabled()
        )

        val response = bridge.askPlan(request)

        handleResponse(project, q, response)
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
        val explainDebug = response.metadata["explain_debug"] as? Map<*, *>
        val body = buildAskResultDialogMessage(question, response)
        Messages.showInfoMessage(
            project,
            body,
            if (explainDebug != null) "Ask Motadata AI — Explain/Debug" else "Ask Motadata AI — PLAN ONLY"
        )
    }

    private fun notify(project: Project, title: String, content: String, type: NotificationType) {
        val group = NotificationGroupManager.getInstance().getNotificationGroup("Motadata AI")
        group.createNotification(title, content, type).notify(project)
    }
}
