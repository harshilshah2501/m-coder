package ai.motadata.plugin.bridge

/**
 * Plan-Gate / runtime HTTP base URL (Ask, execute, commit shadow). Separate from Context Layer (8091).
 *
 * - `-Dmotadata.plan_gate.url=http://<gpu-host>:8089` (On Host VM options), or
 * - `MOTADATA_PLAN_GATE_URL` in the IDE environment.
 *
 * Context Layer stays on WSL (`-Dmotadata.context_layer.url=http://127.0.0.1:8091`) so evidence indexes local files.
 */
object MotadataRuntimeConfig {

    private const val PROP_PLAN_GATE_URL = "motadata.plan_gate.url"
    private const val ENV_PLAN_GATE_URL = "MOTADATA_PLAN_GATE_URL"

    fun planGateBaseUrl(): String {
        System.getProperty(PROP_PLAN_GATE_URL)?.trim()?.takeIf { it.isNotEmpty() }?.let { return it }
        System.getenv(ENV_PLAN_GATE_URL)?.trim()?.takeIf { it.isNotEmpty() }?.let { return it }
        return "http://127.0.0.1:8089"
    }
}
