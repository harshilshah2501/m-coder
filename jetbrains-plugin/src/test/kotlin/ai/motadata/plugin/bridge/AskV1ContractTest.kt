package ai.motadata.plugin.bridge

import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class AskV1ContractTest {

    private val gson = Gson()

    @Test
    fun `contract failures are not v0 fallback cases`() {
        val body = """{"error":"identity_mismatch","message":"hash differs","details":{}}"""
        assertTrue(AskV1Contract.isContractClientFailure(400, body))
        assertFalse(AskV1Contract.shouldFallbackV1ToV0(400))
    }

    @Test
    fun `404 triggers v0 fallback`() {
        assertTrue(AskV1Contract.shouldFallbackV1ToV0(404))
        assertFalse(AskV1Contract.isContractClientFailure(404, "{}"))
    }

    @Test
    fun `generic 400 without known code is not contract-classified`() {
        val body = """{"error":"Schema validation failed","details":[]}"""
        assertFalse(AskV1Contract.isContractClientFailure(400, body))
    }

    @Test
    fun `buildAskRequestV1Json uses ask_request v1 envelope`() {
        val ev = JsonObject()
        ev.addProperty("schema_hint", "layer5.evidence_bundle.v1")
        ev.addProperty("workspace_identity_hash", "abc123")
        ev.add("entries", JsonParser.parseString("[]").asJsonArray)

        val req = RuntimeRequest(
            actionType = RuntimeActionType.ASK_PLAN,
            repoRoot = "/tmp/repo",
            ideContext = IdeContext(projectName = "p"),
            requestId = "rid-1",
            timestampUtc = "2026-03-21T00:00:00Z",
            payload = "hello query",
            revision = "rev1",
            selectedFile = "src/Foo.kt",
            taskType = "general",
        )

        val json = AskV1Contract.buildAskRequestV1Json(gson, req, ev)
        val root = JsonParser.parseString(json).asJsonObject
        assertEquals("ask_request.v1.0", root.get("schema_version").asString)
        assertEquals("rid-1", root.get("request_id").asString)
        assertEquals("hello query", root.get("query").asString)
        assertEquals("rev1", root.get("revision").asString)
        assertEquals("abc123", root.get("expected_workspace_identity_hash").asString)
        assertTrue(root.has("evidence_bundle"))
    }
}
