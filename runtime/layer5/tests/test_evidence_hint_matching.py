"""Hint matching for EXPLAIN_DEBUG selected-file body checks (camelCase Java)."""

from runtime.context_layer_service.evidence_api import (
    _java_snippet_has_implementation_signals,
    _selected_method_body_present,
    _hint_matches_selected_snippet,
)


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
                    "text": "void dispatchTraps() { }\nvoid parseTrap() { }\n",
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
    body = "{\n" + ("  //x\n" * 20) + "  a(b);\n}\n"
    assert len(body) >= 80
    assert "{" in body
    assert _java_snippet_has_implementation_signals(body)


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
