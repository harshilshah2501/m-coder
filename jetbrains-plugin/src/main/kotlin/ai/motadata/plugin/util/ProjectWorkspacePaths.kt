package ai.motadata.plugin.util

import com.intellij.openapi.project.Project
import com.intellij.openapi.roots.ProjectRootManager

/**
 * Resolves a filesystem directory for repo-relative paths, git, and Context Layer indexing.
 *
 * [Project.getBasePath] often points at the `.idea` parent, but under **Remote Development /
 * JetBrains Gateway** it can be JetBrains Roaming metadata, e.g.
 * `.../JetBrains/IntelliJIdea2026.1/projects/<hash>`, which is not the checkout and breaks
 * `workspace_root` for `/v1/export_evidence`. Content roots from the project model point at
 * real sources.
 */
object ProjectWorkspacePaths {

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
     * content root (shortest path first so a monorepo outer root wins over nested modules).
     */
    fun layer5WorkspaceRoot(project: Project): String {
        val roots = ProjectRootManager.getInstance(project).contentRoots
            .asSequence()
            .filter { it.isValid && it.isDirectory }
            .mapNotNull { it.path?.trim()?.takeIf { p -> p.isNotEmpty() } }
            .sortedBy { it.length }
            .toList()

        val base = project.basePath?.trim()?.takeIf { it.isNotEmpty() }

        if (base != null && looksLikeJetBrainsProjectMetadataDir(base)) {
            return roots.firstOrNull() ?: base
        }
        if (!base.isNullOrEmpty()) {
            return base
        }
        return roots.firstOrNull().orEmpty()
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
