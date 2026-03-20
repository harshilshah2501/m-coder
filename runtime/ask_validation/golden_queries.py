"""
Golden query suite for Layer-5 grounded Ask validation.

Defines test queries with expected outcomes:
- Queries that SHOULD find relevant files (grounded)
- Queries that SHOULD return no-match with justification (valid no-match)

Each query includes expectations about:
- Whether files should be found
- Expected file patterns (substring matches)
- Expected selector involvement
- Whether no-match is acceptable with justification
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class QueryExpectation(Enum):
    """Expected outcome type for a golden query."""
    GROUNDED = "grounded"  # Files MUST be found
    NO_MATCH_VALID = "no_match_valid"  # No files expected; justification required
    EITHER_WITH_JUSTIFICATION = "either"  # Either grounded OR valid no-match


@dataclass
class GoldenQuery:
    """
    A golden query definition for validation.
    
    Attributes:
        id: Unique identifier for the query
        query: The natural language query text
        expectation: Expected outcome type
        expected_file_patterns: Substrings that should appear in found file paths (if grounded)
        expected_selectors: Selectors that should contribute (if grounded)
        repo_files: Files to create in test repo for this query
        description: Human-readable description of what this tests
        no_match_keywords: Keywords that should appear in no-match justification
    """
    id: str
    query: str
    expectation: QueryExpectation
    repo_files: dict[str, str] = field(default_factory=dict)
    expected_file_patterns: list[str] = field(default_factory=list)
    expected_selectors: list[str] = field(default_factory=list)
    description: str = ""
    no_match_keywords: list[str] = field(default_factory=list)


# Core golden query suite - minimal but representative
GOLDEN_QUERY_SUITE: list[GoldenQuery] = [
    # === GROUNDED QUERIES: Files MUST be found ===
    
    GoldenQuery(
        id="grounded_symbol_retry",
        query="Where is retry logic implemented?",
        expectation=QueryExpectation.GROUNDED,
        repo_files={
            "billing/retry.py": "def retry(func):\n    '''Retry decorator'''\n    pass\n",
            "billing/__init__.py": "",
        },
        expected_file_patterns=["retry"],
        expected_selectors=["symbols"],
        description="Symbol hint 'retry' should match retry.py",
    ),
    
    GoldenQuery(
        id="grounded_symbol_config",
        query="How does the configuration loader work?",
        expectation=QueryExpectation.GROUNDED,
        repo_files={
            "core/config.py": "class ConfigLoader:\n    def load(self):\n        pass\n",
            "core/settings.py": "DEFAULT_CONFIG = {}\n",
        },
        expected_file_patterns=["config"],
        expected_selectors=["symbols"],
        description="Symbol hints 'configuration' and 'loader' should match config files",
    ),
    
    GoldenQuery(
        id="grounded_symbol_database",
        query="Where is the database connection handled?",
        expectation=QueryExpectation.GROUNDED,
        repo_files={
            "db/connection.py": "class DatabaseConnection:\n    def connect(self):\n        pass\n",
            "db/__init__.py": "from .connection import DatabaseConnection\n",
        },
        expected_file_patterns=["db"],  # Just check for db/ directory match
        expected_selectors=["symbols"],
        description="Database-related symbols should find files in db/",
    ),
    
    GoldenQuery(
        id="grounded_explicit_file",
        query="Explain this code",
        expectation=QueryExpectation.GROUNDED,
        repo_files={
            "src/main.py": "def main():\n    return 42\n",
        },
        expected_file_patterns=["main.py"],
        expected_selectors=["direct"],
        description="Explicit file selection should be grounded",
    ),
    
    # === NO-MATCH QUERIES: No files expected, but justification required ===
    
    GoldenQuery(
        id="no_match_nonexistent_symbol",
        query="Where is the XYZ_NONEXISTENT_SYMBOL_12345 function?",
        expectation=QueryExpectation.NO_MATCH_VALID,
        repo_files={
            "utils.py": "def helper():\n    return 1\n",
        },
        no_match_keywords=["no grounded", "no context", "ungrounded"],
        description="Query for nonexistent symbol should return valid no-match",
    ),
    
    GoldenQuery(
        id="no_match_unrelated_tech",
        query="How does the Kubernetes CRD controller work?",
        expectation=QueryExpectation.NO_MATCH_VALID,
        repo_files={
            "app.py": "# Simple Python web app\nfrom flask import Flask\n",
        },
        no_match_keywords=["no grounded", "no context", "ungrounded"],
        description="Query about K8s in Flask app repo should return valid no-match",
    ),
    
    GoldenQuery(
        id="no_match_obscure_feature",
        query="Where is the quantum encryption module?",
        expectation=QueryExpectation.NO_MATCH_VALID,
        repo_files={
            "crypto/basic.py": "def simple_hash(data):\n    return hash(data)\n",
        },
        no_match_keywords=["no grounded", "no context", "ungrounded"],
        description="Query for nonexistent feature should return valid no-match",
    ),
    
    # === EDGE CASES ===
    
    GoldenQuery(
        id="edge_case_insensitive",
        query="Where is PROCESSFILES function?",
        expectation=QueryExpectation.GROUNDED,
        repo_files={
            "handler.py": "def processFiles():\n    pass\n",
        },
        expected_file_patterns=["handler"],
        expected_selectors=["symbols"],
        description="Case-insensitive symbol matching should work",
    ),
    
    GoldenQuery(
        id="edge_multiple_matches",
        query="How does error handling work?",
        expectation=QueryExpectation.GROUNDED,
        repo_files={
            "errors/base.py": "class BaseError(Exception):\n    pass\n",
            "errors/handlers.py": "def handle_error(e):\n    pass\n",
            "utils/validation.py": "def validate():\n    pass\n",
        },
        expected_file_patterns=["error"],
        expected_selectors=["symbols"],
        description="Multiple symbol matches should return grounded results",
    ),
]


def get_grounded_queries() -> list[GoldenQuery]:
    """Return only queries expected to be grounded."""
    return [q for q in GOLDEN_QUERY_SUITE if q.expectation == QueryExpectation.GROUNDED]


def get_no_match_queries() -> list[GoldenQuery]:
    """Return only queries expected to be valid no-match."""
    return [q for q in GOLDEN_QUERY_SUITE if q.expectation == QueryExpectation.NO_MATCH_VALID]
