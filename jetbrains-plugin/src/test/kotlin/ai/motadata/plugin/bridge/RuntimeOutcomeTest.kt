package ai.motadata.plugin.bridge

import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test

class RuntimeOutcomeTest {

    @Test
    fun `fromPosture maps refuse correctly`() {
        assertEquals(RuntimeOutcome.REFUSED, RuntimeOutcome.fromPosture("refuse"))
        assertEquals(RuntimeOutcome.REFUSED, RuntimeOutcome.fromPosture("REFUSE"))
        assertEquals(RuntimeOutcome.REFUSED, RuntimeOutcome.fromPosture("Refuse"))
    }

    @Test
    fun `fromPosture maps defer correctly`() {
        assertEquals(RuntimeOutcome.DEFERRED, RuntimeOutcome.fromPosture("defer"))
        assertEquals(RuntimeOutcome.DEFERRED, RuntimeOutcome.fromPosture("DEFER"))
    }

    @Test
    fun `fromPosture maps bounded_allow correctly`() {
        assertEquals(RuntimeOutcome.BOUNDED_ALLOW, RuntimeOutcome.fromPosture("bounded_allow"))
        assertEquals(RuntimeOutcome.BOUNDED_ALLOW, RuntimeOutcome.fromPosture("BOUNDED_ALLOW"))
    }

    @Test
    fun `fromPosture maps safe_execute correctly`() {
        assertEquals(RuntimeOutcome.EXECUTED, RuntimeOutcome.fromPosture("safe_execute"))
        assertEquals(RuntimeOutcome.EXECUTED, RuntimeOutcome.fromPosture("SAFE_EXECUTE"))
    }

    @Test
    fun `fromPosture returns UNKNOWN for invalid values`() {
        assertEquals(RuntimeOutcome.UNKNOWN, RuntimeOutcome.fromPosture(null))
        assertEquals(RuntimeOutcome.UNKNOWN, RuntimeOutcome.fromPosture(""))
        assertEquals(RuntimeOutcome.UNKNOWN, RuntimeOutcome.fromPosture("invalid"))
    }

    @Test
    fun `fromLegacyDecision maps REFUSAL correctly`() {
        assertEquals(RuntimeOutcome.REFUSED, RuntimeOutcome.fromLegacyDecision("REFUSAL"))
        assertEquals(RuntimeOutcome.REFUSED, RuntimeOutcome.fromLegacyDecision("refusal"))
    }

    @Test
    fun `fromLegacyDecision maps CONDITIONAL_BLOCK correctly`() {
        assertEquals(RuntimeOutcome.DEFERRED, RuntimeOutcome.fromLegacyDecision("CONDITIONAL_BLOCK"))
    }

    @Test
    fun `fromLegacyDecision maps BOUNDING correctly`() {
        assertEquals(RuntimeOutcome.BOUNDED_ALLOW, RuntimeOutcome.fromLegacyDecision("BOUNDING"))
    }

    @Test
    fun `fromLegacyDecision maps APPROVE correctly`() {
        assertEquals(RuntimeOutcome.EXECUTED, RuntimeOutcome.fromLegacyDecision("APPROVE"))
    }

    @Test
    fun `isSuccess is true only for EXECUTED`() {
        assertTrue(RuntimeOutcome.EXECUTED.isSuccess)
        assertFalse(RuntimeOutcome.REFUSED.isSuccess)
        assertFalse(RuntimeOutcome.DEFERRED.isSuccess)
        assertFalse(RuntimeOutcome.BOUNDED_ALLOW.isSuccess)
        assertFalse(RuntimeOutcome.BLOCKED.isSuccess)
        assertFalse(RuntimeOutcome.RUNTIME_UNAVAILABLE.isSuccess)
        assertFalse(RuntimeOutcome.UNKNOWN.isSuccess)
        assertFalse(RuntimeOutcome.EXECUTED_FAILED.isSuccess)
    }

    @Test
    fun `isError is true for error conditions`() {
        assertTrue(RuntimeOutcome.REFUSED.isError)
        assertTrue(RuntimeOutcome.BLOCKED.isError)
        assertTrue(RuntimeOutcome.RUNTIME_UNAVAILABLE.isError)
        assertFalse(RuntimeOutcome.EXECUTED.isError)
        assertFalse(RuntimeOutcome.DEFERRED.isError)
        assertFalse(RuntimeOutcome.BOUNDED_ALLOW.isError)
        assertTrue(RuntimeOutcome.EXECUTED_FAILED.isError)
    }

    @Test
    fun `wasExecuted is true for EXECUTED and EXECUTED_FAILED`() {
        assertTrue(RuntimeOutcome.EXECUTED.wasExecuted)
        assertTrue(RuntimeOutcome.EXECUTED_FAILED.wasExecuted)
        assertFalse(RuntimeOutcome.REFUSED.wasExecuted)
        assertFalse(RuntimeOutcome.BOUNDED_ALLOW.wasExecuted)
        assertFalse(RuntimeOutcome.RUNTIME_UNAVAILABLE.wasExecuted)
    }

    @Test
    fun `toHumanReadable returns descriptive strings`() {
        assertEquals("Refused by Runtime", RuntimeOutcome.REFUSED.toHumanReadable())
        assertEquals("Deferred for Approval", RuntimeOutcome.DEFERRED.toHumanReadable())
        assertEquals("Bounded Allowance (No Execution)", RuntimeOutcome.BOUNDED_ALLOW.toHumanReadable())
        assertEquals("Blocked by Policy", RuntimeOutcome.BLOCKED.toHumanReadable())
        assertEquals("Executed Successfully", RuntimeOutcome.EXECUTED.toHumanReadable())
        assertEquals("Executed but Failed", RuntimeOutcome.EXECUTED_FAILED.toHumanReadable())
        assertEquals("Runtime Unavailable", RuntimeOutcome.RUNTIME_UNAVAILABLE.toHumanReadable())
        assertEquals("Unknown Outcome", RuntimeOutcome.UNKNOWN.toHumanReadable())
    }

    @Test
    fun `all outcomes are distinct - no collapsing`() {
        val outcomes = RuntimeOutcome.values()
        assertEquals(8, outcomes.size)
        assertEquals(outcomes.toSet().size, outcomes.size)
    }
}
