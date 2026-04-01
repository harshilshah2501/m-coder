package ai.motadata.plugin.ask

import ai.motadata.plugin.bridge.AskPluginRouting
import ai.motadata.plugin.bridge.RuntimeResponse

private const val ASK_SUMMARY_SNIPPET_MAX = 360

/** UI mode from backend [routing_mode] only — never from payload shape or [explain_debug] presence. */
internal fun isExplainDebugAskUi(response: RuntimeResponse): Boolean =
    response.metadata["routing_mode"] as? String == "explain_debug"

/**
 * Short notification-friendly summary (outcome, key calibration, main answer preview).
 * Full diagnostics remain in [buildAskResultDialogMessage].
 */
internal fun buildAskResultSummaryMessage(question: String, response: RuntimeResponse): String {
    val sb = StringBuilder()
    sb.appendLine("Outcome: ${response.outcome.toHumanReadable()}")
    sb.appendLine("request_id: ${response.requestId ?: "(none)"}")
    val qShort = question.trim().let { if (it.length > 100) it.take(100) + "…" else it }
    if (qShort.isNotEmpty()) {
        sb.appendLine("Query: $qShort")
    }
    appendPluginAskTruthSummaryLines(sb, response)
    val bm = response.metadata["backend_metadata"] as? Map<*, *>
    if (bm != null) {
        val eq = (bm["evidence_quality"] as? String)?.trim()
        val intent = (bm["intent_type"] as? String)?.trim()
        val parts = mutableListOf<String>()
        if (!eq.isNullOrEmpty()) parts.add("quality=$eq")
        if (!intent.isNullOrEmpty()) parts.add("intent=$intent")
        if (parts.isNotEmpty()) {
            sb.appendLine(parts.joinToString(" · "))
        }
    }

    if (isExplainDebugAskUi(response)) {
        val explainDebug = response.metadata["explain_debug"] as? Map<*, *>
        val err = explainDebug?.get("error") as? String
        if (err != null) {
            val short = err.trim().let { if (it.length > 140) it.take(140) + "…" else it }
            sb.appendLine("Reasoning unavailable: $short")
        } else {
            val sum = (explainDebug?.get("summary") as? String)?.trim()
            if (!sum.isNullOrEmpty()) {
                sb.appendLine()
                sb.appendLine("Summary")
                val body = if (sum.length > ASK_SUMMARY_SNIPPET_MAX) {
                    sum.take(ASK_SUMMARY_SNIPPET_MAX).trimEnd() + "…"
                } else {
                    sum
                }
                sb.appendLine(body)
            }
        }
    } else {
        response.ui?.title?.takeIf { it.isNotBlank() }?.let { sb.appendLine(it) }
        response.ui?.message?.takeIf { it.isNotBlank() }?.let { m ->
            val t = if (m.length > 220) m.take(220).trimEnd() + "…" else m
            sb.appendLine(t)
        }

        val planSummary = response.metadata["plan_summary"] as? Map<*, *>
        @Suppress("UNCHECKED_CAST")
        val steps = planSummary?.get("steps") as? List<*>
        if (!steps.isNullOrEmpty()) {
            sb.appendLine()
            sb.appendLine("Plan (${steps.size} steps): ${steps.first()}")
            if (steps.size > 1) {
                sb.appendLine("(+${steps.size - 1} more in full response)")
            }
        }

        val eb = response.metadata["evidence_bundle"] as? Map<*, *>
        @Suppress("UNCHECKED_CAST")
        val entries = eb?.get("entries") as? List<*>
        if (!entries.isNullOrEmpty()) {
            sb.appendLine("Grounding: ${entries.size} evidence entr${if (entries.size == 1) "y" else "ies"}")
        } else {
            val contextBundle = response.metadata["context_bundle"] as? Map<*, *>
            @Suppress("UNCHECKED_CAST")
            val files = contextBundle?.get("files") as? List<*>
            if (!files.isNullOrEmpty()) {
                sb.appendLine("Context: ${files.size} file${if (files.size == 1) "" else "s"}")
            }
        }
    }

    sb.appendLine()
    sb.appendLine("— PLAN ONLY — Use View full response or Copy full response for complete diagnostics.")
    return sb.toString()
}

/**
 * Builds the Ask result dialog text. Separated for tests and to keep backend calibration visible
 * without duplication between plan-only and explain/debug paths.
 */
internal fun buildAskResultDialogMessage(question: String, response: RuntimeResponse): String {
    val sb = StringBuilder()
    sb.appendLine("request_id: ${response.requestId ?: "(none)"}")
    sb.appendLine()
    appendPluginAskTruthBlock(sb, response)
    appendBackendTruthSection(sb, response)
    appendResponseProvenanceSection(sb, response)

    val explainDebug = response.metadata["explain_debug"] as? Map<*, *>

    if (isExplainDebugAskUi(response)) {
        sb.appendLine("═══════════════════════════════════════════")
        sb.appendLine("  Explain/Debug — PLAN ONLY")
        sb.appendLine("═══════════════════════════════════════════")
        sb.appendLine()
        val err = explainDebug?.get("error") as? String
        if (err != null) {
            sb.appendLine("Reasoning unavailable: $err")
            sb.appendLine()
            sb.appendLine("No template steps were substituted. Ensure the reasoning service is running (e.g. vLLM) and MOTADATA_EXPLAIN_VLLM_URL is set if needed.")
        } else if (explainDebug == null) {
            sb.appendLine("(routing_mode is explain_debug but explain_debug payload is absent — backend truth incomplete.)")
            sb.appendLine()
        } else {
            (explainDebug["summary"] as? String)?.takeIf { it.isNotBlank() }?.let {
                sb.appendLine("Summary")
                sb.appendLine("──────")
                sb.appendLine(it)
                sb.appendLine()
            }
            (explainDebug["logic_flow"] as? String)?.takeIf { it.isNotBlank() }?.let {
                sb.appendLine("Logic flow")
                sb.appendLine("──────────")
                sb.appendLine(it)
                sb.appendLine()
            }
            (explainDebug["likely_bug_risk"] as? String)?.takeIf { it.isNotBlank() }?.let {
                sb.appendLine("Likely bug/risk")
                sb.appendLine("───────────────")
                sb.appendLine(it)
                sb.appendLine()
            }
            @Suppress("UNCHECKED_CAST")
            (explainDebug["evidence"] as? List<*>)?.filterIsInstance<String>()?.takeIf { it.isNotEmpty() }?.let { evidence ->
                sb.appendLine("Evidence")
                sb.appendLine("────────")
                evidence.forEach { sb.appendLine("  • $it") }
                sb.appendLine()
            }
            (explainDebug["confidence_limits"] as? String)?.takeIf { it.isNotBlank() }?.let {
                sb.appendLine("Confidence / limitations")
                sb.appendLine("─────────────────────────")
                sb.appendLine(it)
                sb.appendLine()
            }
        }
    } else {
        sb.appendLine("═══════════════════════════════════════════")
        sb.appendLine("  PLAN ONLY — No execution performed")
        sb.appendLine("═══════════════════════════════════════════")
        sb.appendLine()
        sb.appendLine("Query: $question")
        sb.appendLine()
        sb.appendLine("Governance Outcome: ${response.outcome.toHumanReadable()}")
        sb.appendLine()

        response.ui?.title?.takeIf { it.isNotBlank() }?.let { sb.appendLine(it) }
        response.ui?.message?.takeIf { it.isNotBlank() }?.let { sb.appendLine(it); sb.appendLine() }

        val evidenceBundle = response.metadata["evidence_bundle"] as? Map<*, *>
        val evidenceMeta = response.metadata["evidence_first_meta"] as? Map<*, *>
        val v1EvidenceAsk = (evidenceMeta?.get("ask_path") as? String) == "v1_evidence"

        if (evidenceBundle != null) {
            sb.appendLine("Grounding — layer5.evidence_bundle.v1 (primary)")
            sb.appendLine("────────────────────────────────────────")
            val hint = evidenceBundle["schema_hint"] ?: evidenceBundle["schema_version"]
            sb.appendLine("schema_hint: $hint")
            if (v1EvidenceAsk) {
                sb.appendLine("ask_path: v1_evidence (POST /v1/ask)")
            }
            sb.appendLine()
            @Suppress("UNCHECKED_CAST")
            val entries = evidenceBundle["entries"] as? List<*>
            if (entries.isNullOrEmpty()) {
                sb.appendLine("(no entries)")
            } else {
                entries.forEachIndexed { i, raw ->
                    val ent = raw as? Map<*, *> ?: return@forEachIndexed
                    val path = ent["relative_path"] ?: ent["path"]
                    sb.appendLine("${i + 1}. $path  (retrieval_score=${ent["retrieval_score"]})")
                    @Suppress("UNCHECKED_CAST")
                    val sn = ent["snippet"] as? Map<*, *>
                    if (sn != null) {
                        val text = (sn["text"] as? String) ?: ""
                        val lines = text.replace("\r\n", "\n").trim().lines().take(5)
                        if (lines.isNotEmpty()) {
                            sb.appendLine("   preview:")
                            lines.forEach { line -> sb.appendLine("   | $line") }
                        }
                    }
                }
            }
            sb.appendLine()
        }

        val contextBundle = response.metadata["context_bundle"] as? Map<*, *>
        if (contextBundle != null && !v1EvidenceAsk) {
            val revision = contextBundle["revision"]
            sb.appendLine("Context bundle @ ${revision ?: "unknown-revision"}")
            val files = contextBundle["files"] as? List<*>
            if (files.isNullOrEmpty()) {
                sb.appendLine("(no files selected)")
            } else {
                sb.appendLine("Files:")
                files.forEach { f ->
                    val fileMap = f as? Map<*, *>
                    val path = fileMap?.get("path")
                    val reason = fileMap?.get("selection_reason")
                    sb.appendLine("  - $path (reason: $reason)")
                }
            }
            sb.appendLine()
            val selectors = contextBundle["selectors_used"] as? List<*>
            if (!selectors.isNullOrEmpty()) {
                sb.appendLine("Selectors used: ${selectors.joinToString(", ")}")
                sb.appendLine()
            }
        } else if (contextBundle != null && v1EvidenceAsk) {
            sb.appendLine("(Planner context is derived from evidence_bundle above; duplicate file list omitted.)")
            sb.appendLine()
        }

        val planSummary = response.metadata["plan_summary"] as? Map<*, *>
        if (planSummary != null) {
            sb.appendLine("Plan:")
            val steps = planSummary["steps"] as? List<*>
            if (steps.isNullOrEmpty()) {
                sb.appendLine("  (no steps returned)")
            } else {
                steps.forEachIndexed { idx, step ->
                    sb.appendLine("  ${idx + 1}. $step")
                }
            }
        }
    }

    sb.appendLine()
    sb.appendLine("───────────────────────────────────────────")
    sb.appendLine("This is a PLAN ONLY response. No code was executed.")
    sb.appendLine("To execute actions, use 'Submit to Runtime'.")
    sb.appendLine("───────────────────────────────────────────")

    return sb.toString()
}

private fun appendPluginAskTruthSummaryLines(sb: StringBuilder, response: RuntimeResponse) {
    val tid = response.metadata["trace_id"] as? String
    val rm = response.metadata["routing_mode"] as? String
    val par = response.metadata[AskPluginRouting.METADATA_KEY] as? String
    val isFallback = par == AskPluginRouting.V0_AFTER_V1_HTTP_FALLBACK ||
        par == AskPluginRouting.CONTEXT_EXPORT_THEN_V0

    if (tid.isNullOrBlank() && rm.isNullOrBlank() && par.isNullOrBlank()) return

    if (isFallback) {
        if (!tid.isNullOrBlank()) sb.appendLine("trace_id: $tid")
        if (!rm.isNullOrBlank()) sb.appendLine("routing_mode: $rm")
        if (!par.isNullOrBlank()) {
            sb.appendLine("plugin_ask_routing: $par")
            sb.appendLine("Note: plugin fallback path — open full response for details.")
        }
        return
    }

    val parts = mutableListOf<String>()
    if (!tid.isNullOrBlank()) parts.add("trace=$tid")
    if (!rm.isNullOrBlank()) parts.add("mode=$rm")
    if (!par.isNullOrBlank()) parts.add("plugin=$par")
    if (parts.isNotEmpty()) {
        sb.appendLine("Routing: ${parts.joinToString(" · ")}")
    }
}

private fun appendPluginAskTruthBlock(sb: StringBuilder, response: RuntimeResponse) {
    sb.appendLine("Routing (correlation)")
    sb.appendLine("────────────────────")
    val tid = response.metadata["trace_id"] as? String
    val rm = response.metadata["routing_mode"] as? String
    val par = response.metadata[AskPluginRouting.METADATA_KEY] as? String
    sb.appendLine("trace_id: ${tid ?: "(not set)"}")
    sb.appendLine("routing_mode: ${rm ?: "(not set)"}")
    sb.appendLine("plugin_ask_routing: ${par ?: "(not set)"}")
    @Suppress("UNCHECKED_CAST")
    val decision = response.metadata["plugin_ask_routing_decision"] as? Map<*, *>
    if (decision != null && decision.isNotEmpty()) {
        sb.appendLine(formatPluginRoutingDecisionOneLine(decision))
    }
    sb.appendLine()
}

/** Single audit line for full dialog — avoids multi-line flight-recorder dump for normal paths. */
private fun formatPluginRoutingDecisionOneLine(decision: Map<*, *>): String {
    val attempt = decision["attempt"]?.toString() ?: "?"
    val result = decision["result"]?.toString() ?: "?"
    val fb = decision["fallback_to"]?.toString()
    val reason = decision["reason"]?.toString()
    val tail = buildString {
        if (fb != null) append(", fallback_to=").append(fb)
        if (!reason.isNullOrBlank()) append(", reason=").append(reason)
    }
    return "plugin_ask_routing_decision: attempt=$attempt, result=$result$tail"
}

/**
 * Backend quality gate output — shown first so it is not visually outranked by plan or model text.
 */
private fun appendBackendTruthSection(sb: StringBuilder, response: RuntimeResponse) {
    val bm = response.metadata["backend_metadata"] as? Map<*, *>
    val cr = response.metadata["context_resolution"] as? Map<*, *>

    if (bm == null && cr == null) {
        return
    }

    sb.appendLine("Grounding calibration (backend)")
    sb.appendLine("──────────────────────────────")

    if (bm != null) {
        val eq = bm["evidence_quality"] as? String
        if (!eq.isNullOrBlank()) {
            sb.appendLine("Evidence quality: $eq")
        } else {
            sb.appendLine("Evidence quality: (not reported)")
        }
        val intentType = bm["intent_type"] as? String
        if (!intentType.isNullOrBlank()) {
            sb.appendLine("intent_type: $intentType")
        }
        @Suppress("UNCHECKED_CAST")
        val reasons = bm["quality_reasons"] as? List<*>
        if (!reasons.isNullOrEmpty()) {
            sb.appendLine("Quality reasons:")
            reasons.forEach { r ->
                val line = r?.toString()?.trim()
                if (!line.isNullOrEmpty()) {
                    sb.appendLine("  • $line")
                }
            }
        }
        @Suppress("UNCHECKED_CAST")
        val dom = bm["dominance_metrics"] as? Map<*, *>
        if (dom != null && dom.isNotEmpty()) {
            sb.appendLine("Dominance metrics (backend): ${formatDominanceMetricsCompact(dom)}")
        }
        val policy = bm["policy_version"] as? String
        if (!policy.isNullOrBlank()) {
            sb.appendLine("Policy: $policy")
        }
    } else {
        sb.appendLine("Evidence quality: (backend metadata not present in response)")
    }

    if (cr != null && cr.isNotEmpty()) {
        sb.appendLine("Context resolution:")
        cr.forEach { (k, v) ->
            sb.appendLine("  $k: $v")
        }
    }

    sb.appendLine()
}

/**
 * Backend-supplied routing only: [evidence_first_meta], presence of [evidence_bundle] in the payload.
 * No client-side inference of ask path beyond echoing backend keys/values.
 */
private fun appendResponseProvenanceSection(sb: StringBuilder, response: RuntimeResponse) {
    val meta = response.metadata["evidence_first_meta"] as? Map<*, *>
    val hasBundle = response.metadata.containsKey("evidence_bundle") && response.metadata["evidence_bundle"] != null

    sb.appendLine("Response provenance (backend)")
    sb.appendLine("──────────────────────────")
    if (!hasBundle && meta.isNullOrEmpty()) {
        sb.appendLine("(no evidence_first_meta or evidence_bundle in response)")
        sb.appendLine()
        return
    }
    if (hasBundle) {
        sb.appendLine("evidence_bundle: present in response")
    }
    if (!meta.isNullOrEmpty()) {
        meta.entries.sortedBy { it.key.toString() }.forEach { (k, v) ->
            sb.appendLine("  ${k}: $v")
        }
    }
    sb.appendLine()
}

private fun formatDominanceMetricsCompact(dom: Map<*, *>): String {
    return dom.entries.joinToString(", ") { (k, v) -> "$k=$v" }
}
