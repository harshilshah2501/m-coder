package ai.motadata.plugin.ask

import ai.motadata.plugin.actions.SubmitToRuntimeAction
import ai.motadata.plugin.assistant.HostContract
import ai.motadata.plugin.bridge.AskPluginRouting
import ai.motadata.plugin.bridge.IdeContext
import ai.motadata.plugin.bridge.RuntimeActionType
import ai.motadata.plugin.bridge.RuntimeBridge
import ai.motadata.plugin.bridge.RuntimeRequest
import ai.motadata.plugin.bridge.RuntimeResponse
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Tag
import org.junit.jupiter.api.Test
import java.lang.reflect.Method
import java.nio.file.Files
import java.nio.file.Path
import kotlin.io.path.writeText

class Phase1TruthProofHarnessTest {

    private val gson = Gson()

    /**
     * Offline regression: committed proof matrix must stay green (8 scenarios, exact_match true).
     * Does not call Context Layer or Plan-Gate.
     */
    @Test
    fun phase1ProofMatrixFrozenContract() {
        val repoRoot = resolveRepoRoot()
        val matrixPath = repoRoot.resolve("docs/validation/artifacts/plugin_phase1_truth_proof/proof_matrix.json")
        assertTrue(Files.exists(matrixPath), "missing proof matrix at $matrixPath")
        val json = Files.readString(matrixPath)
        val type = object : TypeToken<List<Map<String, @JvmSuppressWildcards Any?>>>() {}.type
        @Suppress("UNCHECKED_CAST")
        val rows = gson.fromJson<List<Map<String, Any?>>>(json, type)
        assertEquals(8, rows.size, "expected 8 scenarios S1–S8")
        val ids = rows.mapNotNull { it["scenario"] as? String }.toSet()
        assertEquals(setOf("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"), ids)
        for (row in rows) {
            val scenario = row["scenario"] as? String ?: continue
            val exact = row["exact_match"]
            assertTrue(
                exact is Boolean && exact,
                "scenario $scenario must have exact_match=true (Boolean), got $exact",
            )
        }
    }

    @Tag("live")
    @Test
    fun generatePhase1ProofPack() {
        val repoRoot = resolveRepoRoot()
        val outDir = repoRoot.resolve("docs/validation/artifacts/plugin_phase1_truth_proof")
        Files.createDirectories(outDir)

        val bridge = RuntimeBridge(timeoutMs = 120_000)

        val scenarios = mutableListOf<Map<String, Any?>>()

        // 1) Strong /v1/ask
        val s1 = runAskScenario(
            bridge = bridge,
            scenarioId = "S1",
            title = "strong_v1_ask",
            query = "How does alert correlation work in this repo?",
            evidenceFirst = true,
            outDir = outDir,
        )
        scenarios += s1

        // 2) Default /v0/ask
        val s2 = runAskScenario(
            bridge = bridge,
            scenarioId = "S2",
            title = "default_v0_ask",
            query = "How does alert correlation work in this repo?",
            evidenceFirst = false,
            outDir = outDir,
        )
        scenarios += s2

        // 3) Controlled fallback v1 -> v0
        val oldContextUrl = System.getProperty("motadata.context_layer.url")
        System.setProperty("motadata.context_layer.url", "http://127.0.0.1:65535")
        val s3 = try {
            runAskScenario(
                bridge = bridge,
                scenarioId = "S3",
                title = "controlled_fallback_v1_to_v0",
                query = "How does alert correlation work in this repo?",
                evidenceFirst = true,
                outDir = outDir,
            )
        } finally {
            if (oldContextUrl == null) System.clearProperty("motadata.context_layer.url") else System.setProperty("motadata.context_layer.url", oldContextUrl)
        }
        scenarios += s3

        // 4) Weak evidence
        val s4 = runAskScenario(
            bridge = bridge,
            scenarioId = "S4",
            title = "weak_evidence",
            query = "where is README for docker compose setup?",
            evidenceFirst = true,
            outDir = outDir,
        )
        scenarios += s4

        // 5) No-match / absent grounding
        val s5 = runAskScenario(
            bridge = bridge,
            scenarioId = "S5",
            title = "no_match_absent_grounding",
            query = "abcxyz definitely_not_existing_symbol_92134",
            evidenceFirst = true,
            outDir = outDir,
        )
        scenarios += s5

        // 6-8 execute outcomes
        scenarios += runExecuteScenario(
            bridge = bridge,
            scenarioId = "S6",
            title = "execute_blocked",
            command = "false",
            outDir = outDir,
        )
        scenarios += runExecuteScenario(
            bridge = bridge,
            scenarioId = "S7",
            title = "execute_refused",
            command = "curl https://example.com",
            outDir = outDir,
        )
        scenarios += runExecuteScenario(
            bridge = bridge,
            scenarioId = "S8",
            title = "execute_failed_after_run",
            command = "python3 -c \"import sys; sys.exit(1)\"",
            outDir = outDir,
        )

        val hostPass = HostContract.validate()
        val oldContextUrl2 = System.getProperty("motadata.context_layer.url")
        System.setProperty("motadata.context_layer.url", "http://127.0.0.1:65535")
        val hostFail = try {
            HostContract.validate()
        } finally {
            if (oldContextUrl2 == null) System.clearProperty("motadata.context_layer.url") else System.setProperty("motadata.context_layer.url", oldContextUrl2)
        }

        writeJson(outDir.resolve("host_contract_check.json"), mapOf(
            "pass_check" to mapOf("ok" to hostPass.ok, "findings" to hostPass.findings, "guidance" to hostPass.guidance),
            "forced_fail_check" to mapOf("ok" to hostFail.ok, "findings" to hostFail.findings, "guidance" to hostFail.guidance),
        ))

        writeJson(outDir.resolve("proof_matrix.json"), scenarios)
        outDir.resolve("proof_matrix.md").writeText(buildMatrixMarkdown(scenarios))
    }

    private fun runAskScenario(
        bridge: RuntimeBridge,
        scenarioId: String,
        title: String,
        query: String,
        evidenceFirst: Boolean,
        outDir: Path,
    ): Map<String, Any?> {
        val request = RuntimeRequest(
            actionType = RuntimeActionType.ASK_PLAN,
            repoRoot = "/home/harshil/Projects/Motadata",
            revision = "phase1-proof",
            branch = "phase1-proof",
            payload = query,
            ideContext = IdeContext(projectName = "m-coder-proof"),
            evidenceFirst = evidenceFirst,
        )
        val response = bridge.askPlan(request)

        val scenarioDir = outDir.resolve("scenario_$scenarioId")
        Files.createDirectories(scenarioDir)
        writeJson(scenarioDir.resolve("request.json"), request.toMap())
        writeJson(scenarioDir.resolve("response.json"), runtimeResponseToMap(response))

        val summary = buildAskResultSummaryMessage(query, response)
        val full = buildAskResultDialogMessage(query, response)
        scenarioDir.resolve("plugin_summary.txt").writeText(summary)
        scenarioDir.resolve("plugin_full_dialog.txt").writeText(full)

        val md = response.metadata
        val evidenceMeta = md["evidence_first_meta"] as? Map<*, *>
        val askPath = evidenceMeta?.get("ask_path")?.toString()
        val routingMode = md["routing_mode"] as? String
        val traceId = md["trace_id"] as? String
        val pluginRoute = md[AskPluginRouting.METADATA_KEY] as? String
        @Suppress("UNCHECKED_CAST")
        val backendMetadata = md["backend_metadata"] as? Map<String, Any?>
        val evidenceQuality = backendMetadata?.get("evidence_quality")?.toString()
        @Suppress("UNCHECKED_CAST")
        val decision = md["plugin_ask_routing_decision"] as? Map<String, Any?>
        val fallbackReason = decision?.get("reason")?.toString()
        val fallbackTo = decision?.get("fallback_to")?.toString()
        val planSummary = md["plan_summary"] as? Map<*, *>
        @Suppress("UNCHECKED_CAST")
        val notes = planSummary?.get("notes") as? List<*>
        val notesPresent = !(notes.isNullOrEmpty())
        val hasEvidenceBundle = md["evidence_bundle"] != null

        val exactMatch = when (scenarioId) {
            "S1" -> askPath == "v1_evidence" && routingMode == "plan_only" && traceId != null && hasEvidenceBundle
            "S2" -> askPath == null && pluginRoute == AskPluginRouting.V0_DIRECT && routingMode == "plan_only" && traceId != null
            "S3" -> (pluginRoute == AskPluginRouting.CONTEXT_EXPORT_THEN_V0 || pluginRoute == AskPluginRouting.V0_AFTER_V1_HTTP_FALLBACK) && fallbackTo == "v0"
            "S4" -> evidenceQuality == "WEAK" || evidenceQuality == "INSUFFICIENT"
            "S5" -> evidenceQuality == "NO_MATCH" || evidenceQuality == "INSUFFICIENT"
            else -> false
        }

        return mapOf(
            "scenario" to scenarioId,
            "title" to title,
            "backend_truth" to mapOf(
                "outcome" to response.outcome.name,
                "routing_mode" to routingMode,
                "ask_path" to askPath,
                "trace_id" to traceId,
                "evidence_quality" to evidenceQuality,
                "plugin_route" to pluginRoute,
            ),
            "plugin_visible_truth" to mapOf(
                "summary_contains_routing_mode" to (summary.contains("routing_mode:") || summary.contains("mode=")),
                "summary_contains_ask_path" to summary.contains("ask_path:"),
                "summary_contains_trace" to summary.contains("trace"),
                "summary_contains_evidence_presence" to summary.contains("evidence_bundle_present:"),
                "summary_contains_notes_presence" to summary.contains("plan_summary.notes_present:"),
                "summary_contains_fallback_reason" to summary.contains("fallback_reason:"),
                "notes_present" to notesPresent,
            ),
            "proof_type" to "deterministic harness + live runtime",
            "exact_match" to exactMatch,
            "notes" to "See scenario files for request/response and plugin text captures",
        )
    }

    private fun runExecuteScenario(
        bridge: RuntimeBridge,
        scenarioId: String,
        title: String,
        command: String,
        outDir: Path,
    ): Map<String, Any?> {
        val request = RuntimeRequest(
            actionType = RuntimeActionType.EXECUTE,
            repoRoot = "/home/harshil/Projects/Motadata",
            revision = "phase1-proof",
            branch = "phase1-proof",
            payload = command,
            ideContext = IdeContext(projectName = "m-coder-proof"),
        )
        val response = bridge.requestExecution(request)

        val scenarioDir = outDir.resolve("scenario_$scenarioId")
        Files.createDirectories(scenarioDir)
        writeJson(scenarioDir.resolve("request.json"), request.toMap())
        writeJson(scenarioDir.resolve("response.json"), runtimeResponseToMap(response))

        val action = SubmitToRuntimeAction()
        val methodName = when (response.outcome.name) {
            "BLOCKED" -> "buildBlockedMessage"
            "REFUSED" -> "buildRefusedMessage"
            "EXECUTED_FAILED" -> "buildExecutedFailedMessage"
            "EXECUTED" -> "buildExecutedMessage"
            "DEFERRED" -> "buildDeferredMessage"
            "BOUNDED_ALLOW" -> "buildBoundedAllowMessage"
            "RUNTIME_UNAVAILABLE" -> "buildRuntimeUnavailableMessage"
            else -> "buildUnknownMessage"
        }
        val rendered = invokePrivateMessageBuilder(action, methodName, command, response)
        scenarioDir.resolve("plugin_full_dialog.txt").writeText(rendered)

        val expected = when (scenarioId) {
            "S6" -> "BLOCKED"
            "S7" -> "REFUSED"
            "S8" -> "EXECUTED_FAILED"
            else -> response.outcome.name
        }

        return mapOf(
            "scenario" to scenarioId,
            "title" to title,
            "backend_truth" to mapOf(
                "outcome" to response.outcome.name,
                "executed" to response.wasExecuted,
            ),
            "plugin_visible_truth" to mapOf(
                "message_contains_outcome_label" to rendered.contains(expected),
                "message_contains_not_executed_marker" to (
                    rendered.contains("NOT executed") ||
                        rendered.contains("NOT_EXECUTED") ||
                        rendered.contains("NOT EXECUTED")
                    ),
                "message_contains_executed_marker" to rendered.contains("EXECUTED"),
            ),
            "proof_type" to "deterministic harness + live runtime",
            "exact_match" to (response.outcome.name == expected),
            "notes" to "Rendered via plugin's own private message builder: $methodName",
        )
    }

    private fun invokePrivateMessageBuilder(action: SubmitToRuntimeAction, methodName: String, command: String, response: RuntimeResponse): String {
        val m: Method = SubmitToRuntimeAction::class.java.getDeclaredMethod(
            methodName,
            String::class.java,
            RuntimeResponse::class.java,
        )
        m.isAccessible = true
        return m.invoke(action, command, response) as String
    }

    private fun runtimeResponseToMap(response: RuntimeResponse): Map<String, Any?> = mapOf(
        "outcome" to response.outcome.name,
        "request_id" to response.requestId,
        "reason" to response.reason,
        "was_executed" to response.wasExecuted,
        "ledger_row_id" to response.ledgerRowId,
        "plan_hash" to response.planHash,
        "error" to response.error,
        "metadata" to response.metadata,
    )

    private fun buildMatrixMarkdown(rows: List<Map<String, Any?>>): String {
        val sb = StringBuilder()
        sb.appendLine("# Phase-1 Plugin Truth Proof Matrix")
        sb.appendLine()
        sb.appendLine("| Scenario | Backend truth | Plugin-visible truth | Proof type | Exact match? | Notes |")
        sb.appendLine("| --- | --- | --- | --- | --- | --- |")
        for (row in rows) {
            val scenario = row["scenario"]
            val backend = gson.toJson(row["backend_truth"])
            val plugin = gson.toJson(row["plugin_visible_truth"])
            val proof = row["proof_type"]
            val exact = row["exact_match"]
            val notes = row["notes"]
            sb.appendLine("| $scenario | ${escapePipes(backend)} | ${escapePipes(plugin)} | $proof | $exact | ${escapePipes(notes.toString())} |")
        }
        return sb.toString()
    }

    private fun escapePipes(input: String): String = input.replace("|", "\\|")

    private fun writeJson(path: Path, data: Any) {
        path.writeText(gson.toJson(data) + "\n")
    }

    private fun resolveRepoRoot(): Path {
        val cwd = Path.of(System.getProperty("user.dir")).toAbsolutePath().normalize()
        return if (cwd.fileName.toString() == "jetbrains-plugin") cwd.parent else cwd
    }
}
