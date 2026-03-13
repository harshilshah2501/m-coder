package ai.motadata.plugin.bridge

import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test

class RuntimeRequestTest {

    @Test
    fun `RuntimeRequest generates unique request ID`() {
        val request1 = RuntimeRequest(
            actionType = RuntimeActionType.VCS_COMMIT,
            repoRoot = "/tmp/repo",
            ideContext = IdeContext(projectName = "test")
        )
        val request2 = RuntimeRequest(
            actionType = RuntimeActionType.VCS_COMMIT,
            repoRoot = "/tmp/repo",
            ideContext = IdeContext(projectName = "test")
        )

        assertTrue(request1.requestId.startsWith("req-"))
        assertTrue(request2.requestId.startsWith("req-"))
        assertNotEquals(request1.requestId, request2.requestId)
    }

    @Test
    fun `RuntimeActionType toActionTypeString returns correct values`() {
        assertEquals("VCS_COMMIT_INTENT", RuntimeActionType.VCS_COMMIT.toActionTypeString())
        assertEquals("ASK_PLAN", RuntimeActionType.ASK_PLAN.toActionTypeString())
        assertEquals("EXECUTE_INTENT", RuntimeActionType.EXECUTE.toActionTypeString())
        assertEquals("VALIDATE_INTENT", RuntimeActionType.VALIDATE.toActionTypeString())
    }

    @Test
    fun `toMap includes all required fields`() {
        val request = RuntimeRequest(
            actionType = RuntimeActionType.EXECUTE,
            repoRoot = "/home/user/project",
            revision = "abc123",
            branch = "main",
            payload = "echo hello",
            ideContext = IdeContext(
                product = "jetbrains",
                ide = "intellij",
                projectName = "MyProject",
                user = "testuser"
            ),
            clientPolicy = ClientPolicy(
                failClosedIfUnreachable = true,
                mode = "shadow"
            )
        )

        val map = request.toMap()

        assertEquals("EXECUTE_INTENT", map["action_type"])
        assertEquals("/home/user/project", map["repo_root"])
        assertEquals("abc123", map["revision"])
        assertEquals("main", map["branch"])
        assertEquals("echo hello", map["payload"])
        
        @Suppress("UNCHECKED_CAST")
        val ideContext = map["ide_context"] as Map<String, Any>
        assertEquals("jetbrains", ideContext["product"])
        assertEquals("intellij", ideContext["ide"])
        assertEquals("MyProject", ideContext["project"])
        assertEquals("testuser", ideContext["user"])

        @Suppress("UNCHECKED_CAST")
        val clientPolicy = map["client_policy"] as Map<String, Any>
        assertEquals(true, clientPolicy["fail_closed_if_gate_unreachable"])
        assertEquals("shadow", clientPolicy["mode"])
    }

    @Test
    fun `toMap excludes null values`() {
        val request = RuntimeRequest(
            actionType = RuntimeActionType.ASK_PLAN,
            repoRoot = "/tmp/repo",
            ideContext = IdeContext(projectName = "test")
        )

        val map = request.toMap()

        assertFalse(map.containsKey("task_id"))
        assertFalse(map.containsKey("plan_hash"))
    }

    @Test
    fun `ClientPolicy defaults are correct`() {
        val policy = ClientPolicy()

        assertTrue(policy.failClosedIfUnreachable)
        assertEquals("shadow", policy.mode)
    }

    @Test
    fun `IdeContext has correct defaults`() {
        val context = IdeContext(projectName = "test")

        assertEquals("jetbrains", context.product)
        assertEquals("intellij", context.ide)
    }

    @Test
    fun `timestamp is generated automatically`() {
        val request = RuntimeRequest(
            actionType = RuntimeActionType.VCS_COMMIT,
            repoRoot = "/tmp/repo",
            ideContext = IdeContext(projectName = "test")
        )

        assertNotNull(request.timestampUtc)
        assertTrue(request.timestampUtc.isNotEmpty())
    }
}
