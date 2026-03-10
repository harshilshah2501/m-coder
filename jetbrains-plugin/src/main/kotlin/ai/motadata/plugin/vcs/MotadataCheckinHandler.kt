package ai.motadata.plugin.vcs

import ai.motadata.plugin.gate.PlanGateClient
import ai.motadata.plugin.gate.PlanGateClient.DecisionType
import ai.motadata.plugin.logging.DecisionLogger
import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.project.Project
import com.intellij.openapi.vcs.checkin.CheckinHandler
import com.intellij.openapi.vcs.checkin.CheckinHandlerFactory
import com.intellij.openapi.vcs.checkin.CheckinProjectPanel
import git4idea.repo.GitRepositoryManager

class MotadataCheckinHandlerFactory : CheckinHandlerFactory() {
    override fun createHandler(panel: CheckinProjectPanel): CheckinHandler {
        return MotadataCheckinHandler(panel.project)
    }
}

class MotadataCheckinHandler(
    private val project: Project,
    private val client: PlanGateClient = PlanGateClient()
) : CheckinHandler() {

    override fun beforeCheckin(): ReturnResult {
        val decisionResult = client.evaluateCommit(project)

        val repoManager = GitRepositoryManager.getInstance(project)
        val repo = repoManager.repositories.firstOrNull()
        val branch = repo?.currentBranchName ?: "unknown"
        val revision = repo?.currentRevision ?: "unknown-revision"
        val repoRoot = project.basePath ?: ""

        val decision = decisionResult.decision

        when {
            decisionResult.error != null -> {
                // Shadow mode: warn but do not block.
                notify(
                    project,
                    title = "Plan-Gate unavailable (shadow mode)",
                    content = "Runtime gate could not be reached; proceeding without enforcement.\n${decisionResult.error}",
                    type = NotificationType.WARNING
                )
            }
            decision == DecisionType.REFUSAL -> {
                notify(
                    project,
                    title = decisionResult.ui?.title ?: "Runtime would block this commit",
                    content = decisionResult.ui?.message
                        ?: "Plan-Gate decision: REFUSAL (shadow mode). Runtime would block this commit.",
                    type = NotificationType.ERROR
                )
            }
            decision == DecisionType.CONDITIONAL_BLOCK || decision == DecisionType.BOUNDING -> {
                notify(
                    project,
                    title = decisionResult.ui?.title ?: "Runtime would conditionally block this commit",
                    content = decisionResult.ui?.message
                        ?: "Plan-Gate decision: CONDITIONAL_BLOCK (shadow mode). Runtime would conditionally block / bounded-allow this commit.",
                    type = NotificationType.WARNING
                )
            }
            decision == DecisionType.APPROVE -> {
                // Optional info; can be disabled later if noisy.
                notify(
                    project,
                    title = decisionResult.ui?.title ?: "Runtime would allow this commit",
                    content = decisionResult.ui?.message
                        ?: "Plan-Gate decision: APPROVE (shadow mode). Runtime would allow this commit.",
                    type = NotificationType.INFORMATION
                )
            }
            else -> {
                // Unknown decision: warn but proceed.
                notify(
                    project,
                    title = "Plan-Gate returned unknown decision (shadow mode)",
                    content = "Decision type: $decision. Proceeding without enforcement.",
                    type = NotificationType.WARNING
                )
            }
        }

        DecisionLogger.log(
            action = "commit",
            decision = decision.name,
            repoRoot = repoRoot,
            branch = branch,
            revision = revision
        )

        // Shadow mode: commit must always proceed.
        return ReturnResult.COMMIT
    }

    private fun notify(project: Project, title: String, content: String, type: NotificationType) {
        val group = NotificationGroupManager.getInstance().getNotificationGroup("Motadata AI")
        group.createNotification(title, content, type).notify(project)
    }
}

