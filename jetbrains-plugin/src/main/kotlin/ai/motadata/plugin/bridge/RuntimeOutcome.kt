package ai.motadata.plugin.bridge

/**
 * Plugin-visible runtime outcomes.
 *
 * These map to the runtime postures but are plugin-facing,
 * ensuring the plugin does NOT collapse distinct outcomes.
 *
 * From M3.4 requirements:
 * - REFUSED: Runtime governance denied the action (governance/authority failure)
 * - DEFERRED: Action deferred, not executed (pending approval or escalation)
 * - BOUNDED_ALLOW: Bounded-safe allowance (no sandbox execution in MVP)
 * - BLOCKED: Execution path reached but blocked by runtime/sandbox policy
 * - EXECUTED: Execution completed through governed runtime path
 *
 * The plugin MUST NOT collapse these into generic SUCCESS/FAILURE.
 */
enum class RuntimeOutcome {
    /** Runtime/governance denied the action outright. */
    REFUSED,

    /** Action deferred for later evaluation (e.g., awaiting approval). */
    DEFERRED,

    /** Bounded-safe allowance; no sandbox execution occurred in MVP. */
    BOUNDED_ALLOW,

    /** Execution path was reached but blocked by runtime/sandbox policy. */
    BLOCKED,

    /** Action executed successfully through governed runtime path. */
    EXECUTED,

    /** Runtime was unavailable; action NOT executed (fail-closed). */
    RUNTIME_UNAVAILABLE,

    /** Unknown/unexpected response from runtime. */
    UNKNOWN;

    companion object {
        /**
         * Map runtime posture string to RuntimeOutcome.
         * Postures: refuse, defer, bounded_allow, safe_execute
         */
        fun fromPosture(posture: String?): RuntimeOutcome {
            return when (posture?.lowercase()) {
                "refuse" -> REFUSED
                "defer" -> DEFERRED
                "bounded_allow" -> BOUNDED_ALLOW
                "safe_execute" -> EXECUTED
                else -> UNKNOWN
            }
        }

        /**
         * Map legacy DecisionType to RuntimeOutcome for backward compatibility.
         */
        fun fromLegacyDecision(decision: String?): RuntimeOutcome {
            return when (decision?.uppercase()) {
                "REFUSAL" -> REFUSED
                "CONDITIONAL_BLOCK" -> DEFERRED
                "BOUNDING" -> BOUNDED_ALLOW
                "APPROVE" -> EXECUTED
                else -> UNKNOWN
            }
        }
    }

    /**
     * Whether this outcome should be treated as a success for UI purposes.
     * Note: Only EXECUTED is a true success. BOUNDED_ALLOW is NOT success.
     */
    val isSuccess: Boolean
        get() = this == EXECUTED

    /**
     * Whether this outcome represents an error condition requiring attention.
     */
    val isError: Boolean
        get() = this in listOf(REFUSED, BLOCKED, RUNTIME_UNAVAILABLE)

    /**
     * Whether the action was actually executed through the sandbox.
     */
    val wasExecuted: Boolean
        get() = this == EXECUTED

    /**
     * Human-readable description for UI.
     */
    fun toHumanReadable(): String {
        return when (this) {
            REFUSED -> "Refused by Runtime"
            DEFERRED -> "Deferred for Approval"
            BOUNDED_ALLOW -> "Bounded Allowance (No Execution)"
            BLOCKED -> "Blocked by Policy"
            EXECUTED -> "Executed Successfully"
            RUNTIME_UNAVAILABLE -> "Runtime Unavailable"
            UNKNOWN -> "Unknown Outcome"
        }
    }
}
