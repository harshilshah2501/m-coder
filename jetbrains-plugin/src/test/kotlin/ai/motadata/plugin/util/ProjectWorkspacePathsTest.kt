package ai.motadata.plugin.util

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

class ProjectWorkspacePathsTest {

    @Test
    fun detectsJetBrainsRoamingProjectDir() {
        val wsl =
            "/mnt/c/Users/Harshil Shah/AppData/Roaming/JetBrains/IntelliJIdea2026.1/projects/ac852201fe776dbecf4a042e9084f9c8f10c20de"
        assertTrue(ProjectWorkspacePaths.looksLikeJetBrainsProjectMetadataDir(wsl))
        assertTrue(
            ProjectWorkspacePaths.looksLikeJetBrainsProjectMetadataDir(
                """C:\Users\X\AppData\Roaming\JetBrains\IntelliJIdea2026.1\projects\deadbeef"""
            )
        )
    }

    @Test
    fun normalRepoBasePathNotMetadata() {
        assertFalse(ProjectWorkspacePaths.looksLikeJetBrainsProjectMetadataDir("/home/user/Motadata"))
        assertFalse(ProjectWorkspacePaths.looksLikeJetBrainsProjectMetadataDir(""))
    }

    @Test
    fun relativePathIfUnder() {
        assertEquals(
            "src/Main.kt",
            ProjectWorkspacePaths.relativePathIfUnder("/home/proj", "/home/proj/src/Main.kt")
        )
        assertNull(ProjectWorkspacePaths.relativePathIfUnder("/home/other", "/home/proj/src/Main.kt"))
    }
}
