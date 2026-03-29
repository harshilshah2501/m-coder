package ai.motadata.plugin.actions

import ai.motadata.plugin.bridge.*
import ai.motadata.plugin.logging.DecisionLogger
import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.Messages
import ai.motadata.plugin.util.GitInfoUtil
import ai.motadata.plugin.util.ProjectWorkspacePaths

/**
 * Submit to Runtime — Explicit code-intent action through governed runtime path.
 *
 * M3.4 Architecture:
 * - Demonstrates plugin → runtime → Plan-Gate → sandbox (if allowed) path
 * - Routes through RuntimeBridge exclusively
 * - Surfaces all distinct outcomes (REFUSED, DEFERRED, BOUNDED_ALLOW, BLOCKED, EXECUTED, EXECUTED_FAILED)
 * - Does NOT execute locally
 * - Does NOT fallback if runtime unavailable
 *
 * This action is important because M3.4 should demonstrate more than just
 * commit interception and Ask. It shows one direct runtime-governed user action.
 */
class SubmitToRuntimeAction : AnAction() {

    private val bridge = RuntimeBridge()

    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return

        if (!bridge.isRuntimeAvailable()) {
            showRuntimeUnavailableDialog(project)
            return
        }

        val command = Messages.showInputDialog(
            project,
            buildString {
                appendLine("Enter a command or action to submit for governed execution.")
                appendLine()
                appendLine("This will route through the runtime Plan-Gate:")
                appendLine("  Plugin → Runtime → Plan-Gate → Sandbox (if allowed)")
                appendLine()
                appendLine("The runtime decides whether execution is permitted.")
                appendLine("No local execution will occur.")
            },
            "Submit to Runtime",
            Messages.getInformationIcon()
        ) ?: return

        if (command.isBlank()) {
            return
        }

        executeGovernedRequest(project, command)
    }

    private fun showRuntimeUnavailableDialog(project: Project) {
        Messages.showErrorDialog(
            project,
            buildString {
                appendLine("Runtime service is not available.")
                appendLine()
                appendLine("Cannot submit action for governed execution:")
                appendLine("  - Runtime must be running at http://127.0.0.1:8089")
                appendLine("  - No local fallback is permitted")
                appendLine("  - Action was NOT executed")
                appendLine()
                appendLine("Start the runtime service and try again.")
            },
            "Runtime Unavailable — Action Not Executed"
        )

        val repoRoot = ProjectWorkspacePaths.layer5WorkspaceRoot(project)
        DecisionLogger.log(
            action = "execute",
            decision = "RUNTIME_UNAVAILABLE [NO_FALLBACK]",
            repoRoot = repoRoot,
            branch = null,
            revision = null
        )
    }

    private fun executeGovernedRequest(project: Project, command: String) {
        val gitInfo = GitInfoUtil.getGitInfo(project)
        val branch = gitInfo.branch
        val revision = gitInfo.revision
        val repoRoot = ProjectWorkspacePaths.layer5WorkspaceRoot(project)

        val request = RuntimeRequest(
            actionType = RuntimeActionType.EXECUTE,
            repoRoot = repoRoot,
            revision = revision,
            branch = branch,
            payload = command,
            ideContext = IdeContext(projectName = project.name),
            clientPolicy = ClientPolicy(
                failClosedIfUnreachable = true,
                mode = "shadow"
            )
        )

        val response = bridge.requestExecution(request)

        logDecision(response, repoRoot, branch, revision)
        showOutcomeDialog(project, command, response)
    }

    private fun logDecision(response: RuntimeResponse, repoRoot: String, branch: String, revision: String) {
        val outcomeStr = buildString {
            append(response.outcome.name)
            if (response.wasExecuted) {
                append(" [EXECUTED]")
            } else {
                append(" [NOT_EXECUTED]")
            }
            response.ledgerRowId?.let { append(" ledger=$it") }
        }

        DecisionLogger.log(
            action = "execute",
            decision = outcomeStr,
            repoRoot = repoRoot,
            branch = branch,
            revision = revision
        )
    }

    private fun showOutcomeDialog(project: Project, command: String, response: RuntimeResponse) {
        val (title, message, icon) = when (response.outcome) {
            RuntimeOutcome.EXECUTED -> Triple(
                "Execution Complete",
                buildExecutedMessage(command, response),
                Messages.getInformationIcon()
            )

            RuntimeOutcome.EXECUTED_FAILED -> Triple(
                "Execution Failed",
                buildExecutedFailedMessage(command, response),
                Messages.getWarningIcon()
            )

            RuntimeOutcome.REFUSED -> Triple(
                "Execution Refused",
                buildRefusedMessage(command, response),
                Messages.getErrorIcon()
            )

            RuntimeOutcome.DEFERRED -> Triple(
                "Execution Deferred",
                buildDeferredMessage(command, response),
                Messages.getWarningIcon()
            )

            RuntimeOutcome.BOUNDED_ALLOW -> Triple(
                "Bounded Allowance",
                buildBoundedAllowMessage(command, response),
                Messages.getWarningIcon()
            )

            RuntimeOutcome.BLOCKED -> Triple(
                "Execution Blocked",
                buildBlockedMessage(command, response),
                Messages.getErrorIcon()
            )

            RuntimeOutcome.RUNTIME_UNAVAILABLE -> Triple(
                "Runtime Unavailable",
                buildRuntimeUnavailableMessage(command, response),
                Messages.getErrorIcon()
            )

            RuntimeOutcome.UNKNOWN -> Triple(
                "Unknown Outcome",
                buildUnknownMessage(command, response),
                Messages.getWarningIcon()
            )
        }

        Messages.showMessageDialog(project, message, title, icon)
    }

    private fun buildExecutedMessage(command: String, response: RuntimeResponse): String {
        return buildString {
            appendLine("═══════════════════════════════════════════")
            appendLine("  EXECUTED — Governed execution complete")
            appendLine("═══════════════════════════════════════════")
            appendLine()
            appendLine("Command: $command")
            appendLine()
            appendLine("Outcome: ${response.outcome.toHumanReadable()}")
            appendLine()
            response.reason?.let { appendLine("Reason: $it") }
            response.ledgerRowId?.let { appendLine("Ledger Row: $it") }
            response.planHash?.let { appendLine("Plan Hash: ${it.take(16)}...") }
            appendLine()
            appendLine("The action was executed through the governed sandbox.")
        }
    }

    private fun buildExecutedFailedMessage(command: String, response: RuntimeResponse): String {
        return buildString {
            appendLine("═══════════════════════════════════════════")
            appendLine("  EXECUTED — Run failed (not a policy block)")
            appendLine("═══════════════════════════════════════════")
            appendLine()
            appendLine("Command: $command")
            appendLine()
            appendLine("Outcome: ${response.outcome.toHumanReadable()}")
            appendLine()
            appendLine(
                "The sandbox ran this command; it did not succeed (e.g. non-zero exit). " +
                    "This is distinct from execution blocked before run."
            )
            appendLine()
            response.reason?.let { appendLine("Reason: $it") }
            response.ui?.message?.let { appendLine("Details: $it") }
            response.ledgerRowId?.let { appendLine("Ledger Row: $it") }
            response.planHash?.let { appendLine("Plan Hash: ${it.take(16)}...") }
        }
    }

    private fun buildRefusedMessage(command: String, response: RuntimeResponse): String {
        return buildString {
            appendLine("═══════════════════════════════════════════")
            appendLine("  REFUSED — Governance denied this action")
            appendLine("═══════════════════════════════════════════")
            appendLine()
            appendLine("Command: $command")
            appendLine()
            appendLine("Outcome: ${response.outcome.toHumanReadable()}")
            appendLine()
            appendLine("This is NOT a transient error.")
            appendLine("Runtime governance explicitly refused this action.")
            appendLine()
            response.reason?.let { appendLine("Reason: $it") }
            response.ui?.message?.let { appendLine("Details: $it") }
            appendLine()
            appendLine("The action was NOT executed.")
        }
    }

    private fun buildDeferredMessage(command: String, response: RuntimeResponse): String {
        return buildString {
            appendLine("═══════════════════════════════════════════")
            appendLine("  DEFERRED — Action not executed yet")
            appendLine("═══════════════════════════════════════════")
            appendLine()
            appendLine("Command: $command")
            appendLine()
            appendLine("Outcome: ${response.outcome.toHumanReadable()}")
            appendLine()
            appendLine("This action requires additional approval or context.")
            appendLine("It has been deferred, not refused outright.")
            appendLine()
            response.reason?.let { appendLine("Reason: $it") }
            appendLine()
            appendLine("The action was NOT executed.")
        }
    }

    private fun buildBoundedAllowMessage(command: String, response: RuntimeResponse): String {
        return buildString {
            appendLine("═══════════════════════════════════════════")
            appendLine("  BOUNDED ALLOW — No sandbox execution")
            appendLine("═══════════════════════════════════════════")
            appendLine()
            appendLine("Command: $command")
            appendLine()
            appendLine("Outcome: ${response.outcome.toHumanReadable()}")
            appendLine()
            appendLine("Runtime granted bounded-safe allowance.")
            appendLine("However, in this MVP, bounded_allow does NOT")
            appendLine("reach the sandbox for actual execution.")
            appendLine()
            response.reason?.let { appendLine("Reason: $it") }
            appendLine()
            appendLine("The action was NOT executed.")
            appendLine("This is intentional MVP behavior, not an error.")
        }
    }

    private fun buildBlockedMessage(command: String, response: RuntimeResponse): String {
        return buildString {
            appendLine("═══════════════════════════════════════════")
            appendLine("  BLOCKED — Policy blocked execution")
            appendLine("═══════════════════════════════════════════")
            appendLine()
            appendLine("Command: $command")
            appendLine()
            appendLine("Outcome: ${response.outcome.toHumanReadable()}")
            appendLine()
            appendLine("The execution path was reached but blocked")
            appendLine("by runtime or sandbox policy.")
            appendLine()
            response.reason?.let { appendLine("Reason: $it") }
            appendLine()
            appendLine("The action was NOT executed.")
        }
    }

    private fun buildRuntimeUnavailableMessage(command: String, response: RuntimeResponse): String {
        return buildString {
            appendLine("═══════════════════════════════════════════")
            appendLine("  RUNTIME UNAVAILABLE — Fail-closed")
            appendLine("═══════════════════════════════════════════")
            appendLine()
            appendLine("Command: $command")
            appendLine()
            appendLine("Runtime service could not be reached.")
            appendLine()
            appendLine("In governed execution mode, we FAIL CLOSED.")
            appendLine("No local fallback or bypass is permitted.")
            appendLine()
            response.error?.let { appendLine("Error: $it") }
            appendLine()
            appendLine("The action was NOT executed.")
        }
    }

    private fun buildUnknownMessage(command: String, response: RuntimeResponse): String {
        return buildString {
            appendLine("═══════════════════════════════════════════")
            appendLine("  UNKNOWN — Unexpected runtime response")
            appendLine("═══════════════════════════════════════════")
            appendLine()
            appendLine("Command: $command")
            appendLine()
            appendLine("Runtime returned an unexpected or invalid response.")
            appendLine()
            response.error?.let { appendLine("Error: $it") }
            response.reason?.let { appendLine("Reason: $it") }
            appendLine()
            appendLine("The action was NOT executed.")
        }
    }
}
