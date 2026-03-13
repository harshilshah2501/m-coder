package ai.motadata.plugin.ask

import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.Messages

class AskMotadataAiAction : AnAction() {

    private val client = AskClient()

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

        val result = client.ask(project, question)

        if (!result.success) {
            val message = result.error ?: "Ask service unavailable or returned invalid response."
            notify(project, "Ask Motadata AI failed (PLAN ONLY)", message, NotificationType.WARNING)
            return
        }

        val sb = StringBuilder()
        sb.appendLine("PLAN ONLY — No execution performed")
        sb.appendLine()
        sb.appendLine("Context bundle @ ${result.contextRevision ?: "unknown-revision"}")
        if (result.files.isEmpty()) {
            sb.appendLine("(no files selected)")
        } else {
            sb.appendLine("Files:")
            result.files.forEach { f ->
                sb.appendLine("- ${f.path} (reason: ${f.selectionReason})")
            }
        }
        sb.appendLine()
        if (result.selectorsUsed.isNotEmpty()) {
            sb.appendLine("Selectors used: ${result.selectorsUsed.joinToString(", ")}")
            sb.appendLine()
        }
        sb.appendLine("Plan:")
        if (result.planSteps.isEmpty()) {
            sb.appendLine("(no steps returned)")
        } else {
            result.planSteps.forEachIndexed { idx, step ->
                sb.appendLine("${idx + 1}. $step")
            }
        }

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

