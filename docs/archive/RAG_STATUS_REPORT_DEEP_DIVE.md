# RAG-Datastore Project Status Report (Deep-Dive)

**Date:** December 15, 2025
**Status:** Production Ready (with legacy cleanup required)
**Pass Rate:** 60% (Evaluation)

---

## 1. Executive Summary

The RAG-Datastore project is a production-deployed Anti-Hallucination RAG system designed to provide grounded code assistance for the Motadata codebase. It uses a hybrid retrieval approach combining **Qdrant** (vector search) and **Neo4j** (graph relationships) to feed context into a fine-tuned **vLLM** model.

The system is currently in a stable state with a defined startup orchestration (`orchestrator.sh`) and active API (`rag_api.py`). However, the codebase contains significant "dead code" from previous iterations (ChromaDB migration scripts, static AST JSON dumps) that should be purged to avoid confusion.

---

## 2. Active Architecture (The "Source of Truth")

The following components represent the active, production-critical path. Any file not listed here or in the dependency tree is a candidate for archiving.

### 2.1 Core Services
| Service | Port | Description | Status |
|---------|------|-------------|--------|
| **RAG API** | `8081` | Main entry point (`rag_api.py`). Handles search, context injection, and tool calling. | ✅ Active |
| **vLLM Server** | `8000` | Fine-tuned `motadata-coder` model inference. | ✅ Active |
| **vLLM Wrapper** | `8080` | Anti-repetition and formatting layer. | ✅ Active |
| **Qdrant** | `6333` | Vector database for semantic code search. | ✅ Active |
| **Neo4j** | `7474` | Graph database for class/method relationships. | ✅ Active |

### 2.2 Key Files
*   **`rag-system/rag_api.py`**: The monolithic API server. Implements the `/v1/chat/completions` endpoint, integrates `project_indexer`, and handles tool execution.
*   **`rag-system/project_indexer.py`**: The **active** indexing logic. Uses regex-based parsing to dynamically index projects into Qdrant. **Does NOT use `ast_nodes.json`.**
*   **`rag-system/orchestrator.sh`**: The production startup script. Manages the dependency chain (Docker -> vLLM -> Wrapper -> API).
*   **`rag-system/diagnostic_logger.py`**: Provides 4-layer observability into RAG performance.
*   **`rag-system/docker-compose.yml`**: Infrastructure definition for Qdrant and Neo4j.

---

## 3. Component Deep-Dive

### 3.1 Indexing Subsystem
*   **Current State**: Dynamic, regex-based indexing via `project_indexer.py`.
*   **Legacy State**: Static, AST-based indexing via `qdrant_indexer.py` consuming `ast_nodes.json`.
*   **Status**: The system has moved to dynamic indexing to support multi-project workflows. The static AST files are obsolete.

### 3.2 Vector Database (Qdrant)
*   **Collection**: `motadata_code` (legacy default) or project-specific collections (e.g., `project_<hash>`).
*   **Health**: Stable, managed via Docker.

### 3.3 Graph Database (Neo4j)
*   **Status**: Optional. The API (`rag_api.py`) can start without it.
*   **Data**: Currently populated with ~10k nodes for the core Motadata project. New projects do not automatically get graph indexing (a known limitation).

---

## 4. Cleanup Recommendations (The "Purge")

The following files are identified as **technical debt** or **artifacts** and should be removed or archived.

### 4.1 Files to Delete/Archive
| File Path | Reason for Removal |
|-----------|--------------------|
| `rag-system/migrate_chroma_to_qdrant.py` | One-off migration script. ChromaDB is no longer used. |
| `rag-system/filter_ast.py` | Unused helper script for the old AST JSON format. |
| `rag-system/test_vllm_direct.py` | Ad-hoc testing script. |
| `rag-system/ast_nodes.json` | **Large static dump (100MB+)**. Obsolete; replaced by dynamic indexing. |
| `rag-system/ast_nodes_small.json` | Sample data for the obsolete static indexer. |
| `rag-system/curl_result.json` | Temporary debug output. |
| `rag-system/payload_dump.json` | Temporary debug output. |
| `rag-system/vllm_direct_output.txt` | Temporary debug output. |
| `rag-system/qdrant_indexer.py` | **Legacy Indexer**. Relies on `ast_nodes.json`. Superseded by `project_indexer.py`. |
| `rag-system/20251212*_session.md` | Old session logs. |

### 4.2 Documentation Gaps
*   **`README.md`**: References `migrate_chroma_to_qdrant.py` which should be removed.
*   **`ARCHITECTURE.md`**: Describes the "Re-parse Java code (generates ast_nodes.json)" workflow, which is now legacy. Needs update to reflect `project_indexer.py`'s regex approach.

---

## 5. Testing & Evaluation Status

*   **Overall Pass Rate**: 60% (6/10 tests passing).
*   **Strengths**:
    *   **Knowledge Retrieval**: 100% pass.
    *   **RCA/Debugging**: 100% pass.
*   **Weaknesses**:
    *   **Multi-File Feature Creation**: 0% pass. The model struggles to scaffold complex features across multiple files.
    *   **Code Review**: 50% pass. Misses subtle security issues.

---

## 6. Next Steps

1.  **Execute Purge**: Move the listed files to `archive/legacy_v2/` or delete them.
2.  **Update Docs**: Rewrite `ARCHITECTURE.md` to match the code in `project_indexer.py`.
3.  **Fix Qdrant Stability**: Investigate why Qdrant occasionally restarts (mentioned in logs).
4.  **Improve Training Data**: Focus on "Type B" multi-file tasks to improve the 0% pass rate.
