from __future__ import annotations

from runtime.mcoder_cli.answer_shaping import shape_prompt_summary


def _resp(steps: list[str], files: list[str] | None = None) -> dict:
    payload = {"plan_summary": {"steps": steps}}
    if files is not None:
        payload["context_bundle"] = {"files": [{"path": p} for p in files]}
    return payload


def _resp_with_graph(graph_traversal: dict) -> dict:
    return {"plan_summary": {"steps": []}, "graph_traversal": graph_traversal}


def test_base_api_class_prefers_direct_answer_and_hides_owner_boilerplate():
    shaped = shape_prompt_summary(
        "Which class is the base class for all APIs?",
        _resp(
            [
                "Direct answer (grounded): strongest API base-class signal in current evidence is `AbstractAPI` (limited declaration coverage in top snippets).",
                "Execution owner anchor (supporting context, not base-class answer): `APIServer` in `src/main/java/com/mindarray/api/APIServer.java`, method `start`.",
            ]
        ),
    )
    assert "AbstractAPI" in shaped["answer_1"]
    assert shaped["next_step"] == ""


def test_mail_server_configuration_shapes_explanation_without_blob():
    shaped = shape_prompt_summary(
        "How does mail server configuration work?",
        _resp(
            [
                "Primary implementation owner: `MailServerConfiguration` in `src/main/java/com/mindarray/api/MailServerConfiguration.java`, method `beforeUpdate`.",
                "How it works (grounded): `MailServerConfiguration`.`beforeUpdate` is the main execution path for this behavior. Method-window excerpt: @Override protected Future<JsonObject> beforeUpdate(...)",
            ]
        ),
    )
    assert "main execution path for this behavior" in shaped["answer_1"]
    assert "Method-window excerpt:" not in shaped["answer_1"]
    assert "Inspect `MailServerConfiguration.beforeUpdate`" in shaped["next_step"]


def test_config_store_organization_avoids_raw_visible_method_snippet():
    shaped = shape_prompt_summary(
        "How are config stores organized?",
        _resp(
            [
                "Primary implementation owner: `AbstractConfigStore` in `src/main/java/com/mindarray/store/AbstractConfigStore.java`, method `getItem`.",
                "Visible method-window evidence: public JsonObject getItem(long id) { return items.containsKey(id) ? items.get(id).copy() : null; }",
            ]
        ),
    )
    assert "AbstractConfigStore.getItem" in shaped["answer_1"]
    assert "Visible method-window evidence:" not in shaped["next_step"]
    assert "Inspect `AbstractConfigStore.getItem`" in shaped["next_step"]


def test_api_layer_architecture_starts_with_architecture_anchor():
    shaped = shape_prompt_summary(
        "Explain the API layer architecture.",
        _resp(
            [
                "Primary implementation owner: `APIServer` in `src/main/java/com/mindarray/api/APIServer.java`, method `start`.",
                "Visible method-window evidence: @Override public void start(Promise<Void> promise) throws Exception { ... }",
            ]
        ),
    )
    assert "APIServer.start" in shaped["answer_1"]
    assert "Inspect `APIServer.start`" in shaped["next_step"]


def test_notification_discovery_prefers_list_style_over_single_owner():
    shaped = shape_prompt_summary(
        "Find all classes that handle notifications.",
        _resp(
            [
                "Primary implementation owner: `NotificationEngine` in `src/main/java/com/mindarray/notification/NotificationEngine.java`, method `start`.",
                "Supporting context only (collaborators; not alternative owners): related paths include src/main/java/com/mindarray/notification/EmailNotification.java, src/main/java/com/mindarray/notification/SMSNotification.java.",
            ],
            files=[
                "src/main/java/com/mindarray/notification/NotificationEngine.java",
                "src/main/java/com/mindarray/notification/EmailNotification.java",
                "src/main/java/com/mindarray/notification/SMSNotification.java",
            ],
        ),
    )
    assert "relevant classes include" in shaped["answer_1"].lower()
    assert "`NotificationEngine`" in shaped["answer_1"]
    assert "`EmailNotification`" in shaped["answer_1"]
    assert "`SMSNotification`" in shaped["answer_1"]


def test_structural_query_ignores_authority_status_preamble():
    shaped = shape_prompt_summary(
        "Which class is the base class for all APIs?",
        _resp(
            [
                "Authority status: stale. Confidence: weak. Owner mapping may still resolve, but verification metadata is out of date. Treat the following as provisional; verify against the current codebase.",
                "Direct answer (grounded): strongest API base-class signal in current evidence is `AbstractAPI` (limited declaration coverage in top snippets).",
            ]
        ),
    )
    assert "AbstractAPI" in shaped["answer_1"]
    assert "Authority status:" not in shaped["answer_1"]


def test_discovery_fallback_suppresses_owner_only_next_step():
    shaped = shape_prompt_summary(
        "Find all classes that handle notifications.",
        _resp(
            [
                "Authority status: stale. Confidence: weak. Owner mapping may still resolve, but verification metadata is out of date.",
                "Primary implementation owner: `NotificationEngine` in `src/main/java/com/mindarray/notification/NotificationEngine.java`.",
            ],
            files=[],
        ),
    )
    assert "complete class list could not be confidently enumerated" in shaped["answer_1"]
    assert shaped["next_step"] == ""


def test_graph_explain_composer_avoids_single_anchor_collapse():
    shaped = shape_prompt_summary(
        "Explain the API layer architecture.",
        _resp_with_graph(
            {
                "flow_paths": [
                    "APIServer.start -> MailServerConfiguration.beforeUpdate",
                    "APIServer.start -> AbstractAPI.getItem",
                ],
                "inheritance_chain": ["MailServerConfiguration", "AbstractAPI"],
                "owners": ["APIServer", "AbstractAPI"],
                "collaborators": ["MailServerConfiguration"],
            }
        ),
    )
    assert "Entry point:" in shaped["answer_1"]
    assert "Core abstraction:" in shaped["answer_1"]
    assert "Concrete handlers/collaborators:" in shaped["answer_1"]
    assert "Persistence/event/store path:" in shaped["answer_1"]
    assert "Confidence limits:" in shaped["answer_1"]
    assert shaped["answer_1"] != "Based on deterministic graph evidence, flow: `APIServer.start`."


def test_graph_discovery_composer_separates_owner_and_collaborator():
    shaped = shape_prompt_summary(
        "Find all classes that handle notifications.",
        _resp_with_graph(
            {
                "owners": ["NotificationEngine"],
                "collaborators": ["EmailNotification", "SMSNotification"],
            }
        ),
    )
    assert "primary owners:" in shaped["answer_1"]
    assert "collaborators:" in shaped["answer_1"]


def test_graph_mail_explain_does_not_collapse_to_single_method():
    shaped = shape_prompt_summary(
        "How does mail server configuration work?",
        _resp_with_graph(
            {
                "flow_paths": ["MailServerConfiguration.beforeUpdate -> AbstractConfigStore.getItem"],
                "call_paths": ["MailServerConfiguration.beforeUpdate -> AbstractConfigStore.getItem"],
                "inheritance_chain": ["MailServerConfiguration", "AbstractAPI"],
                "owners": ["MailServerConfiguration"],
                "collaborators": ["AbstractConfigStore"],
            }
        ),
    )
    assert "Entry point:" in shaped["answer_1"]
    assert "MailServerConfiguration.beforeUpdate" in shaped["answer_1"]
    assert "AbstractConfigStore" in shaped["answer_1"]
    assert shaped["answer_1"] != "Based on deterministic graph evidence, flow: `MailServerConfiguration.beforeUpdate`."


def test_graph_config_store_chain_is_compressed_and_labeled():
    shaped = shape_prompt_summary(
        "How are config stores organized?",
        _resp_with_graph(
            {
                "flow_paths": [
                    "AbstractConfigStore.getItem -> AbstractConfigStore.getItemByValue -> AbstractConfigStore.getItems -> AbstractConfigStore.getItemsByMapMultiValueField -> AbstractConfigStore.getItemsByMapValueField -> AbstractConfigStore.getItemsByMultiValueField"
                ],
                "owners": ["AbstractConfigStore"],
                "collaborators": ["ObjectConfigStore", "ProtocolMapperConfigStore"],
            }
        ),
    )
    assert "Persistence/event/store path:" in shaped["answer_1"]
    assert "exposes lookup/helpers" in shaped["answer_1"]
    # avoid dumping long unlabeled raw chain
    assert "getItemByMapMultiValueField ->" not in shaped["answer_1"]

