package ai.motadata.plugin.ask

import ai.motadata.plugin.assistant.HostContract
import ai.motadata.plugin.bridge.*
import ai.motadata.plugin.logging.DecisionLogger
import com.intellij.notification.NotificationAction
import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.ide.CopyPasteManager
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.Messages
import java.awt.datatransfer.StringSelection
import ai.motadata.plugin.util.GitInfoUtil
import ai.motadata.plugin.util.ProjectWorkspacePaths

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
        if (!HostContract.enforceOrShow(project, "ask_explain_plan")) {
            return
        }

        val editor = e.getData(CommonDataKeys.EDITOR)
        val virtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE)
        val selectionText = editor?.selectionModel?.selectedText
        val anchorForWorkspace = virtualFile ?: editor?.virtualFile
        val workspaceRoot = ProjectWorkspacePaths.layer5WorkspaceRoot(project, anchorForWorkspace)
        val selectedFileRepoRelative: String? = if (virtualFile != null) {
            ProjectWorkspacePaths.relativePathIfUnder(workspaceRoot, virtualFile.path) ?: virtualFile.name
        } else {
            null
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
            repoRoot = workspaceRoot,
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

        logAskDecision(response, workspaceRoot, branch, revision, if (useExplainDebug) "explain_debug" else "ask_plan")
        handleResponse(project, q, response)
    }

    private fun logAskDecision(
        response: RuntimeResponse,
        repoRoot: String,
        branch: String,
        revision: String,
        mode: String,
    ) {
        val routingMode = response.metadata["routing_mode"] as? String ?: "(none)"
        val pluginRoute = response.metadata[AskPluginRouting.METADATA_KEY] as? String ?: "(none)"
        val traceId = response.metadata["trace_id"] as? String ?: "(none)"
        val evidenceMeta = response.metadata["evidence_first_meta"] as? Map<*, *>
        val askPath = evidenceMeta?.get("ask_path")?.toString() ?: "(none)"
        val hasEvidenceBundle = response.metadata["evidence_bundle"] != null
        val planSummary = response.metadata["plan_summary"] as? Map<*, *>
        @Suppress("UNCHECKED_CAST")
        val notes = planSummary?.get("notes") as? List<*>
        val notesPresent = !(notes.isNullOrEmpty())
        @Suppress("UNCHECKED_CAST")
        val decision = response.metadata["plugin_ask_routing_decision"] as? Map<*, *>
        val fallbackReason = decision?.get("reason")?.toString() ?: "(none)"

        val decisionStr =
            "mode=$mode outcome=${response.outcome.name} path=$askPath routing_mode=$routingMode plugin_route=$pluginRoute trace_id=$traceId evidence_bundle=$hasEvidenceBundle notes_present=$notesPresent fallback_reason=$fallbackReason"

        DecisionLogger.log(
            action = "ask",
            decision = decisionStr,
            repoRoot = repoRoot,
            branch = branch,
            revision = revision,
        )
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
        val fullBody = buildAskResultDialogMessage(question, response)
        val summary = buildAskResultSummaryMessage(question, response)
        val title =
            if (isExplainDebugAskUi(response)) "Ask Motadata AI — Explain/Debug" else "Ask Motadata AI — PLAN ONLY"

        val group = NotificationGroupManager.getInstance().getNotificationGroup("Motadata AI")
        if (group == null) {
            Messages.showInfoMessage(project, fullBody, title)
            return
        }

        val pluginRoute = response.metadata[AskPluginRouting.METADATA_KEY] as? String
        val notifyType = when (pluginRoute) {
            AskPluginRouting.V0_AFTER_V1_HTTP_FALLBACK,
            AskPluginRouting.CONTEXT_EXPORT_THEN_V0,
            -> NotificationType.WARNING
            else -> NotificationType.INFORMATION
        }
        val notification = group.createNotification(title, summary, notifyType)
        notification.addAction(
            NotificationAction.createSimple("View full response") {
                Messages.showInfoMessage(project, fullBody, title)
            }
        )
        notification.addAction(
            NotificationAction.createSimple("Copy full response") {
                CopyPasteManager.getInstance().setContents(StringSelection(fullBody))
            }
        )
        notification.notify(project)
    }

    private fun notify(project: Project, title: String, content: String, type: NotificationType) {
        val group = NotificationGroupManager.getInstance().getNotificationGroup("Motadata AI")
        group.createNotification(title, content, type).notify(project)
    }
}
