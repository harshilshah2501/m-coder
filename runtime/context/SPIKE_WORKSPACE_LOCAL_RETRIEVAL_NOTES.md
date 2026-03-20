# Spike: Workspace-Local Retrieval (Agent A1)

**Agent**: A1 — Grounded Ask Spike  
**Date**: 2026-03-20  
**Status**: Complete — All validation checks passed

## Mission

Prove that workspace-local retrieval in WSL can return relevant grounded files/evidence quickly via a thin, integration-light vertical slice.

## Retrieval Method Used

### Primary: Lexical Token Matching

1. **Query tokenization**: Extract meaningful tokens from natural language queries
   - CamelCase detection (e.g., `ContextEngine`)
   - snake_case detection (e.g., `build_context`)
   - Word extraction (3+ chars, stopword filtered)
   - Limited to top 10 tokens for performance

2. **File scanning**: Direct filesystem walk with exclusion patterns
   - Excludes: `__pycache__`, `.git`, `node_modules`, `.venv`, etc.
   - File size cap: 500KB
   - Optional extension filtering

3. **Token matching**: Case-insensitive substring search
   - Count matches per token
   - Relevance score = matched_tokens / total_tokens

4. **Snippet extraction**: Context window around first match per token
   - Configurable context lines (default: 3 before/after)
   - Deduplication of overlapping snippets

### Optional: Regex Symbol Matching

Available via `retrieve_with_regex()` for explicit pattern search when caller knows exact symbols.

## What Worked

| Aspect | Result |
|--------|--------|
| Lexical retrieval | ✅ Effective for code-related queries |
| Token extraction | ✅ CamelCase/snake_case detection useful |
| File scanning | ✅ 1257 files indexed in ~480ms (cold) |
| Cached indexing | ✅ 0ms on subsequent queries |
| Per-query retrieval | ✅ 70-120ms average |
| Snippet extraction | ✅ Provides useful context |
| Evidence payload | ✅ Structured, serializable output |

## What Was Intentionally Skipped

- **Semantic/embedding retrieval**: Out of scope for lexical spike
- **Graph traversal**: Beyond minimal file scanning
- **Multi-language parsing**: Python AST only (via existing selectors)
- **Dirty buffer overlay**: Not needed for spike
- **Plan-Gate integration**: Bypassed — standalone harness
- **Final contract freeze**: Provisional shape only
- **GPU filesystem dependency**: Avoided by design

## Measured Latency Snapshot

**Environment**: Workspace with 1257 indexed files

| Metric | Value |
|--------|-------|
| Cold indexing | 481.28 ms |
| Warm indexing (cached) | 0.00 ms |
| Retrieval (min) | 73.72 ms |
| Retrieval (max) | 118.76 ms |
| Retrieval (avg) | 100.32 ms |
| Total cold query | ~600 ms |
| Total warm query | ~100 ms |

## Evidence Payload Shape (Provisional)

```json
{
  "query": "string",
  "workspace_root": "string",
  "timing": {
    "indexing_ms": 0.0,
    "retrieval_ms": 0.0,
    "total_ms": 0.0
  },
  "stats": {
    "files_scanned": 0,
    "files_returned": 0
  },
  "evidence": [
    {
      "file_path": "relative/path.py",
      "relevance_score": 0.0,
      "match_count": 0,
      "selection_reason": "lexical:tokens:...",
      "snippets": [
        {
          "line_range": [1, 5],
          "match_line": 3,
          "match_text": "matched_token",
          "content": "snippet content..."
        }
      ]
    }
  ]
}
```

## Validation Results

| Check | Status |
|-------|--------|
| At least one query returns ≥1 relevant file | ✅ 8/8 queries |
| Evidence-bearing output produced | ✅ |
| WSL-local retrieval (no GPU dependency) | ✅ |
| Timing readouts present | ✅ |
| Snippets extracted for evidence | ✅ |

## Files Created

- `runtime/context/spike_workspace_local_retrieval.py` — Core retrieval implementation
- `runtime/context/spike_grounded_ask_harness.py` — Runnable demo/harness
- `runtime/context/SPIKE_WORKSPACE_LOCAL_RETRIEVAL_NOTES.md` — This document

## Usage

```bash
# Run the spike harness
python3 -m runtime.context.spike_grounded_ask_harness [workspace_root]

# Programmatic usage
from runtime.context.spike_workspace_local_retrieval import (
    WorkspaceLocalRetriever,
    RetrievalConfig,
    format_evidence_payload,
)

retriever = WorkspaceLocalRetriever("/path/to/workspace")
result = retriever.retrieve("How does context engine work?")
payload = format_evidence_payload(result)
```

## Recommendations for A6 (Evidence Contract Design)

Based on this spike, the evidence contract should consider:

1. **Required fields**:
   - `file_path` (repo-relative)
   - `relevance_score` (0.0-1.0)
   - `selection_reason` (string describing why selected)
   - `snippets` (array of contextual excerpts)

2. **Snippet structure**:
   - Line range (start, end)
   - Match line (primary match location)
   - Match text (what was matched)
   - Content (actual snippet text)

3. **Timing metadata**:
   - Include timing for performance monitoring
   - Separate indexing from retrieval time

4. **Stats metadata**:
   - Files scanned vs returned
   - Useful for understanding retrieval coverage

5. **Extensibility**:
   - `selection_reason` pattern allows multiple retrieval methods
   - Current: `lexical:tokens:...`, `regex:pattern:...`
   - Future: `semantic:embedding:...`, `graph:neighbor:...`

6. **Compatibility with existing contracts**:
   - Structure is compatible with `SelectedContextRef` and `ContextItem`
   - Can be adapted to fit `ContextBundle` pattern if needed
