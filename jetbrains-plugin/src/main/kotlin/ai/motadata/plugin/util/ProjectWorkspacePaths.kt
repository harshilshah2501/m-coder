package ai.motadata.plugin.util

import com.intellij.openapi.module.ModuleManager
import com.intellij.openapi.project.Project
import com.intellij.openapi.roots.ModuleRootManager
import com.intellij.openapi.roots.ProjectFileIndex
import com.intellij.openapi.roots.ProjectRootManager
import com.intellij.openapi.vfs.VirtualFile

/**
 * Resolves a filesystem directory for repo-relative paths, git, and Context Layer indexing.
 *
 * [Project.getBasePath] often points at the `.idea` parent, but under **Remote Development /
 * JetBrains Gateway** it can be JetBrains Roaming metadata, e.g.
 * `.../JetBrains/IntelliJIdea2026.1/projects/<hash>`, which is not the checkout and breaks
 * `workspace_root` for `/v1/export_evidence`. Content roots from the project model point at
 * real sources.
 *
 * **Important:** [ProjectRootManager.getInstance(project).contentRoots] is often **empty** in
 * Gateway/remote flows even when modules have roots; we also scan [ModuleRootManager]. When an
 * anchor file is provided (e.g. open editor), [ProjectFileIndex.getContentRootForFile] is used first.
 */
object ProjectWorkspacePaths {

    private const val WORKSPACE_OVERRIDE_PROP = "motadata.layer5.workspace_root"

    /**
     * True when [path] looks like JetBrains config `.../JetBrains/.../projects/...` (not the repo).
     */
    fun looksLikeJetBrainsProjectMetadataDir(path: String): Boolean {
        if (path.isBlank()) return false
        val p = path.replace('\\', '/')
        if (!p.contains("/JetBrains/", ignoreCase = true)) return false
        return p.contains("/projects/", ignoreCase = true)
    }

    /**
     * Prefer [Project.getBasePath] when it is not a JetBrains metadata dir; otherwise first
     * usable root (shortest path first so a monorepo outer root wins over nested modules).
     *
     * Override (escape hatch): JVM property `-Dmotadata.layer5.workspace_root=/abs/path` (e.g. VM options).
     *
     * @param anchorFile Optional focused file (e.g. from the action event). Its content root is the
     *   most reliable signal when [Project.getBasePath] is Gateway metadata.
     */
    fun layer5WorkspaceRoot(project: Project, anchorFile: VirtualFile? = null): String {
        System.getProperty(WORKSPACE_OVERRIDE_PROP)?.trim()?.takeIf { it.isNotEmpty() }?.let { return it }

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

    /**
     * Repo-relative path of [filePath] under [rootPath], or null if not under root.
     */
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
