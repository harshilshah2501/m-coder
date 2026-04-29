from __future__ import annotations

import json

import pytest

from runtime.context.contracts import (
    ContextBundle,
    ContextBundleLimits,
    ContextBundleProvenance,
    ContextItem,
)


def _bundle(items: list[ContextItem]) -> ContextBundle:
    return ContextBundle(
        task_id="t",
        revision="r",
        created_at_utc="2026-01-01T00:00:00Z",
        items=items,
        limits=ContextBundleLimits(max_files=10, max_bytes=100_000, truncated=False),
        provenance=ContextBundleProvenance(
            root_path="/tmp",
            selectors=["direct"],
            requested_files=[],
            symbol_hints=[],
        ),
    )
from runtime.ask_service.bounded_ask_narrator import (
    _build_symbol_allowlist,
    _validate_governed_prose,
    governed_ask_narrator_enabled,
    try_governed_ask_narration,
)


def test_governed_narrator_disabled_by_default():
    assert governed_ask_narrator_enabled() is False


def test_validate_accepts_allowlisted_backticks():
    allow = _build_symbol_allowlist(
        {
            "primary_owner": {"class": "APIServer", "method": "start"},
            "anchor_method": "APIServer.start",
            "typed_nodes": {
                "handlers": [{"class": "AlarmAPI", "method": "beforeUpdate"}],
            },
        },
        ["Owner `APIServer` method `start`."],
        _bundle(
            [
                ContextItem(
                    path="src/APIServer.java",
                    content="class APIServer {}",
                    byte_size=len(b"class APIServer {}"),
                    selection_reason="x",
                ),
            ]
        ),
    )
    paras = [
        "The API layer starts at `APIServer.start`, which routes traffic.",
        "Handlers include `AlarmAPI.beforeUpdate` for request work.",
        "The full chain is not fully visible in this snapshot.",
    ]
    ok, issues = _validate_governed_prose(
        paras,
        allowlist=allow,
        anchor_method="APIServer.start",
    )
    assert ok
    assert not issues


def test_validate_rejects_ungrounded_backtick():
    allow = {"APIServer", "APIServer.start"}
    ok, issues = _validate_governed_prose(
        [
            "Something uses `MadeUpClass` and `APIServer.start`.",
        ],
        allowlist=allow,
        anchor_method="APIServer.start",
    )
    assert not ok
    assert any("ungrounded" in i for i in issues)


def test_try_governed_returns_payload_when_http_ok(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MCODER_GOVERNED_ASK_NARRATOR", "1")

    body = "class Foo { void bar() {} }"
    bundle = _bundle(
        [
            ContextItem(path="src/Foo.java", content=body, byte_size=len(body.encode("utf-8")), selection_reason="r"),
        ]
    )
    rc = {
        "primary_owner": {"class": "Foo", "method": "bar"},
        "anchor_method": "Foo.bar",
        "typed_nodes": {"handlers": [{"class": "Baz", "method": "x"}]},
        "evidence_sources": [{"inferred_class": "Foo"}],
    }
    meta = {"evidence_quality": "STRONG", "reasoning_context": rc}

    fake_body = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "paragraphs": [
                                "The flow centers on `Foo.bar`, which handles work.",
                                "`Baz` participates as a handler.",
                                "Limits: snapshot only.",
                            ],
                            "evidence_limit": "Grounded to evidence above.",
                        }
                    )
                }
            }
        ]
    }

    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(fake_body).encode("utf-8")

    def _fake_urlopen(req, timeout=0):  # noqa: ARG001
        return _Resp()

    monkeypatch.setattr(
        "runtime.ask_service.bounded_ask_narrator.urllib.request.urlopen",
        _fake_urlopen,
    )

    out = try_governed_ask_narration(
        query="How does Foo work?",
        bundle=bundle,
        plan_steps=["Primary owner `Foo`."],
        metadata=meta,
        request_id="r1",
        trace_id="t1",
    )
    assert out is not None
    assert out.get("narration_source") == "governed_vllm"
    assert out.get("shape") == "governed_vllm_contract"
    assert len(out.get("paragraphs") or []) >= 1


def test_try_governed_returns_none_when_http_fails(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MCODER_GOVERNED_ASK_NARRATOR", "1")
    monkeypatch.setattr(
        "runtime.ask_service.bounded_ask_narrator.urllib.request.urlopen",
        lambda *a, **k: (_ for _ in ()).throw(OSError("nop")),
    )
    bundle = _bundle([ContextItem(path="src/Foo.java", content="x", byte_size=1, selection_reason="r")])
    meta = {
        "evidence_quality": "STRONG",
        "reasoning_context": {
            "primary_owner": {"class": "Foo", "method": "bar"},
            "anchor_method": "Foo.bar",
            "typed_nodes": {"handlers": [{"class": "Baz", "method": "z"}]},
        },
    }
    assert (
        try_governed_ask_narration(
            query="q",
            bundle=bundle,
            plan_steps=["step"],
            metadata=meta,
        )
        is None
    )
