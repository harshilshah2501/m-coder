package ai.motadata.plugin.bridge

/**
 * Unified response from runtime governance.
 *
 * Contains the outcome, UX information, and audit details.
 * The plugin MUST surface these outcomes distinctly—no collapsing.
 */
data class RuntimeResponse(
    /** The governed outcome (REFUSED, DEFERRED, BOUNDED_ALLOW, BLOCKED, EXECUTED, etc.). */
    val outcome: RuntimeOutcome,

    /** Request ID echoed back for correlation. */
    val requestId: String?,

    /** UX information from runtime. */
    val ui: RuntimeUi? = null,

    /** Detailed reason for the decision. */
    val reason: String? = null,

    /** Whether the action was actually executed. */
    val wasExecuted: Boolean = false,

    /** Ledger row ID if recorded. */
    val ledgerRowId: String? = null,

    /** Plan hash from runtime (for audit trail). */
    val planHash: String? = null,

    /** Error message if runtime call failed. */
    val error: String? = null,

    /** Additional metadata from runtime. */
    val metadata: Map<String, Any?> = emptyMap()
) {
    companion object {
        /**
         * Create a response for runtime unavailable scenario.
         */
        fun runtimeUnavailable(requestId: String?, error: String): RuntimeResponse {
            return RuntimeResponse(
                outcome = RuntimeOutcome.RUNTIME_UNAVAILABLE,
                requestId = requestId,
                error = error,
                reason = "Runtime service could not be reached. Action not executed.",
                wasExecuted = false
            )
        }

        /**
         * Create a response for unknown/invalid runtime response.
         */
        fun unknown(requestId: String?, error: String): RuntimeResponse {
            return RuntimeResponse(
                outcome = RuntimeOutcome.UNKNOWN,
                requestId = requestId,
                error = error,
                reason = "Runtime returned an unexpected or invalid response.",
                wasExecuted = false
            )
        }
    }

    /**
     * Whether this response indicates the plugin should proceed with the action.
     * For shadow mode, this may differ from actual enforcement.
     */
    fun shouldProceed(shadowMode: Boolean): Boolean {
        return if (shadowMode) {
            true
        } else {
            outcome == RuntimeOutcome.EXECUTED
        }
    }

    /**
     * Get appropriate notification severity for this outcome.
     */
    fun getSeverity(): RuntimeSeverity {
        return when (outcome) {
            RuntimeOutcome.EXECUTED -> RuntimeSeverity.INFO
            RuntimeOutcome.BOUNDED_ALLOW -> RuntimeSeverity.WARNING
            RuntimeOutcome.DEFERRED -> RuntimeSeverity.WARNING
            RuntimeOutcome.REFUSED -> RuntimeSeverity.ERROR
            RuntimeOutcome.BLOCKED -> RuntimeSeverity.ERROR
            RuntimeOutcome.RUNTIME_UNAVAILABLE -> RuntimeSeverity.ERROR
            RuntimeOutcome.UNKNOWN -> RuntimeSeverity.WARNING
        }
    }
}

/**
 * UX information from runtime for display in IDE.
 */
data class RuntimeUi(
    val title: String?,
    val message: String?,
    val severity: String?
)

/**
 * Notification severity levels.
 */
enum class RuntimeSeverity {
    INFO,
    WARNING,
    ERROR
}
