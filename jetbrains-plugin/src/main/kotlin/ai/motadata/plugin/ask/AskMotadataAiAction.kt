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
        val sb = StringBuilder()
        val explainDebug = response.metadata["explain_debug"] as? Map<*, *>

        if (explainDebug != null) {
            sb.appendLine("═══════════════════════════════════════════")
            sb.appendLine("  Explain/Debug — PLAN ONLY")
            sb.appendLine("═══════════════════════════════════════════")
            sb.appendLine()
            val err = explainDebug["error"] as? String
            if (err != null) {
                sb.appendLine("Reasoning unavailable: $err")
                sb.appendLine()
                sb.appendLine("No template steps were substituted. Ensure the reasoning service is running (e.g. vLLM) and MOTADATA_EXPLAIN_VLLM_URL is set if needed.")
            } else {
                (explainDebug["summary"] as? String)?.takeIf { it.isNotBlank() }?.let {
                    sb.appendLine("Summary")
                    sb.appendLine("──────")
                    sb.appendLine(it)
                    sb.appendLine()
                }
                (explainDebug["logic_flow"] as? String)?.takeIf { it.isNotBlank() }?.let {
                    sb.appendLine("Logic flow")
                    sb.appendLine("──────────")
                    sb.appendLine(it)
                    sb.appendLine()
                }
                (explainDebug["likely_bug_risk"] as? String)?.takeIf { it.isNotBlank() }?.let {
                    sb.appendLine("Likely bug/risk")
                    sb.appendLine("───────────────")
                    sb.appendLine(it)
                    sb.appendLine()
                }
                @Suppress("UNCHECKED_CAST")
                (explainDebug["evidence"] as? List<*>)?.filterIsInstance<String>()?.takeIf { it.isNotEmpty() }?.let { evidence ->
                    sb.appendLine("Evidence")
                    sb.appendLine("────────")
                    evidence.forEach { sb.appendLine("  • $it") }
                    sb.appendLine()
                }
                (explainDebug["confidence_limits"] as? String)?.takeIf { it.isNotBlank() }?.let {
                    sb.appendLine("Confidence / limitations")
                    sb.appendLine("─────────────────────────")
                    sb.appendLine(it)
                    sb.appendLine()
                }
            }
        } else {
            sb.appendLine("═══════════════════════════════════════════")
            sb.appendLine("  PLAN ONLY — No execution performed")
            sb.appendLine("═══════════════════════════════════════════")
            sb.appendLine()
            sb.appendLine("Query: $question")
            sb.appendLine()
            sb.appendLine("Governance Outcome: ${response.outcome.toHumanReadable()}")
            sb.appendLine()

            response.ui?.title?.takeIf { it.isNotBlank() }?.let { sb.appendLine(it) }
            response.ui?.message?.takeIf { it.isNotBlank() }?.let { sb.appendLine(it); sb.appendLine() }

            val evidenceBundle = response.metadata["evidence_bundle"] as? Map<*, *>
            val evidenceMeta = response.metadata["evidence_first_meta"] as? Map<*, *>
            val v1EvidenceAsk = (evidenceMeta?.get("ask_path") as? String) == "v1_evidence"

            if (evidenceBundle != null) {
                sb.appendLine("Grounding — layer5.evidence_bundle.v1 (primary)")
                sb.appendLine("────────────────────────────────────────")
                val hint = evidenceBundle["schema_hint"] ?: evidenceBundle["schema_version"]
                sb.appendLine("schema_hint: $hint")
                if (v1EvidenceAsk) {
                    sb.appendLine("ask_path: v1_evidence (POST /v1/ask)")
                }
                sb.appendLine()
                @Suppress("UNCHECKED_CAST")
                val entries = evidenceBundle["entries"] as? List<*>
                if (entries.isNullOrEmpty()) {
                    sb.appendLine("(no entries)")
                } else {
                    entries.forEachIndexed { i, raw ->
                        val ent = raw as? Map<*, *> ?: return@forEachIndexed
                        val path = ent["relative_path"] ?: ent["path"]
                        sb.appendLine("${i + 1}. $path  (retrieval_score=${ent["retrieval_score"]})")
                        @Suppress("UNCHECKED_CAST")
                        val sn = ent["snippet"] as? Map<*, *>
                        if (sn != null) {
                            val text = (sn["text"] as? String) ?: ""
                            val lines = text.replace("\r\n", "\n").trim().lines().take(5)
                            if (lines.isNotEmpty()) {
                                sb.appendLine("   preview:")
                                lines.forEach { line -> sb.appendLine("   | $line") }
                            }
                        }
                    }
                }
                sb.appendLine()
            }

            val contextBundle = response.metadata["context_bundle"] as? Map<*, *>
            if (contextBundle != null && !v1EvidenceAsk) {
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
            } else if (contextBundle != null && v1EvidenceAsk) {
                sb.appendLine("(Planner context is derived from evidence_bundle above; duplicate file list omitted.)")
                sb.appendLine()
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
        }

        sb.appendLine()
        sb.appendLine("───────────────────────────────────────────")
        sb.appendLine("This is a PLAN ONLY response. No code was executed.")
        sb.appendLine("To execute actions, use 'Submit to Runtime'.")
        sb.appendLine("───────────────────────────────────────────")

        Messages.showInfoMessage(
            project,
            sb.toString(),
            if (explainDebug != null) "Ask Motadata AI — Explain/Debug" else "Ask Motadata AI — PLAN ONLY"
        )
    }

    private fun notify(project: Project, title: String, content: String, type: NotificationType) {
        val group = NotificationGroupManager.getInstance().getNotificationGroup("Motadata AI")
        group.createNotification(title, content, type).notify(project)
    }
}
