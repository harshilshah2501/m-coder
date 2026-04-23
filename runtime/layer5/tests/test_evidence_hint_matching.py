"""Hint matching for EXPLAIN_DEBUG selected-file body checks (camelCase Java)."""

from runtime.context_layer_service.evidence_api import _hint_matches_selected_snippet, _selected_method_body_present


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
