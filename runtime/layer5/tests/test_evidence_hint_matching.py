"""Hint matching for EXPLAIN_DEBUG selected-file body checks (camelCase Java)."""

from runtime.context_layer_service.evidence_api import (
    DebugGroundingTier,
    detect_selected_method_grounding,
    _java_snippet_has_implementation_signals,
    _selected_method_body_present,
    _hint_matches_selected_snippet,
)
from runtime.layer5.evidence.executable_snippet_signals import text_has_executable_control_flow


def test_executable_cf_null_guard_return_lambda():
    assert text_has_executable_control_flow("if (x != null) { ok(); }")
    assert text_has_executable_control_flow("void run() { return; }")
    assert text_has_executable_control_flow("Runnable r = () -> { log(); };")
    assert not text_has_executable_control_flow(" * @return the foo")


def test_hint_matches_camel_case_dispatch_and_parse_methods():
    hay = """
    class SNMPTrapProcessor {
      void dispatchTraps() { }
      protected void parsePdu() { }
    }
    """
    assert _hint_matches_selected_snippet("dispatch", hay)
    assert _hint_matches_selected_snippet("parse", hay)
    assert _hint_matches_selected_snippet("SNMPTrapProcessor", hay)


def test_selected_method_body_present_accepts_camel_methods():
    bundle = {
        "entries": [
            {
                "relative_path": "motadata/src/main/java/com/mindarray/nms/SNMPTrapProcessor.java",
                "snippet": {
                    "text": (
                        "void dispatchTraps() {\n  if (x == null) return;\n}\n"
                        "void parseTrap() {\n  try { read(); } catch (Exception e) { throw e; }\n}\n"
                    ),
                },
            }
        ]
    }
    hints = ["SNMPTrapProcessor", "parse", "dispatch"]
    assert _selected_method_body_present(bundle, "motadata/src/main/java/com/mindarray/nms/SNMPTrapProcessor.java", hints) is True


def test_java_impl_signals_accepts_tab_after_void():
    t = "public\tvoid\nfoo() {\n  return;\n}\n"
    assert _java_snippet_has_implementation_signals(t)


def test_java_impl_signals_substantial_brace_block():
    body = "{\n" + ("  //x\n" * 15) + "  if (q != null) { a(b); }\n}\n"
    assert len(body) >= 40
    assert _java_snippet_has_implementation_signals(body)
    assert text_has_executable_control_flow(body)


def test_selected_path_motadata_prefix_vs_index_entry():
    """selected_file may be src/... while bundle entry uses motadata/src/... (same file)."""
    bundle = {
        "entries": [
            {
                "relative_path": "motadata/src/main/java/com/mindarray/nms/SNMPTrapProcessor.java",
                "snippet": {
                    "text": "void x() {\n  if (a == b) { return; }\n}\n",
                },
            }
        ]
    }
    hints = ["SNMPTrapProcessor", "parse", "dispatch"]
    sel = "src/main/java/com/mindarray/nms/SNMPTrapProcessor.java"
    assert _selected_method_body_present(bundle, sel, hints) is True


def test_selected_method_body_false_when_only_empty_class_declaration():
    bundle = {
        "entries": [
            {
                "relative_path": "motadata/src/main/java/com/mindarray/nms/SNMPTrapProcessor.java",
                "snippet": {"text": "package x;\npublic class SNMPTrapProcessor {\n}\n"},
            }
        ]
    }
    hints = ["SNMPTrapProcessor", "parse", "dispatch"]
    assert _selected_method_body_present(bundle, "motadata/src/main/java/com/mindarray/nms/SNMPTrapProcessor.java", hints) is False


def test_selected_method_body_present_basename_hint_mid_file_window_without_class_name():
    """Snippet anchored mid-file may omit class line; basename hint + Java body signals suffice."""
    bundle = {
        "entries": [
            {
                "relative_path": "motadata/src/main/java/com/mindarray/nms/SNMPTrapProcessor.java",
                "snippet": {
                    "text": "  public void handleIncoming(byte[] raw) {\n    if (raw == null) {\n      return;\n    }\n    // process buffer\n  }\n",
                },
            }
        ]
    }
    hints = ["SNMPTrapProcessor", "parse", "dispatch"]
    assert _selected_method_body_present(bundle, "motadata/src/main/java/com/mindarray/nms/SNMPTrapProcessor.java", hints) is True


def test_detect_selected_method_grounding_declarative_tier():
    bundle = {
        "entries": [
            {
                "relative_path": "motadata/src/main/java/com/mindarray/api/MailServerConfiguration.java",
                "snippet": {
                    "text": (
                        "package com.mindarray.api;\n"
                        "public class MailServerConfiguration extends AbstractAPI {\n"
                        "  private static final String MAIL_SERVER_USERNAME = \"mail.server.username\";\n"
                        "}\n"
                    ),
                    "start_line": 1,
                    "end_line": 4,
                },
            }
        ]
    }
    out = detect_selected_method_grounding(
        bundle,
        "motadata/src/main/java/com/mindarray/api/MailServerConfiguration.java",
        ["beforeUpdate", "afterUpdate", "MailServerConfiguration"],
    )
    assert out.tier == DebugGroundingTier.DECLARATIVE
    assert out.missing_reason == "selected_file_snippet_declarative_only"


def test_detect_selected_method_grounding_partial_when_no_method_hint_match():
    bundle = {
        "entries": [
            {
                "relative_path": "motadata/src/main/java/com/mindarray/nms/SNMPTrapProcessor.java",
                "snippet": {
                    "text": "void handle() {\n  if (raw == null) { return; }\n}\n",
                    "start_line": 11,
                    "end_line": 13,
                },
            }
        ]
    }
    out = detect_selected_method_grounding(
        bundle,
        "motadata/src/main/java/com/mindarray/nms/SNMPTrapProcessor.java",
        ["parse", "dispatch"],
    )
    assert out.tier == DebugGroundingTier.PARTIAL
    assert out.missing_reason == "selected_file_snippets_missing_method_hints"


def test_detect_selected_method_grounding_traceable_tier():
    bundle = {
        "entries": [
            {
                "relative_path": "motadata/src/main/java/com/mindarray/nms/SNMPTrapProcessor.java",
                "snippet": {
                    "text": (
                        "void dispatchTraps() {\n"
                        "  for (Trap t : traps) {\n"
                        "    if (t == null) { continue; }\n"
                        "    parser.parse(t);\n"
                        "    handlers.add(t);\n"
                        "  }\n"
                        "  return;\n"
                        "}\n"
                    ),
                    "start_line": 41,
                    "end_line": 49,
                },
            }
        ]
    }
    out = detect_selected_method_grounding(
        bundle,
        "motadata/src/main/java/com/mindarray/nms/SNMPTrapProcessor.java",
        ["SNMPTrapProcessor", "parse", "dispatch"],
    )
    assert out.tier == DebugGroundingTier.TRACEABLE
    assert out.missing_reason is None
    assert out.control_flow_markers >= 2
