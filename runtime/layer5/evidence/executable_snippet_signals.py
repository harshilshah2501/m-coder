"""
Shared heuristics for “executable” Java/Python-like snippets (control-flow / exits).

Used by EXPLAIN_DEBUG method-body diagnostics and snippet re-anchoring so both
stay aligned on one definition of “not declarations-only”.
"""

from __future__ import annotations

import re

# Executable control flow — branch / loop / exit / guards (not declarations-only).
# Avoid treating Javadoc ``@return`` as a Java ``return`` via negative lookbehind.
EXECUTABLE_CF = re.compile(
    r"\b(if|while|for|switch)\s*\(|"
    r"\b(do)\s*\{|"
    r"\b(try|catch|finally)\b|"
    r"\belse\b\s*(?:if\b|\{)|"
    r"\bcase\b\s+[^:]+?\s*(?:->|:)|"
    r"->\s*\{|"
    r"(?<![@])\breturn\b|"
    r"\bthrow\b|"
    r"[!=]=\s*null\b|"
    r"\?\s*[^:]+:",
    re.I,
)


def text_has_executable_control_flow(text: str) -> bool:
    t = text.strip()
    if len(t) < 12:
        return False
    return bool(EXECUTABLE_CF.search(t))
