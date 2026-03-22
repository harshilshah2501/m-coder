package ai.motadata.plugin.bridge

/**
 * Result of asking the WSL Context Layer (HTTP / CLI / dev script) for `layer5.evidence_bundle.v1`.
 *
 * Used to separate **absent/unreachable** Context Layer (allowed controlled `/v0/ask` fallback)
 * from **reachable but failed** (must not silently masquerade as evidence-first success).
 */
sealed class EvidenceExportOutcome {
    data class Success(val bundleJson: String) : EvidenceExportOutcome()

    /** Transport failure, wrong host, timeout, or no provider succeeded — not an HTTP error body. */
    data class Unreachable(val detail: String? = null) : EvidenceExportOutcome()

    /**
     * Context Layer responded (or CLI exited with failure after being invoked).
     * Plugin must surface this; do not silently fall back to `/v0/ask` for evidence-first mode.
     */
    data class ServiceFailure(val httpStatus: Int, val responseBody: String) : EvidenceExportOutcome()
}
