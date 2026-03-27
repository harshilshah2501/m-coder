package ai.motadata.plugin.bridge

import org.junit.jupiter.api.Assertions.assertEquals
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

    @Test
    fun `parseAskResponse preserves backend metadata and context_resolution`() {
        val json = """
            {
              "schema_version": "plan_only_response.v0.1",
              "request_id": "req-x",
              "timestamp_utc": "2026-01-01T00:00:00Z",
              "governance_posture": "PLAN_ONLY",
              "execution": false,
              "context_bundle": { "revision": "r", "files": [], "selectors_used": [] },
              "plan_summary": { "steps": [] },
              "ui": { "title": "t", "message": "m", "severity": "info" },
              "metadata": {
                "intent_type": "CODE_INTENT",
                "evidence_quality": "INSUFFICIENT",
                "quality_reasons": ["R1"],
                "dominance_metrics": { "top_k_size": 8.0 },
                "policy_version": "quality_gate.v1"
              },
              "context_resolution": {
                "requested_repo_root": "/a",
                "effective_repo_root": "/b",
                "fallback_used": true
              },
              "evidence_first_meta": {
                "ask_path": "v1_evidence",
                "context_source": "layer5.evidence_bundle.v1",
                "no_context_engine": true
              }
            }
        """.trimIndent()

        val bridge = RuntimeBridge()
        val r = bridge.parseAskResponse("req-x", json)
        @Suppress("UNCHECKED_CAST")
        val bm = r.metadata["backend_metadata"] as Map<String, Any?>
        assertEquals("CODE_INTENT", bm["intent_type"])
        assertEquals("INSUFFICIENT", bm["evidence_quality"])
        @Suppress("UNCHECKED_CAST")
        val reasons = bm["quality_reasons"] as List<*>
        assertEquals(listOf("R1"), reasons)
        @Suppress("UNCHECKED_CAST")
        val dom = bm["dominance_metrics"] as Map<*, *>
        assertEquals(8.0, dom["top_k_size"])
        @Suppress("UNCHECKED_CAST")
        val cr = r.metadata["context_resolution"] as Map<*, *>
        assertEquals("/a", cr["requested_repo_root"])
        assertEquals("/b", cr["effective_repo_root"])
        assertEquals(true, cr["fallback_used"])
        @Suppress("UNCHECKED_CAST")
        val efm = r.metadata["evidence_first_meta"] as Map<*, *>
        assertEquals("v1_evidence", efm["ask_path"])
        assertEquals("layer5.evidence_bundle.v1", efm["context_source"])
        assertEquals(true, efm["no_context_engine"])
    }

    @Test
    fun `parseAskResponse preserves explain_debug and all truth surfaces for Explain slash Debug`() {
        val json = """
            {
              "schema_version": "plan_only_response.v0.1",
              "request_id": "req-explain-e2e",
              "timestamp_utc": "2026-01-01T00:00:00Z",
              "governance_posture": "PLAN_ONLY",
              "execution": false,
              "context_bundle": {
                "revision": "rev1",
                "files": [{"path": "m/sample.py", "selection_reason": "evidence"}],
                "selectors_used": ["plan_gate:v1_ask:evidence_bundle.v1"]
              },
              "plan_summary": { "steps": ["Explain/debug analysis completed; see structured output above."] },
              "ui": { "title": "Evidence-driven Plan (PLAN ONLY)", "message": "m", "severity": "info" },
              "metadata": {
                "intent_type": "GENERIC_INTENT",
                "evidence_quality": "STRONG",
                "quality_reasons": ["OK"],
                "dominance_metrics": { "top_k_size": 1.0 },
                "policy_version": "quality_gate.v1"
              },
              "context_resolution": {
                "context_source": "layer5.evidence_bundle.v1",
                "no_repo_filesystem": true
              },
              "evidence_first_meta": {
                "ask_path": "v1_evidence",
                "context_source": "layer5.evidence_bundle.v1",
                "no_context_engine": true
              },
              "evidence_bundle": { "schema_hint": "layer5.evidence_bundle.v1", "entries": [] },
              "explain_debug": {
                "summary": "Parsed summary line.",
                "logic_flow": "",
                "likely_bug_risk": "",
                "evidence": ["m/sample.py"],
                "confidence_limits": "Limited to bundle."
              }
            }
        """.trimIndent()

        val bridge = RuntimeBridge()
        val r = bridge.parseAskResponse("req-explain-e2e", json)

        @Suppress("UNCHECKED_CAST")
        val ed = r.metadata["explain_debug"] as Map<String, Any?>
        assertEquals("Parsed summary line.", ed["summary"])
        @Suppress("UNCHECKED_CAST")
        val evid = ed["evidence"] as List<*>
        assertEquals(listOf("m/sample.py"), evid)

        @Suppress("UNCHECKED_CAST")
        val bm = r.metadata["backend_metadata"] as Map<String, Any?>
        assertEquals("STRONG", bm["evidence_quality"])
        assertEquals("GENERIC_INTENT", bm["intent_type"])
        @Suppress("UNCHECKED_CAST")
        val reasons = bm["quality_reasons"] as List<*>
        assertEquals(listOf("OK"), reasons)

        @Suppress("UNCHECKED_CAST")
        val efm = r.metadata["evidence_first_meta"] as Map<*, *>
        assertEquals("v1_evidence", efm["ask_path"])
        assertEquals("layer5.evidence_bundle.v1", efm["context_source"])

        @Suppress("UNCHECKED_CAST")
        val cr = r.metadata["context_resolution"] as Map<*, *>
        assertEquals("layer5.evidence_bundle.v1", cr["context_source"])
        assertEquals(true, cr["no_repo_filesystem"])

        @Suppress("UNCHECKED_CAST")
        val eb = r.metadata["evidence_bundle"] as Map<*, *>
        assertEquals("layer5.evidence_bundle.v1", eb["schema_hint"])
    }

    @Test
    fun `parseExecuteResponse maps EXECUTED_FAILED and wasExecuted`() {
        val json = """
            {
              "schema_version": "execute_response.v0.1",
              "request_id": "req-exec-fail",
              "outcome": "EXECUTED_FAILED",
              "posture": "safe_execute",
              "executed": true,
              "reason": "Command ran but did not succeed (exit_code=1).",
              "plan_hash": "abc",
              "ui": { "title": "Execution Failed", "message": "Not a policy block.", "severity": "warning" }
            }
        """.trimIndent()
        val bridge = RuntimeBridge()
        val r = bridge.parseExecuteResponse("req-exec-fail", json)
        assertEquals(RuntimeOutcome.EXECUTED_FAILED, r.outcome)
        assertTrue(r.wasExecuted)
        assertEquals("req-exec-fail", r.requestId)
    }

    @Test
    fun `parseExecuteResponse BLOCKED remains distinct from EXECUTED_FAILED`() {
        val json = """
            {
              "schema_version": "execute_response.v0.1",
              "request_id": "req-block",
              "outcome": "BLOCKED",
              "posture": "safe_execute",
              "executed": false,
              "reason": "Execution blocked by sandbox policy.",
              "plan_hash": "def",
              "ui": { "title": "Execution Blocked", "message": "x", "severity": "error" }
            }
        """.trimIndent()
        val bridge = RuntimeBridge()
        val r = bridge.parseExecuteResponse("req-block", json)
        assertEquals(RuntimeOutcome.BLOCKED, r.outcome)
        assertFalse(r.wasExecuted)
    }
}
