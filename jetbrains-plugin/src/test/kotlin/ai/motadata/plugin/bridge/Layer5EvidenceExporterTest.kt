package ai.motadata.plugin.bridge

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Test

class Layer5EvidenceExporterTest {

    @Test
    fun `dev repo script fallback is disabled by default`() {
        assertFalse(Layer5EvidenceExporter.isDevRepoScriptFallbackEnabled())
    }

    @Test
    fun `default context layer URL is localhost 8091`() {
        assertEquals("http://127.0.0.1:8091", Layer5EvidenceExporter.resolveContextLayerBaseUrl())
    }
}
