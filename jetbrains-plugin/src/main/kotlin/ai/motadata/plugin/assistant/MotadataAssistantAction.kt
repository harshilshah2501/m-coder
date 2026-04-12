package ai.motadata.plugin.assistant

import ai.motadata.plugin.actions.SubmitToRuntimeAction
import ai.motadata.plugin.ask.AskMotadataAiAction
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.ui.Messages

class MotadataAssistantAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        if (!HostContract.enforceOrShow(project, "assistant_shell")) {
            return
        }

        val options = arrayOf("Ask / Explain / Plan", "Execute")
        val selected = Messages.showDialog(
            project,
            "Choose assistant mode. Modes remain explicitly separated.",
            "Motadata Assistant",
            options,
            0,
            Messages.getQuestionIcon(),
        )
        if (selected < 0) return

        if (selected == 0) {
            AskMotadataAiAction().actionPerformed(e)
        } else {
            SubmitToRuntimeAction().actionPerformed(e)
        }
    }
}
