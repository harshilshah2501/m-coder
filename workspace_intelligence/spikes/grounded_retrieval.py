"""
Spike: Workspace-Local Retrieval for Layer-5 Wave 1.

Agent A1: Grounded Ask Spike

MISSION:
    Prove that workspace-local retrieval in WSL can return relevant
    grounded files/evidence quickly via a thin, integration-light vertical slice.

APPROACH:
    - Lexical-first retrieval (substring/regex search)
    - Simple file inventory scanning
    - Naive snippet extraction around matches
    - Provisional evidence payload shape
    - NO GPU dependency, NO embeddings, NO graph traversal

This is intentionally ugly but working.

LAYER-5 NOTE:
    This is a provisional spike implementation. It will be superseded by
    production L5.2/L5.3 implementations. Do not treat this as final
    architecture.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class EvidenceSnippet:
    """A snippet of evidence from a file."""
    
    line_start: int
    line_end: int
    content: str
    match_line: int  # The primary line where the match occurred
    match_text: str  # The matched text/token


@dataclass
class GroundedEvidence:
    """Evidence payload for a single file."""
    
    file_path: str  # Repo-relative path
    relevance_score: float  # 0.0 to 1.0
    match_count: int
    snippets: List[EvidenceSnippet] = field(default_factory=list)
    selection_reason: str = ""


@dataclass
class RetrievalResult:
    """Result of workspace-local retrieval."""
    
    query: str
    workspace_root: str
    evidence: List[GroundedEvidence] = field(default_factory=list)
    files_scanned: int = 0
    retrieval_ms: float = 0.0
    indexing_ms: float = 0.0
    total_ms: float = 0.0


@dataclass
class RetrievalConfig:
    """Configuration for workspace-local retrieval."""
    
    max_files: int = 20  # Max files to return
    max_snippets_per_file: int = 3  # Max snippets per file
    snippet_context_lines: int = 3  # Lines before/after match
    max_file_size_bytes: int = 500_000  # Skip files larger than this
    include_extensions: Optional[List[str]] = None  # e.g., ['.py', '.java']
    exclude_patterns: List[str] = field(default_factory=lambda: [
        '__pycache__',
        '.git',
        'node_modules',
        '.venv',
        'venv',
        '.pytest_cache',
        '__snapshots__',
        'dist',
        'build',
        '.mypy_cache',
    ])


class WorkspaceLocalRetriever:
    """
    Workspace-local retrieval using lexical/regex search.
    
    This is a spike implementation prioritizing simplicity over sophistication.
    """
    
    def __init__(self, workspace_root: str, config: Optional[RetrievalConfig] = None):
        self.workspace_root = Path(workspace_root).resolve()
        self.config = config or RetrievalConfig()
        self._file_index: Optional[List[Path]] = None
    
    def _should_include_file(self, path: Path) -> bool:
        """Check if file should be included in search."""
        path_str = str(path)
        
        for pattern in self.config.exclude_patterns:
            if pattern in path_str:
                return False
        
        if not path.is_file():
            return False
        
        if self.config.include_extensions:
            if path.suffix not in self.config.include_extensions:
                return False
        
        try:
            if path.stat().st_size > self.config.max_file_size_bytes:
                return False
        except OSError:
            return False
        
        return True
    
    def _build_file_index(self) -> List[Path]:
        """Build simple file index by scanning workspace."""
        if self._file_index is not None:
            return self._file_index
        
        files: List[Path] = []
        for p in sorted(self.workspace_root.rglob("*")):
            if self._should_include_file(p):
                files.append(p)
        
        self._file_index = files
        return files
    
    def _extract_query_tokens(self, query: str) -> List[str]:
        """Extract search tokens from natural language query."""
        query_lower = query.lower()
        
        tokens: List[str] = []
        
        camel_case = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)*', query)
        tokens.extend([t.lower() for t in camel_case])
        
        snake_case = re.findall(r'[a-z]+(?:_[a-z]+)+', query_lower)
        tokens.extend(snake_case)
        
        words = re.findall(r'\b[a-z]{3,}\b', query_lower)
        tokens.extend(words)
        
        unique_tokens = list(dict.fromkeys(tokens))
        
        stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
                     'can', 'had', 'her', 'was', 'one', 'our', 'out', 'has',
                     'have', 'been', 'were', 'with', 'they', 'this', 'that',
                     'from', 'what', 'how', 'where', 'when', 'which', 'who',
                     'does', 'should', 'would', 'could', 'there', 'here'}
        
        filtered = [t for t in unique_tokens if t not in stopwords and len(t) >= 3]
        
        return filtered[:10]  # Limit tokens for performance
    
    def _read_file_safe(self, path: Path) -> Optional[str]:
        """Safely read file content."""
        try:
            return path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            return None
    
    def _extract_snippet(
        self,
        lines: List[str],
        match_line_idx: int,
        match_text: str
    ) -> EvidenceSnippet:
        """Extract a snippet around a match line."""
        ctx = self.config.snippet_context_lines
        start = max(0, match_line_idx - ctx)
        end = min(len(lines), match_line_idx + ctx + 1)
        
        snippet_lines = lines[start:end]
        content = '\n'.join(snippet_lines)
        
        return EvidenceSnippet(
            line_start=start + 1,  # 1-indexed
            line_end=end,
            content=content,
            match_line=match_line_idx + 1,  # 1-indexed
            match_text=match_text
        )
    
    def _search_file(
        self,
        path: Path,
        tokens: List[str]
    ) -> Optional[GroundedEvidence]:
        """Search a single file for query tokens."""
        content = self._read_file_safe(path)
        if content is None:
            return None
        
        content_lower = content.lower()
        lines = content.split('\n')
        
        match_count = 0
        matched_tokens: List[str] = []
        match_positions: List[Tuple[int, str]] = []  # (line_idx, token)
        
        for token in tokens:
            if token in content_lower:
                match_count += content_lower.count(token)
                matched_tokens.append(token)
                
                for idx, line in enumerate(lines):
                    if token in line.lower():
                        match_positions.append((idx, token))
                        break  # First match per token
        
        if not matched_tokens:
            return None
        
        relevance = len(matched_tokens) / len(tokens) if tokens else 0.0
        
        rel_path = str(path.relative_to(self.workspace_root))
        
        snippets: List[EvidenceSnippet] = []
        seen_lines: set = set()
        
        match_positions.sort(key=lambda x: x[0])
        
        for line_idx, token in match_positions:
            if len(snippets) >= self.config.max_snippets_per_file:
                break
            if line_idx in seen_lines:
                continue
            
            snippet = self._extract_snippet(lines, line_idx, token)
            snippets.append(snippet)
            
            for i in range(snippet.line_start - 1, snippet.line_end):
                seen_lines.add(i)
        
        return GroundedEvidence(
            file_path=rel_path,
            relevance_score=relevance,
            match_count=match_count,
            snippets=snippets,
            selection_reason=f"lexical:tokens:{','.join(matched_tokens[:3])}"
        )
    
    def retrieve(self, query: str) -> RetrievalResult:
        """
        Perform workspace-local retrieval for a query.
        
        Returns grounded evidence with file paths and snippets.
        """
        start_total = time.perf_counter()
        
        start_index = time.perf_counter()
        files = self._build_file_index()
        indexing_ms = (time.perf_counter() - start_index) * 1000
        
        start_retrieval = time.perf_counter()
        
        tokens = self._extract_query_tokens(query)
        
        if not tokens:
            return RetrievalResult(
                query=query,
                workspace_root=str(self.workspace_root),
                evidence=[],
                files_scanned=len(files),
                retrieval_ms=0.0,
                indexing_ms=indexing_ms,
                total_ms=(time.perf_counter() - start_total) * 1000
            )
        
        evidence_list: List[GroundedEvidence] = []
        
        for file_path in files:
            evidence = self._search_file(file_path, tokens)
            if evidence:
                evidence_list.append(evidence)
        
        evidence_list.sort(key=lambda e: (-e.relevance_score, -e.match_count))
        evidence_list = evidence_list[:self.config.max_files]
        
        retrieval_ms = (time.perf_counter() - start_retrieval) * 1000
        total_ms = (time.perf_counter() - start_total) * 1000
        
        return RetrievalResult(
            query=query,
            workspace_root=str(self.workspace_root),
            evidence=evidence_list,
            files_scanned=len(files),
            retrieval_ms=retrieval_ms,
            indexing_ms=indexing_ms,
            total_ms=total_ms
        )
    
    def retrieve_with_regex(
        self,
        query: str,
        pattern: Optional[str] = None
    ) -> RetrievalResult:
        """
        Retrieve with optional explicit regex pattern for symbol matching.
        
        If pattern is None, extracts patterns from query.
        """
        start_total = time.perf_counter()
        
        start_index = time.perf_counter()
        files = self._build_file_index()
        indexing_ms = (time.perf_counter() - start_index) * 1000
        
        start_retrieval = time.perf_counter()
        
        if pattern:
            patterns = [pattern]
        else:
            tokens = self._extract_query_tokens(query)
            patterns = [re.escape(t) for t in tokens]
        
        if not patterns:
            return RetrievalResult(
                query=query,
                workspace_root=str(self.workspace_root),
                evidence=[],
                files_scanned=len(files),
                retrieval_ms=0.0,
                indexing_ms=indexing_ms,
                total_ms=(time.perf_counter() - start_total) * 1000
            )
        
        combined_pattern = '|'.join(patterns)
        try:
            regex = re.compile(combined_pattern, re.IGNORECASE)
        except re.error:
            return self.retrieve(query)
        
        evidence_list: List[GroundedEvidence] = []
        
        for file_path in files:
            content = self._read_file_safe(file_path)
            if content is None:
                continue
            
            matches = list(regex.finditer(content))
            if not matches:
                continue
            
            lines = content.split('\n')
            rel_path = str(file_path.relative_to(self.workspace_root))
            
            match_positions: List[Tuple[int, str]] = []
            for m in matches:
                line_num = content[:m.start()].count('\n')
                match_positions.append((line_num, m.group()))
            
            snippets: List[EvidenceSnippet] = []
            seen_lines: set = set()
            
            for line_idx, matched_text in match_positions:
                if len(snippets) >= self.config.max_snippets_per_file:
                    break
                if line_idx in seen_lines:
                    continue
                
                snippet = self._extract_snippet(lines, line_idx, matched_text)
                snippets.append(snippet)
                
                for i in range(snippet.line_start - 1, snippet.line_end):
                    seen_lines.add(i)
            
            unique_matches = set(m.group().lower() for m in matches[:10])
            
            evidence_list.append(GroundedEvidence(
                file_path=rel_path,
                relevance_score=min(1.0, len(unique_matches) / max(len(patterns), 1)),
                match_count=len(matches),
                snippets=snippets,
                selection_reason=f"regex:pattern:{combined_pattern[:50]}"
            ))
        
        evidence_list.sort(key=lambda e: (-e.relevance_score, -e.match_count))
        evidence_list = evidence_list[:self.config.max_files]
        
        retrieval_ms = (time.perf_counter() - start_retrieval) * 1000
        total_ms = (time.perf_counter() - start_total) * 1000
        
        return RetrievalResult(
            query=query,
            workspace_root=str(self.workspace_root),
            evidence=evidence_list,
            files_scanned=len(files),
            retrieval_ms=retrieval_ms,
            indexing_ms=indexing_ms,
            total_ms=total_ms
        )


def format_evidence_payload(result: RetrievalResult) -> dict:
    """
    Format retrieval result as a provisional evidence payload.
    
    This is a draft shape for the evidence contract.
    """
    return {
        "query": result.query,
        "workspace_root": result.workspace_root,
        "timing": {
            "indexing_ms": round(result.indexing_ms, 2),
            "retrieval_ms": round(result.retrieval_ms, 2),
            "total_ms": round(result.total_ms, 2),
        },
        "stats": {
            "files_scanned": result.files_scanned,
            "files_returned": len(result.evidence),
        },
        "evidence": [
            {
                "file_path": e.file_path,
                "relevance_score": round(e.relevance_score, 3),
                "match_count": e.match_count,
                "selection_reason": e.selection_reason,
                "snippets": [
                    {
                        "line_range": [s.line_start, s.line_end],
                        "match_line": s.match_line,
                        "match_text": s.match_text,
                        "content": s.content,
                    }
                    for s in e.snippets
                ],
            }
            for e in result.evidence
        ],
    }
