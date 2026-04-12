# Layer-5 Spikes — Workspace Intelligence

This directory contains provisional spike implementations proving specific Layer-5 capabilities.

## IMPORTANT: Spike Status

**Code in this directory is intentionally minimal and may be ugly-but-working.**

- It is NOT final architecture
- It will be superseded by production implementations in L5.2/L5.3
- Do not harden or refactor without explicit direction

## Current Spikes

### A1: Grounded Retrieval (`grounded_retrieval.py`)

**Agent**: A1 — Grounded Ask Spike  
**Date**: 2026-03-20  
**Status**: Complete — All validation checks passed

Proves that workspace-local retrieval in WSL can return relevant grounded files/evidence quickly.

#### Approach

- Lexical-first retrieval (substring/regex search)
- Simple file inventory scanning
- Naive snippet extraction around matches
- Provisional evidence payload shape
- NO GPU dependency, NO embeddings, NO graph traversal

#### Usage

```bash
# Run the spike harness
python3 -m workspace_intelligence.spikes.grounded_retrieval_harness [workspace_root]

# Programmatic usage
from workspace_intelligence.spikes.grounded_retrieval import (
    WorkspaceLocalRetriever,
    RetrievalConfig,
    format_evidence_payload,
)

retriever = WorkspaceLocalRetriever("/path/to/workspace")
result = retriever.retrieve("How does context engine work?")
payload = format_evidence_payload(result)
```

#### Timing (measured)

| Metric | Value |
|--------|-------|
| Cold indexing | ~480ms |
| Warm indexing (cached) | 0ms |
| Per-query retrieval | 70-120ms |
| Total cold query | ~600ms |
| Total warm query | ~100ms |

#### What This Spike Intentionally Skipped

- Semantic/embedding retrieval
- Graph traversal beyond file scanning
- Multi-language parsing
- Dirty buffer overlay
- Plan-Gate integration (standalone harness)
- Final contract freeze (provisional shape only)

## Recommendations for Follow-up (A6)

The evidence contract should include:

1. **Required fields**: `file_path`, `relevance_score`, `selection_reason`, `snippets`
2. **Snippet structure**: `line_range`, `match_line`, `match_text`, `content`
3. **Metadata**: Timing, stats (files scanned/returned)
4. **Extensibility**: `selection_reason` pattern supports multiple retrieval methods
