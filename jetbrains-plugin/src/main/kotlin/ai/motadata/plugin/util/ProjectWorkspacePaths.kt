package ai.motadata.plugin.util

import com.intellij.openapi.module.ModuleManager
import com.intellij.openapi.project.Project
import com.intellij.openapi.roots.ModuleRootManager
import com.intellij.openapi.roots.ProjectFileIndex
import com.intellij.openapi.roots.ProjectRootManager
import com.intellij.openapi.vfs.VirtualFile

/** Repo / Layer5 index root. Gateway may set [Project.getBasePath] to Roaming `.../JetBrains/.../projects/<hash>`; we use anchor file content root, module roots, then project roots. */
object ProjectWorkspacePaths {

    private const val WORKSPACE_OVERRIDE_PROP = "motadata.layer5.workspace_root"
    private const val ENV_LAYER5_WORKSPACE = "MOTADATA_LAYER5_WORKSPACE_ROOT"
    private const val ENV_MOTADATA_ROOT = "MOTADATA_ROOT"

    /**
     * Explicit checkout path (highest priority). Use when VM `-D` is not visible to the backend JVM
     * (Toolbox / Remote Dev) — set env in the **host** IDE launch environment instead.
     */
    private fun explicitWorkspaceOverride(): String? {
        System.getProperty(WORKSPACE_OVERRIDE_PROP)?.trim()?.takeIf { it.isNotEmpty() }?.let { return it }
        System.getenv(ENV_LAYER5_WORKSPACE)?.trim()?.takeIf { it.isNotEmpty() }?.let { return it }
        System.getenv(ENV_MOTADATA_ROOT)?.trim()?.takeIf { it.isNotEmpty() }?.let { return it }
        return null
    }

    fun looksLikeJetBrainsProjectMetadataDir(path: String): Boolean {
        if (path.isBlank()) return false
        val p = path.replace('\\', '/')
        if (!p.contains("/JetBrains/", ignoreCase = true)) return false
        return p.contains("/projects/", ignoreCase = true)
    }

    /** `-Dmotadata.layer5.workspace_root`, then `MOTADATA_LAYER5_WORKSPACE_ROOT`, then `MOTADATA_ROOT`; else anchor/module roots. */
    fun layer5WorkspaceRoot(project: Project, anchorFile: VirtualFile? = null): String {
        explicitWorkspaceOverride()?.let { return it }

        val fromAnchor = anchorFile?.let { vf ->
            ProjectFileIndex.getInstance(project).getContentRootForFile(vf, false)
                ?.takeIf { it.isValid && it.isDirectory }
                ?.path?.trim()
                ?.takeIf { it.isNotEmpty() && !looksLikeJetBrainsProjectMetadataDir(it) }
        }
        if (fromAnchor != null) {
            return fromAnchor
        }

        val roots = collectContentRootPaths(project)
        val base = project.basePath?.trim()?.takeIf { it.isNotEmpty() }

        if (base != null && looksLikeJetBrainsProjectMetadataDir(base)) {
            val nonMetadata = roots.filter { !looksLikeJetBrainsProjectMetadataDir(it) }
            return nonMetadata.firstOrNull()
                ?: roots.firstOrNull()
                ?: base
        }
        if (!base.isNullOrEmpty()) {
            return base
        }
        return roots.firstOrNull().orEmpty()
    }

    private fun collectContentRootPaths(project: Project): List<String> {
        val prm = ProjectRootManager.getInstance(project)
        val fromProject = prm.contentRoots.asSequence()
        val fromModules = ModuleManager.getInstance(project).modules.asSequence()
            .filter { !it.isDisposed }
            .flatMap { ModuleRootManager.getInstance(it).contentRoots.asSequence() }

        return (fromProject + fromModules)
            .filter { it.isValid && it.isDirectory }
            .mapNotNull { it.path?.trim()?.takeIf { p -> p.isNotEmpty() } }
            .distinct()
            .sortedBy { it.length }
            .toList()
    }

    fun isDescendantPath(rootPath: String, candidatePath: String): Boolean {
        if (rootPath.isBlank() || candidatePath.isBlank()) return false
        val root = rootPath.trimEnd('/', '\\').replace('\\', '/')
        val child = candidatePath.trimEnd('/', '\\').replace('\\', '/')
        return child.equals(root, ignoreCase = true) ||
            child.startsWith("$root/", ignoreCase = true)
    }

    fun relativePathIfUnder(rootPath: String, filePath: String): String? {
        if (!isDescendantPath(rootPath, filePath)) return null
        val root = rootPath.trimEnd('/', '\\').replace('\\', '/')
        val child = filePath.replace('\\', '/')
        val prefix = "$root/"
        return when {
            child.equals(root, ignoreCase = true) -> ""
            child.startsWith(prefix, ignoreCase = true) -> child.substring(prefix.length).trimStart('/')
            else -> null
        }
    }
}
