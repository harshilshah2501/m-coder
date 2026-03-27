package ai.motadata.plugin.bridge

import com.google.gson.Gson
import com.google.gson.JsonParser
import java.io.File
import java.io.OutputStreamWriter
import java.net.ConnectException
import java.net.HttpURLConnection
import java.net.SocketTimeoutException
import java.net.URL
import java.net.UnknownHostException
import java.nio.charset.StandardCharsets
import java.util.concurrent.TimeUnit

/**
 * Resolves `layer5.evidence_bundle.v1` for evidence-first Ask before [POST /v1/ask].
 *
 * **Deployment order (packaged WSL model):**
 * 1. **Context Layer HTTP** — `MOTADATA_CONTEXT_LAYER_URL` / `motadata.context_layer.url`
 *    (default `http://127.0.0.1:8091`), unless `MOTADATA_CONTEXT_LAYER_DISABLE_HTTP=1`.
 *    If the server returns an HTTP error body, that is [EvidenceExportOutcome.ServiceFailure]
 *    (no silent `/v0/ask` fallback).
 * 2. **Installed CLI** — `MOTADATA_CONTEXT_LAYER_CLI` / `motadata.context_layer.cli`.
 * 3. **Dev-only** — repo script when `MOTADATA_CONTEXT_LAYER_DEV_REPO_SCRIPT_FALLBACK=1`.
 */
object Layer5EvidenceExporter {

    private const val DEFAULT_SERVICE_URL = "http://127.0.0.1:8091"
    private const val PROP_SERVICE_URL = "motadata.context_layer.url"
    private const val ENV_SERVICE_URL = "MOTADATA_CONTEXT_LAYER_URL"
    private const val ENV_DISABLE_HTTP = "MOTADATA_CONTEXT_LAYER_DISABLE_HTTP"

    private const val PROP_CLI = "motadata.context_layer.cli"
    private const val ENV_CLI = "MOTADATA_CONTEXT_LAYER_CLI"

    private const val PROP_DEV_SCRIPT_FALLBACK = "motadata.context_layer.dev_repo_script_fallback"
    private const val ENV_DEV_SCRIPT_FALLBACK = "MOTADATA_CONTEXT_LAYER_DEV_REPO_SCRIPT_FALLBACK"

    private const val DEFAULT_SCRIPT_RELATIVE = "runtime/scripts/layer5_export_evidence.py"
    private const val PROP_SCRIPT = "motadata.layer5.evidence.script"
    private const val ENV_SCRIPT = "MOTADATA_LAYER5_EVIDENCE_SCRIPT"
    private const val PROP_PYTHON = "motadata.python.executable"
    private const val ENV_PYTHON = "MOTADATA_PYTHON"

    private val gson = Gson()

    private const val HTTP_CONNECT_MS = 10_000
    private const val HTTP_READ_MS = 120_000

    internal fun isDevRepoScriptFallbackEnabled(): Boolean {
        val p = System.getProperty(PROP_DEV_SCRIPT_FALLBACK, "").trim().lowercase()
        if (p == "true" || p == "1" || p == "yes") return true
        val e = (System.getenv(ENV_DEV_SCRIPT_FALLBACK) ?: "").trim().lowercase()
        return e == "1" || e == "true" || e == "yes"
    }

    internal fun isHttpDisabled(): Boolean {
        val e = (System.getenv(ENV_DISABLE_HTTP) ?: "").trim().lowercase()
        return e == "1" || e == "true" || e == "yes"
    }

    internal fun resolveContextLayerBaseUrl(): String {
        System.getProperty(PROP_SERVICE_URL)?.trim()?.takeIf { it.isNotEmpty() }?.let { return it }
        System.getenv(ENV_SERVICE_URL)?.trim()?.takeIf { it.isNotEmpty() }?.let { return it }
        return DEFAULT_SERVICE_URL
    }

    /**
     * @param requestId optional; forwarded as `request_id` on HTTP POST `/v1/export_evidence` for log correlation with Plan-Gate.
     */
    fun tryExportEvidenceBundle(
        workspaceRoot: String,
        query: String,
        requestId: String? = null,
    ): EvidenceExportOutcome {
        val root = workspaceRoot.trim()
        val q = query.trim()
        if (root.isEmpty() || q.isEmpty()) {
            return EvidenceExportOutcome.Unreachable("empty_workspace_or_query")
        }

        if (!isHttpDisabled()) {
            when (val http = tryHttpExport(resolveContextLayerBaseUrl(), root, q, requestId)) {
                is EvidenceExportOutcome.ServiceFailure -> return http
                is EvidenceExportOutcome.Success -> return http
                is EvidenceExportOutcome.Unreachable -> { /* try CLI / dev */ }
            }
        }

        tryInstalledCliExport(root, q)?.let { return it }
        if (isDevRepoScriptFallbackEnabled()) {
            tryDevRepoScriptExport(root, q)?.let { return it }
        }

        return EvidenceExportOutcome.Unreachable("context_layer_unreachable_no_provider")
    }

    private fun tryHttpExport(
        baseUrl: String,
        workspaceRoot: String,
        query: String,
        requestId: String?,
    ): EvidenceExportOutcome {
        val base = baseUrl.trimEnd('/')
        if (base.isEmpty()) return EvidenceExportOutcome.Unreachable("empty_context_layer_url")
        val url = "$base/v1/export_evidence"
        return try {
            val conn = URL(url).openConnection() as HttpURLConnection
            conn.connectTimeout = HTTP_CONNECT_MS
            conn.readTimeout = HTTP_READ_MS
            conn.requestMethod = "POST"
            conn.doOutput = true
            conn.setRequestProperty("Content-Type", "application/json; charset=utf-8")
            val payload = buildMap {
                put("workspace_root", workspaceRoot)
                put("query", query)
                put("top_k", 8)
                val rid = requestId?.trim()
                if (!rid.isNullOrEmpty()) {
                    put("request_id", rid)
                }
            }
            OutputStreamWriter(conn.outputStream, StandardCharsets.UTF_8).use { it.write(gson.toJson(payload)) }
            val code = conn.responseCode
            val stream = if (code in 200..299) conn.inputStream else conn.errorStream ?: conn.inputStream
            val text = stream.use { String(it.readBytes(), StandardCharsets.UTF_8) }.trim()

            if (code !in 200..299) {
                return EvidenceExportOutcome.ServiceFailure(code, text)
            }
            if (!text.startsWith("{")) {
                return EvidenceExportOutcome.ServiceFailure(code, text.ifEmpty { "(empty body)" })
            }
            if (!isPlausibleEvidenceBundleJson(text)) {
                return EvidenceExportOutcome.ServiceFailure(code, text)
            }
            EvidenceExportOutcome.Success(text)
        } catch (_: UnknownHostException) {
            EvidenceExportOutcome.Unreachable("unknown_host")
        } catch (_: SocketTimeoutException) {
            EvidenceExportOutcome.Unreachable("timeout")
        } catch (_: ConnectException) {
            EvidenceExportOutcome.Unreachable("connection_refused")
        } catch (e: Exception) {
            EvidenceExportOutcome.Unreachable(e.message ?: "http_error")
        }
    }

    private fun isPlausibleEvidenceBundleJson(json: String): Boolean {
        return try {
            val o = JsonParser.parseString(json).asJsonObject
            o.get("schema_hint")?.asString == "layer5.evidence_bundle.v1"
        } catch (_: Exception) {
            false
        }
    }

    private fun tryInstalledCliExport(workspaceRoot: String, query: String): EvidenceExportOutcome? {
        val cli = System.getProperty(PROP_CLI)?.trim()?.takeIf { it.isNotEmpty() }
            ?: System.getenv(ENV_CLI)?.trim()?.takeIf { it.isNotEmpty() }
            ?: return null
        return runProcessExport(cli, listOf(cli, workspaceRoot), query, "cli")
    }

    private fun tryDevRepoScriptExport(workspaceRoot: String, query: String): EvidenceExportOutcome? {
        val script = System.getProperty(PROP_SCRIPT)?.trim()?.takeIf { it.isNotEmpty() }
            ?: System.getenv(ENV_SCRIPT)?.trim()?.takeIf { it.isNotEmpty() }
            ?: run {
                val candidate = File(workspaceRoot, DEFAULT_SCRIPT_RELATIVE)
                if (candidate.isFile) candidate.absolutePath else null
            }
            ?: return null
        val python = resolvePythonExecutable()
        return runProcessExport("$python $script", listOf(python, script, workspaceRoot), query, "dev_script")
    }

    private fun runProcessExport(
        label: String,
        command: List<String>,
        query: String,
        kind: String,
    ): EvidenceExportOutcome {
        return try {
            val pb = ProcessBuilder(command)
            pb.redirectErrorStream(false)
            val proc = pb.start()
            proc.outputStream.writer(StandardCharsets.UTF_8).use { w ->
                w.write(query)
                w.flush()
            }
            proc.outputStream.close()
            val stdout = proc.inputStream.use { String(it.readBytes(), StandardCharsets.UTF_8) }
            val stderr = proc.errorStream.use { String(it.readBytes(), StandardCharsets.UTF_8) }
            val finished = proc.waitFor(120, TimeUnit.SECONDS)
            if (!finished) {
                proc.destroyForcibly()
                return EvidenceExportOutcome.ServiceFailure(
                    0,
                    "{\"failure_class\":\"process_timeout\",\"message\":\"$kind $label\"}",
                )
            }
            if (proc.exitValue() != 0) {
                return EvidenceExportOutcome.ServiceFailure(
                    0,
                    "{\"failure_class\":\"${kind}_failed\",\"exitCode\":${proc.exitValue()},\"stderr\":${gson.toJson(stderr.trim())}}",
                )
            }
            val out = stdout.trim()
            if (!out.startsWith("{") || !isPlausibleEvidenceBundleJson(out)) {
                return EvidenceExportOutcome.ServiceFailure(
                    0,
                    "{\"failure_class\":\"${kind}_invalid_output\",\"message\":${gson.toJson(out.take(500))}}",
                )
            }
            EvidenceExportOutcome.Success(out)
        } catch (e: Exception) {
            EvidenceExportOutcome.ServiceFailure(0, "{\"failure_class\":\"${kind}_exception\",\"message\":${gson.toJson(e.message ?: "")}}")
        }
    }

    private fun resolvePythonExecutable(): String {
        System.getProperty(PROP_PYTHON)?.trim()?.takeIf { it.isNotEmpty() }?.let { return it }
        System.getenv(ENV_PYTHON)?.trim()?.takeIf { it.isNotEmpty() }?.let { return it }
        if (File("/usr/bin/python3").canExecute()) return "/usr/bin/python3"
        return "python3"
    }
}
