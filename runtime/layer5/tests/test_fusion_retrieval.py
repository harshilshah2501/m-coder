"""Fusion layer: precedence, caps, deterministic reorder, roles."""

from __future__ import annotations

import tempfile
from pathlib import Path

from runtime.layer5.authority.registry_loader import load_registry
from runtime.layer5.evidence import build_evidence_bundle
from runtime.layer5.index import build_file_index
from runtime.layer5.retrieval import LexicalRetrievalConfig, retrieve_lexical
from runtime.layer5.retrieval.effective_intent import merge_effective_intent
from runtime.layer5.retrieval.fusion import FusionConfig, fuse_and_filter, hard_filter_only
from runtime.layer5.retrieval.roles import DISTRACTOR_RISK, PRIMARY_OWNER_CANDIDATE, SUPPORTING_CONTEXT
from runtime.layer5.workspace.identity import WorkspaceIdentity


def _touch(p: Path, text: str = "x") -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _idx_for(root: Path):
    ident = WorkspaceIdentity(
        canonical_root=str(root.resolve()),
        identity_hash=WorkspaceIdentity.compute_identity_hash(str(root.resolve())),
        original_input=str(root.resolve()),
        path_type="posix",
        is_git_repo=False,
    )
    return build_file_index(ident)


def test_fusion_deterministic_and_reorders():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    _touch(
        root / "src/main/java/com/mindarray/aiops/correlation/X.java",
        "public class X { void correlationEngine() {} }\n",
    )
    _touch(
        root / "src/main/java/com/mindarray/aiops/api/Constants.java",
        "public class Constants { static String correlation = \"x\"; }\n",
    )
    idx = _idx_for(root)
    q = "correlation engine"
    r = retrieve_lexical(idx, q, 4, LexicalRetrievalConfig())
    reg = load_registry(Path(__file__).resolve().parents[1] / "authority" / "product_authority_registry.yaml")
    eff = merge_effective_intent("general", q)
    fused, diag, roles = fuse_and_filter(
        r,
        effective_intent=eff,
        registry=reg,
        code_index_adapter=None,
        selected_file=None,
        fusion_config=FusionConfig(),
        index=idx,
        authority_resolution=None,
    )
    assert len(fused.hits) == len(r.hits)
    # Two runs identical
    fused2, diag2, roles2 = fuse_and_filter(
        r,
        effective_intent=eff,
        registry=reg,
        code_index_adapter=None,
        selected_file=None,
        fusion_config=FusionConfig(),
        index=idx,
        authority_resolution=None,
    )
    assert [h.relative_path for h in fused.hits] == [h.relative_path for h in fused2.hits]
    assert [h.score for h in fused.hits] == [h.score for h in fused2.hits]
    assert "effective_intent" in diag or "per_path" in diag
    assert roles
    tmp.cleanup()


def test_fusion_disabled_passthrough():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    _touch(root / "a.java", "class A {}\n")
    idx = _idx_for(root)
    r = retrieve_lexical(idx, "hello", 1, LexicalRetrievalConfig())
    reg = load_registry(Path(__file__).resolve().parents[1] / "authority" / "product_authority_registry.yaml")
    eff = merge_effective_intent("general", "hello")
    fused, diag, _roles = fuse_and_filter(
        r,
        effective_intent=eff,
        registry=reg,
        fusion_config=FusionConfig(enable_fusion=False),
        index=idx,
    )
    assert fused.hits == r.hits
    assert diag.get("skipped") is True
    tmp.cleanup()


def test_evidence_bundle_uses_fusion_scores():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    _touch(
        root / "src/main/java/com/mindarray/aiops/correlation/Z.java",
        "public class Z { void correlation() {} }\n",
    )
    idx = _idx_for(root)
    q = "correlation"
    r = retrieve_lexical(idx, q, 2, LexicalRetrievalConfig())
    reg = load_registry(Path(__file__).resolve().parents[1] / "authority" / "product_authority_registry.yaml")
    eff = merge_effective_intent("general", q)
    fused, _, roles = fuse_and_filter(
        r,
        effective_intent=eff,
        registry=reg,
        code_index_adapter=None,
        fusion_config=FusionConfig(),
        index=idx,
        authority_resolution=None,
    )
    roles_map = {p: ra.role for p, ra in roles.items()}
    from runtime.layer5.retrieval.fusion import fusion_authority_note

    b = build_evidence_bundle(
        fused,
        idx,
        role_by_path=roles_map,
        authority_note=fusion_authority_note(),
    )
    assert b.entries[0].retrieval_score == fused.hits[0].score
    assert b.entries[0].retrieval_role in (PRIMARY_OWNER_CANDIDATE, DISTRACTOR_RISK, SUPPORTING_CONTEXT)
    tmp.cleanup()


def test_merge_effective_intent_debug_task():
    e = merge_effective_intent("EXPLAIN_DEBUG", "why error")
    assert e.primary_mode == "DEBUG"


def test_merge_effective_intent_general_code_query():
    e = merge_effective_intent("general", "Where is FooBar implemented")
    assert e.primary_mode in ("ASK", "CODE", "DEBUG", "PLAN")


def test_merge_effective_intent_explicit_code_task():
    e = merge_effective_intent("CODE", "generic question text")
    assert e.primary_mode == "CODE"


def test_fusion_authority_owner_promoted_into_top3():
    """v2.1.2: Stage B must not drop authority primary_owner below top-3 when present in fused list."""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    owner = "src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java"
    _touch(root / owner, "public class AlertCorrelationEngine { void correlation() {} }\n")
    for i in range(12):
        _touch(
            root / f"src/main/java/com/mindarray/notification/NotificationHeavy{i}.java",
            "notification " * 50 + "correlation correlation\n",
        )
    idx = _idx_for(root)
    q = "correlation"
    r = retrieve_lexical(
        idx,
        q,
        8,
        LexicalRetrievalConfig(enable_stage_a_v2=True),
        authority_resolution={"primary_owner": {"file": owner}},
    )
    reg = load_registry(Path(__file__).resolve().parents[1] / "authority" / "product_authority_registry.yaml")
    eff = merge_effective_intent("general", q)
    fused, diag, _roles = fuse_and_filter(
        r,
        effective_intent=eff,
        registry=reg,
        code_index_adapter=None,
        selected_file=None,
        fusion_config=FusionConfig(),
        index=idx,
        authority_resolution={"primary_owner": {"file": owner}},
    )
    top3 = [h.relative_path for h in fused.hits[:3]]
    assert owner in top3
    if diag.get("authority_owner_top3_promotion", {}).get("applied"):
        assert diag["authority_owner_top3_promotion"].get("swap_into_slot") in (0, 1, 2)
    tmp.cleanup()


def test_fusion_hard_caps_drop_surplus_generic_paths():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    _touch(
        root / "src/main/java/com/mindarray/aiops/correlation/Owner.java",
        "public class Owner { void correlation() {} }\n",
    )
    # Generic/support-style paths
    _touch(root / "src/main/java/com/mindarray/api/APIServer.java", "class APIServer {}\n")
    _touch(root / "src/main/java/com/mindarray/db/ConfigDBServiceImpl.java", "class ConfigDBServiceImpl {}\n")
    _touch(root / "src/main/java/com/mindarray/cache/PolicyCacheServiceImpl.java", "class PolicyCacheServiceImpl {}\n")
    _touch(root / "src/main/java/com/mindarray/notification/Notification.java", "class Notification {}\n")
    _touch(root / "src/main/java/com/mindarray/manager/MotadataAppManager.java", "class MotadataAppManager {}\n")

    idx = _idx_for(root)
    q = "correlation"
    r = retrieve_lexical(idx, q, 8, LexicalRetrievalConfig())
    reg = load_registry(Path(__file__).resolve().parents[1] / "authority" / "product_authority_registry.yaml")
    eff = merge_effective_intent("general", q)
    fused, diag, _roles = fuse_and_filter(
        r,
        effective_intent=eff,
        registry=reg,
        code_index_adapter=None,
        selected_file=None,
        fusion_config=FusionConfig(max_generic_infra_paths=2, max_distractor_paths=1),
        index=idx,
        authority_resolution=None,
    )

    kept_paths = [h.relative_path for h in fused.hits]
    generic_like = sum(
        1
        for p in kept_paths
        if any(t in p.lower() for t in ("/api/", "/db/", "/cache/", "/notification/", "/manager/"))
    )
    assert generic_like <= 2
    assert "hard_caps" in diag
    assert isinstance((diag.get("hard_caps") or {}).get("dropped"), int)
    tmp.cleanup()


def test_hard_filter_only_applies_caps_without_registry():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    _touch(
        root / "src/main/java/com/mindarray/aiops/correlation/Owner.java",
        "public class Owner { void correlation() {} }\n",
    )
    _touch(root / "src/main/java/com/mindarray/api/APIServer.java", "class APIServer {}\n")
    _touch(root / "src/main/java/com/mindarray/db/ConfigDBServiceImpl.java", "class ConfigDBServiceImpl {}\n")
    _touch(root / "src/main/java/com/mindarray/cache/PolicyCacheServiceImpl.java", "class PolicyCacheServiceImpl {}\n")
    _touch(root / "src/main/java/com/mindarray/notification/Notification.java", "class Notification {}\n")
    _touch(root / "src/main/java/com/mindarray/manager/MotadataAppManager.java", "class MotadataAppManager {}\n")

    idx = _idx_for(root)
    q = "correlation"
    r = retrieve_lexical(idx, q, 8, LexicalRetrievalConfig())
    filtered, diag, roles = hard_filter_only(
        r,
        fusion_config=FusionConfig(max_generic_infra_paths=2, max_distractor_paths=1, min_paths_after_caps=3),
        owner_path=None,
        selected_file=None,
        collaborator_paths=set(),
    )
    kept_paths = [h.relative_path for h in filtered.hits]
    generic_like = sum(
        1
        for p in kept_paths
        if any(t in p.lower() for t in ("/api/", "/db/", "/cache/", "/notification/", "/manager/"))
    )
    assert generic_like <= 2
    assert diag.get("skipped_authority_fusion") is True
    assert "hard_caps" in diag
    assert roles
    tmp.cleanup()
