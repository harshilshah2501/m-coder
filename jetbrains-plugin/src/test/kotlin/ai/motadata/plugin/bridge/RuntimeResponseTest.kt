package ai.motadata.plugin.bridge

import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test

class RuntimeResponseTest {

    @Test
    fun `runtimeUnavailable creates correct response`() {
        val response = RuntimeResponse.runtimeUnavailable("req-123", "Connection refused")
        
        assertEquals(RuntimeOutcome.RUNTIME_UNAVAILABLE, response.outcome)
        assertEquals("req-123", response.requestId)
        assertEquals("Connection refused", response.error)
        assertFalse(response.wasExecuted)
        assertNotNull(response.reason)
    }

    @Test
    fun `unknown creates correct response`() {
        val response = RuntimeResponse.unknown("req-456", "Invalid JSON")
        
        assertEquals(RuntimeOutcome.UNKNOWN, response.outcome)
        assertEquals("req-456", response.requestId)
        assertEquals("Invalid JSON", response.error)
        assertFalse(response.wasExecuted)
    }

    @Test
    fun `shouldProceed in shadow mode always returns true`() {
        val executedResponse = RuntimeResponse(RuntimeOutcome.EXECUTED, "req-1")
        val refusedResponse = RuntimeResponse(RuntimeOutcome.REFUSED, "req-2")
        val unavailableResponse = RuntimeResponse(RuntimeOutcome.RUNTIME_UNAVAILABLE, "req-3")

        assertTrue(executedResponse.shouldProceed(shadowMode = true))
        assertTrue(refusedResponse.shouldProceed(shadowMode = true))
        assertTrue(unavailableResponse.shouldProceed(shadowMode = true))
    }

    @Test
    fun `shouldProceed in enforcing mode only returns true for EXECUTED`() {
        val executedResponse = RuntimeResponse(RuntimeOutcome.EXECUTED, "req-1")
        val refusedResponse = RuntimeResponse(RuntimeOutcome.REFUSED, "req-2")
        val deferredResponse = RuntimeResponse(RuntimeOutcome.DEFERRED, "req-3")
        val boundedResponse = RuntimeResponse(RuntimeOutcome.BOUNDED_ALLOW, "req-4")
        val blockedResponse = RuntimeResponse(RuntimeOutcome.BLOCKED, "req-5")
        val unavailableResponse = RuntimeResponse(RuntimeOutcome.RUNTIME_UNAVAILABLE, "req-6")
        val executedFailedResponse = RuntimeResponse(RuntimeOutcome.EXECUTED_FAILED, "req-7")

        assertTrue(executedResponse.shouldProceed(shadowMode = false))
        assertFalse(refusedResponse.shouldProceed(shadowMode = false))
        assertFalse(deferredResponse.shouldProceed(shadowMode = false))
        assertFalse(boundedResponse.shouldProceed(shadowMode = false))
        assertFalse(blockedResponse.shouldProceed(shadowMode = false))
        assertFalse(unavailableResponse.shouldProceed(shadowMode = false))
        assertFalse(executedFailedResponse.shouldProceed(shadowMode = false))
    }

    @Test
    fun `getSeverity returns correct severity for each outcome`() {
        assertEquals(RuntimeSeverity.INFO, RuntimeResponse(RuntimeOutcome.EXECUTED, "").getSeverity())
        assertEquals(RuntimeSeverity.WARNING, RuntimeResponse(RuntimeOutcome.BOUNDED_ALLOW, "").getSeverity())
        assertEquals(RuntimeSeverity.WARNING, RuntimeResponse(RuntimeOutcome.DEFERRED, "").getSeverity())
        assertEquals(RuntimeSeverity.ERROR, RuntimeResponse(RuntimeOutcome.REFUSED, "").getSeverity())
        assertEquals(RuntimeSeverity.ERROR, RuntimeResponse(RuntimeOutcome.BLOCKED, "").getSeverity())
        assertEquals(RuntimeSeverity.ERROR, RuntimeResponse(RuntimeOutcome.RUNTIME_UNAVAILABLE, "").getSeverity())
        assertEquals(RuntimeSeverity.WARNING, RuntimeResponse(RuntimeOutcome.UNKNOWN, "").getSeverity())
        assertEquals(RuntimeSeverity.WARNING, RuntimeResponse(RuntimeOutcome.EXECUTED_FAILED, "").getSeverity())
    }

    @Test
    fun `response preserves all metadata`() {
        val response = RuntimeResponse(
            outcome = RuntimeOutcome.EXECUTED,
            requestId = "req-full",
            ui = RuntimeUi("Title", "Message", "info"),
            reason = "All checks passed",
            wasExecuted = true,
            ledgerRowId = "ledger-123",
            planHash = "abc123",
            metadata = mapOf("key" to "value")
        )

        assertEquals(RuntimeOutcome.EXECUTED, response.outcome)
        assertEquals("req-full", response.requestId)
        assertEquals("Title", response.ui?.title)
        assertEquals("Message", response.ui?.message)
        assertEquals("info", response.ui?.severity)
        assertEquals("All checks passed", response.reason)
        assertTrue(response.wasExecuted)
        assertEquals("ledger-123", response.ledgerRowId)
        assertEquals("abc123", response.planHash)
        assertEquals("value", response.metadata["key"])
    }
}
