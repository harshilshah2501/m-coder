from __future__ import annotations

import tempfile
from pathlib import Path

from runtime.layer5.evidence.config import SnippetConfig
from runtime.layer5.evidence.snippet import extract_snippet
from runtime.layer5.evidence.snippet_anchor_quality import pick_best_anchor_line


def test_pick_best_prefers_implementation_line_over_copyright_header():
    bodies = [
        "/* Copyright (c) Motadata 2025. All rights reserved.",
        " * proprietary and confidential",
        " */",
        "package com.mindarray.aiops;",
        "",
        "public class AvailabilityCorrelationEngine {",
        "  public void processCorrelationAlerts() { }",
        "}",
    ]
    tokens = ("correlation", "alert", "motadata")
    idx, matched = pick_best_anchor_line(bodies, tokens)
    # First lines match generic "motadata"; best score should land on implementation.
    assert idx >= 4
    assert "correlation" in matched or "alert" in matched


def test_extract_snippet_skips_banner_for_domain_tokens(tmp_path: Path):
    java = """/*
 * Copyright (c) Motadata 2025. All rights reserved.
 */
package com.example;

public class X {
  public void handleCorrelation() {
    alert();
  }
}
"""
    p = tmp_path / "src" / "main" / "java" / "X.java"
    p.parent.mkdir(parents=True)
    p.write_text(java, encoding="utf-8")
    span = extract_snippet(
        canonical_root=tmp_path,
        relative_path="src/main/java/X.java",
        query_tokens=("correlation", "alert"),
        config=SnippetConfig(context_lines_before=0, context_lines_after=2),
    )
    assert span.selection_reason.value == "query_token_substring_anchor"
    assert "handleCorrelation" in span.text or "correlation" in span.text.lower()
    assert "Copyright" not in span.text.split("\n")[0] or "handleCorrelation" in span.text
