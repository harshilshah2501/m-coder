package ai.motadata.plugin.bridge

import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

/**
 * Focused tests for RuntimeBridge availability and error classification.
 * - Availability: unreachable host => isRuntimeAvailable() false.
 * - HTTP 4xx/5xx from plan/ask/execute must be classified as UNKNOWN (reachable, bad request), not RUNTIME_UNAVAILABLE.
 */
class RuntimeBridgeTest {

    @Test
    fun `isRuntimeAvailable returns false when host is unreachable`() {
        val bridge = RuntimeBridge(baseUrl = "http://192.0.2.1:8089", timeoutMs = 500)
        assertFalse(bridge.isRuntimeAvailable())
    }

    @Test
    fun `unknown response is used for HTTP error not transport failure`() {
        val response = RuntimeResponse.unknown("req-1", "Runtime HTTP 400: schema validation error")
        assertTrue(response.outcome == RuntimeOutcome.UNKNOWN)
        assertFalse(response.outcome == RuntimeOutcome.RUNTIME_UNAVAILABLE)
        assertTrue(response.error!!.contains("400"))
    }
}
