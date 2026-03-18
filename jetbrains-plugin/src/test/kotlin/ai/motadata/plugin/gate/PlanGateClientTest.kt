package ai.motadata.plugin.gate

import com.google.gson.Gson
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class PlanGateClientTest {

    @Test
    fun `parseDecisionResponse maps basic fields`() {
        val json = """
            {
              "schema_version": "decision_response.v0.1",
              "request_id": "req-1",
              "decision": "REFUSAL",
              "constitutional_phase_emitted": "REF",
              "dominance_source": "REF",
              "irreversible_boundary_phrase": "prod_write",
              "boundary_phrase_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
              "boundary_type": "prod_write",
              "authority_verdict": "fail",
              "missing_evidence": [],
              "allowed_pre_boundary_actions": [],
              "blocked_actions": [],
              "reason_codes": ["MISSING_AUTHORITY"],
              "plan_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
              "ui": {
                "title": "Runtime would block",
                "message": "Missing approval for prod write.",
                "severity": "error"
              },
              "provenance_resolution": {
                "resolved_via": "lineage_index"
              }
            }
        """.trimIndent()

        val client = PlanGateClient(Gson())
        val result = client.parseDecisionResponse(json)

        assertEquals(PlanGateClient.DecisionType.REFUSAL, result.decision)
        assertEquals("Runtime would block", result.ui?.title)
        assertEquals("Missing approval for prod write.", result.ui?.message)
        assertEquals("error", result.ui?.severity)
    }
}

