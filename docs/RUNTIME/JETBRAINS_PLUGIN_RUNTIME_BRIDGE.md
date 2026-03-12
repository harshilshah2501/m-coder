# JetBrains Plugin Runtime Bridge

## Overview

The **RuntimeBridge** is the single integration point between the JetBrains IDE plugin and the Motadata runtime governance system. It ensures that all governed IDE actions flow through the runtime path without local bypass or governance reinterpretation.

## Architectural Principles

### The plugin is a client, NOT a governor

The plugin MUST:
- ✅ Intercept or initiate actions
- ✅ Package requests using `RuntimeRequest`
- ✅ Call runtime through `RuntimeBridge`
- ✅ Display governed outcomes truthfully
- ✅ Avoid bypasses

The plugin MUST NOT:
- ❌ Make governance decisions itself
- ❌ Reinterpret posture semantics
- ❌ Execute protected actions locally as fallback
- ❌ Silently bypass runtime when unavailable
- ❌ Collapse distinct outcomes into generic states

## Component Overview

```
jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/
├── bridge/
│   ├── RuntimeBridge.kt      # Single integration point
│   ├── RuntimeOutcome.kt     # 7 distinct outcomes
│   ├── RuntimeRequest.kt     # Request envelope
│   └── RuntimeResponse.kt    # Response contract
├── vcs/
│   └── MotadataCheckinHandler.kt  # Uses RuntimeBridge
├── ask/
│   ├── AskClient.kt              # Legacy (kept for compatibility)
│   └── AskMotadataAiAction.kt    # Uses RuntimeBridge
├── actions/
│   └── SubmitToRuntimeAction.kt  # Uses RuntimeBridge
└── logging/
    └── DecisionLogger.kt         # Audit trail
```

## RuntimeBridge API

### Constructor

```kotlin
class RuntimeBridge(
    private val gson: Gson = Gson(),
    private val baseUrl: String = "http://127.0.0.1:8089",
    private val timeoutMs: Int = 5000
)
```

### Methods

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `evaluateCommit(request)` | `POST /v0/plan` | Evaluate VCS commit governance |
| `askPlan(request)` | `POST /v0/ask` | Plan-only Ask request |
| `requestExecution(request)` | `POST /v0/execute` | Request governed execution |
| `validateAction(request)` | `POST /v0/plan?validate_only` | Validate without execution |
| `isRuntimeAvailable()` | `GET /healthz` | Check runtime health |
| `getRuntimeVersion()` | `GET /version` | Get supported schemas |

## RuntimeOutcome Enum

The plugin surfaces **7 distinct outcomes** — never collapsed:

```kotlin
enum class RuntimeOutcome {
    REFUSED,            // Governance denied the action
    DEFERRED,           // Action deferred pending approval
    BOUNDED_ALLOW,      // Bounded-safe, no sandbox execution
    BLOCKED,            // Execution blocked by policy
    EXECUTED,           // Successfully executed
    RUNTIME_UNAVAILABLE, // Runtime unreachable (fail-closed)
    UNKNOWN             // Unexpected response
}
```

### Outcome Properties

| Property | Type | Description |
|----------|------|-------------|
| `isSuccess` | Boolean | `true` only for `EXECUTED` |
| `isError` | Boolean | `true` for `REFUSED`, `BLOCKED`, `RUNTIME_UNAVAILABLE` |
| `wasExecuted` | Boolean | `true` only for `EXECUTED` |
| `toHumanReadable()` | String | User-friendly description |

### Posture Mapping

| Runtime Posture | RuntimeOutcome |
|-----------------|----------------|
| `refuse` | `REFUSED` |
| `defer` | `DEFERRED` |
| `bounded_allow` | `BOUNDED_ALLOW` |
| `safe_execute` | `EXECUTED` |

### Legacy Decision Mapping

| Legacy Decision | RuntimeOutcome |
|-----------------|----------------|
| `REFUSAL` | `REFUSED` |
| `CONDITIONAL_BLOCK` | `DEFERRED` |
| `BOUNDING` | `BOUNDED_ALLOW` |
| `APPROVE` | `EXECUTED` |

## RuntimeRequest Contract

```kotlin
data class RuntimeRequest(
    val requestId: String,              // req-{UUID}
    val actionType: RuntimeActionType,  // VCS_COMMIT, ASK_PLAN, EXECUTE, VALIDATE
    val taskId: String?,                // Optional multi-step ID
    val repoRoot: String,               // Repository root path
    val revision: String?,              // Git SHA
    val branch: String?,                // Git branch
    val payload: String?,               // Command/query text
    val planHash: String?,              // Prior plan hash
    val ideContext: IdeContext,         // IDE metadata
    val timestampUtc: String,           // ISO-8601 UTC
    val clientPolicy: ClientPolicy      // Fail-closed, mode
)
```

### RuntimeActionType

| Type | Action String | Purpose |
|------|---------------|---------|
| `VCS_COMMIT` | `VCS_COMMIT_INTENT` | Commit interception |
| `ASK_PLAN` | `ASK_PLAN` | Plan-only Ask |
| `EXECUTE` | `EXECUTE_INTENT` | Execution request |
| `VALIDATE` | `VALIDATE_INTENT` | Validation check |

### ClientPolicy

```kotlin
data class ClientPolicy(
    val failClosedIfUnreachable: Boolean = true,  // Fail-closed when unreachable
    val mode: String = "shadow"                   // "shadow" or "enforcing"
)
```

## RuntimeResponse Contract

```kotlin
data class RuntimeResponse(
    val outcome: RuntimeOutcome,     // Governed outcome
    val requestId: String?,          // Echoed back
    val ui: RuntimeUi?,              // Title, message, severity
    val reason: String?,             // Decision reason
    val wasExecuted: Boolean,        // Did sandbox run?
    val ledgerRowId: String?,        // Audit trail
    val planHash: String?,           // Plan hash
    val error: String?,              // Error if runtime call failed
    val metadata: Map<String, Any?>  // Additional data
)
```

### Helper Methods

| Method | Description |
|--------|-------------|
| `shouldProceed(shadowMode)` | Whether action should continue |
| `getSeverity()` | Notification severity level |

### Factory Methods

| Method | Creates |
|--------|---------|
| `RuntimeResponse.runtimeUnavailable(requestId, error)` | Unavailable response |
| `RuntimeResponse.unknown(requestId, error)` | Unknown response |

## Usage Examples

### Commit Interception

```kotlin
class MotadataCheckinHandler(
    private val project: Project,
    private val bridge: RuntimeBridge = RuntimeBridge(),
    private val enforcingMode: Boolean = false
) : CheckinHandler() {

    override fun beforeCheckin(): ReturnResult {
        val request = RuntimeRequest(
            actionType = RuntimeActionType.VCS_COMMIT,
            repoRoot = project.basePath ?: "",
            revision = getRevision(),
            branch = getBranch(),
            ideContext = IdeContext(projectName = project.name),
            clientPolicy = ClientPolicy(
                failClosedIfUnreachable = enforcingMode,
                mode = if (enforcingMode) "enforcing" else "shadow"
            )
        )

        val response = bridge.evaluateCommit(request)
        
        showNotification(response)
        logDecision(response)
        
        return if (response.shouldProceed(shadowMode = !enforcingMode)) {
            ReturnResult.COMMIT
        } else {
            ReturnResult.CANCEL
        }
    }
}
```

### Ask / Plan Request

```kotlin
class AskMotadataAiAction : AnAction() {
    private val bridge = RuntimeBridge()

    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val question = getUserQuestion() ?: return

        val request = RuntimeRequest(
            actionType = RuntimeActionType.ASK_PLAN,
            repoRoot = project.basePath ?: "",
            payload = question,
            ideContext = IdeContext(projectName = project.name)
        )

        val response = bridge.askPlan(request)
        showPlanOnlyResult(response)
    }
}
```

### Submit to Runtime

```kotlin
class SubmitToRuntimeAction : AnAction() {
    private val bridge = RuntimeBridge()

    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        
        if (!bridge.isRuntimeAvailable()) {
            showRuntimeUnavailableDialog()
            return
        }

        val command = getUserCommand() ?: return

        val request = RuntimeRequest(
            actionType = RuntimeActionType.EXECUTE,
            repoRoot = project.basePath ?: "",
            payload = command,
            ideContext = IdeContext(projectName = project.name),
            clientPolicy = ClientPolicy(failClosedIfUnreachable = true)
        )

        val response = bridge.requestExecution(request)
        showGovernedOutcome(response)
    }
}
```

## Error Handling

### Runtime Unavailable

When runtime is unreachable:

```kotlin
// In RuntimeBridge
return try {
    val responseJson = postJson("$baseUrl/v0/execute", request)
    parseResponse(responseJson)
} catch (e: Exception) {
    RuntimeResponse.runtimeUnavailable(request.requestId, e.message)
}
```

### Fail-Closed Semantics

```kotlin
// In MotadataCheckinHandler
private fun determineResult(response: RuntimeResponse): ReturnResult {
    if (!enforcingMode) {
        return ReturnResult.COMMIT  // Shadow mode: always proceed
    }
    
    return when (response.outcome) {
        RuntimeOutcome.EXECUTED -> ReturnResult.COMMIT
        RuntimeOutcome.BOUNDED_ALLOW -> ReturnResult.COMMIT
        else -> ReturnResult.CANCEL  // Fail-closed
    }
}
```

## Notification Mapping

| Outcome | NotificationType | Severity |
|---------|------------------|----------|
| `EXECUTED` | `INFORMATION` | Info |
| `BOUNDED_ALLOW` | `WARNING` | Warning |
| `DEFERRED` | `WARNING` | Warning |
| `REFUSED` | `ERROR` | Error |
| `BLOCKED` | `ERROR` | Error |
| `RUNTIME_UNAVAILABLE` | `ERROR` | Error |
| `UNKNOWN` | `WARNING` | Warning |

## Testing

### Unit Tests

```kotlin
// RuntimeOutcomeTest.kt
@Test
fun `all outcomes are distinct - no collapsing`() {
    val outcomes = RuntimeOutcome.values()
    assertEquals(7, outcomes.size)
    assertEquals(outcomes.toSet().size, outcomes.size)
}

@Test
fun `isSuccess is true only for EXECUTED`() {
    assertTrue(RuntimeOutcome.EXECUTED.isSuccess)
    assertFalse(RuntimeOutcome.REFUSED.isSuccess)
    assertFalse(RuntimeOutcome.BOUNDED_ALLOW.isSuccess)
}
```

### Integration Tests

```bash
# Run runtime execute service tests
python3 -m pytest runtime/tests/test_execute_service.py -v
```

## Related Documents

- [M3.4 IDE Plugin Integration](milestones/M3.4_IDE_PLUGIN_INTEGRATION.md)
- [JetBrains Plugin MVP Spike](JETBRAINS_PLUGIN_MVP_SPIKE.md)
- [JetBrains Plugin Demo Guide](JETBRAINS_PLUGIN_DEMO_GUIDE.md)
- [Runtime Agent Architecture](RUNTIME_AGENT_ARCHITECTURE.md)
