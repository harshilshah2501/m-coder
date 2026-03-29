package ai.motadata.plugin.util

import com.intellij.execution.configurations.GeneralCommandLine
import com.intellij.execution.process.CapturingProcessHandler
import com.intellij.execution.process.ProcessOutput
import com.intellij.openapi.project.Project
import java.io.File
import java.nio.charset.StandardCharsets

/**
 * Gets git branch and revision using platform process execution only.
 * Avoids dependency on git4idea plugin types (e.g. GitRepositoryManager) so the plugin
 * compiles against IntelliJ 2025.3 without requiring the dvcs bundled module.
 */
object GitInfoUtil {

    data class GitInfo(val branch: String, val revision: String)

    fun getGitInfo(project: Project): GitInfo {
        val workDir = ProjectWorkspacePaths.layer5WorkspaceRoot(project).ifBlank { null }
            ?: return GitInfo("unknown", "unknown-revision")
        val branch = runCommand(workDir, "git", "branch", "--show-current")?.trim().orEmpty()
        val revision = runCommand(workDir, "git", "rev-parse", "HEAD")?.trim().orEmpty()
        return GitInfo(
            branch = if (branch.isNotBlank()) branch else "unknown",
            revision = if (revision.isNotBlank()) revision else "unknown-revision"
        )
    }

    private fun runCommand(workDir: String, vararg command: String): String? {
        return try {
            val cmd = GeneralCommandLine(*command)
                .withWorkDirectory(File(workDir))
                .withCharset(StandardCharsets.UTF_8)
            val handler = CapturingProcessHandler(cmd)
            val output: ProcessOutput = handler.runProcess(30_000)
            if (output.exitCode == 0) output.stdout.trim() else null
        } catch (_: Exception) {
            null
        }
    }
}
