package ai.motadata.plugin.logging

import java.io.File
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.StandardOpenOption
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

object DecisionLogger {

    private val logPath: Path by lazy {
        val home = System.getProperty("user.home") ?: "."
        val dir = File(home, ".motadata-ai")
        if (!dir.exists()) {
            dir.mkdirs()
        }
        File(dir, "plugin-decisions.log").toPath()
    }

    fun log(
        action: String,
        decision: String,
        repoRoot: String?,
        branch: String?,
        revision: String?
    ) {
        val timestamp = Instant.now().atOffset(ZoneOffset.UTC)
            .format(DateTimeFormatter.ISO_INSTANT)
        val line = buildString {
            append(timestamp)
            append(" | action=")
            append(action)
            append(" | decision=")
            append(decision)
            append(" | repo=")
            append(repoRoot ?: "")
            append(" | branch=")
            append(branch ?: "")
            append(" | revision=")
            append(revision ?: "")
            append("\n")
        }

        try {
            Files.write(
                logPath,
                line.toByteArray(Charsets.UTF_8),
                StandardOpenOption.CREATE,
                StandardOpenOption.APPEND
            )
        } catch (_: Exception) {
            // Logging must never break IDE behavior.
        }
    }
}

