package ai.motadata.plugin.ask

/**
 * Feature flags for Ask (no UI; configure via JVM / environment).
 *
 * Evidence-first Ask: `-Dmotadata.ask.evidence_first=true` or `MOTADATA_PLUGIN_ASK_EVIDENCE_FIRST=1`.
 * When enabled, the plugin obtains evidence from the **Context Layer** (`MOTADATA_CONTEXT_LAYER_URL`,
 * default `http://127.0.0.1:8091`) or installed CLI, then calls `POST /v1/ask` with `ask_request.v1.0`.
 * Controlled fallback uses `POST /v0/ask` with `evidence_first` if export or `/v1/ask` fails.
 */
object MotadataAskFlags {

    fun isEvidenceFirstAskEnabled(): Boolean {
        val prop = System.getProperty("motadata.ask.evidence_first", "").trim()
        if (prop.equals("true", ignoreCase = true) || prop == "1") {
            return true
        }
        val env = System.getenv("MOTADATA_PLUGIN_ASK_EVIDENCE_FIRST")?.trim()
        return env == "1" || env.equals("true", ignoreCase = true)
    }
}
