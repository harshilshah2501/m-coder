package ai.motadata.plugin.bridge

import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.util.UUID

/**
 * Action types that the plugin can request from the runtime.
 */
enum class RuntimeActionType {
    /** VCS commit intent - check governance before commit */
    VCS_COMMIT,

    /** Ask/plan request - planning only, no execution */
    ASK_PLAN,

    /** Explicit execution request - governed code/command execution */
    EXECUTE,

    /** Validation request - check if action would be allowed */
    VALIDATE;

    fun toActionTypeString(): String {
        return when (this) {
            VCS_COMMIT -> "VCS_COMMIT_INTENT"
            ASK_PLAN -> "ASK_PLAN"
            EXECUTE -> "EXECUTE_INTENT"
            VALIDATE -> "VALIDATE_INTENT"
        }
    }
}

/**
 * Unified request envelope for plugin-to-runtime communication.
 *
 * All plugin requests to the runtime should use this envelope
 * to ensure consistent tracing, context, and governance.
 */
data class RuntimeRequest(
    /** Unique request identifier for tracing. */
    val requestId: String = "req-${UUID.randomUUID()}",

    /** Type of action being requested. */
    val actionType: RuntimeActionType,

    /** Optional task ID for multi-step workflows. */
    val taskId: String? = null,

    /** Repository root path. */
    val repoRoot: String,

    /** Git revision / commit SHA if available. */
    val revision: String? = null,

    /** Git branch name if available. */
    val branch: String? = null,

    /** Command or intent payload (e.g., query text, command to execute). */
    val payload: String? = null,

    /** Plan hash if this request relates to a prior plan. */
    val planHash: String? = null,

    /** IDE context metadata for tracing. */
    val ideContext: IdeContext,

    /** Timestamp of request creation. */
    val timestampUtc: String = Instant.now().atOffset(ZoneOffset.UTC)
        .format(DateTimeFormatter.ISO_INSTANT),

    /** Plugin client policy. */
    val clientPolicy: ClientPolicy = ClientPolicy()
) {
    /**
     * Convert to JSON-compatible map for serialization.
     */
    fun toMap(): Map<String, Any?> {
        return mapOf(
            "request_id" to requestId,
            "action_type" to actionType.toActionTypeString(),
            "task_id" to taskId,
            "repo_root" to repoRoot,
            "revision" to revision,
            "branch" to branch,
            "payload" to payload,
            "plan_hash" to planHash,
            "ide_context" to ideContext.toMap(),
            "timestamp_utc" to timestampUtc,
            "client_policy" to clientPolicy.toMap()
        ).filterValues { it != null }
    }
}

/**
 * IDE context for runtime tracing.
 */
data class IdeContext(
    /** IDE product family (e.g., "jetbrains"). */
    val product: String = "jetbrains",

    /** Specific IDE (e.g., "intellij", "pycharm"). */
    val ide: String = "intellij",

    /** Project name. */
    val projectName: String,

    /** Current user. */
    val user: String = System.getProperty("user.name") ?: "unknown-user"
) {
    fun toMap(): Map<String, Any> {
        return mapOf(
            "product" to product,
            "ide" to ide,
            "project" to projectName,
            "user" to user
        )
    }
}

/**
 * Client policy for runtime communication.
 */
data class ClientPolicy(
    /**
     * If true, the plugin must fail closed when runtime is unreachable.
     * For governed actions, this should be true.
     */
    val failClosedIfUnreachable: Boolean = true,

    /**
     * Operating mode: "shadow" or "enforcing".
     * Shadow mode logs but does not block; enforcing mode blocks.
     */
    val mode: String = "shadow"
) {
    fun toMap(): Map<String, Any> {
        return mapOf(
            "fail_closed_if_gate_unreachable" to failClosedIfUnreachable,
            "mode" to mode
        )
    }
}
