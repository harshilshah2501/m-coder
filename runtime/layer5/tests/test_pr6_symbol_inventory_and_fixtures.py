from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List

from runtime.layer5.audit.noisy_workspace_fixture import write_noisy_aiops_workspace
from runtime.layer5.index import (
    build_file_index,
    build_symbol_inventory,
    inventory_token_lookup,
    resolve_symbol_lookup_for_index,
)
from runtime.layer5.retrieval import LexicalRetrievalConfig, classify_file, retrieve_lexical
from runtime.layer5.workspace.identity import WorkspaceIdentity


def _touch(path: Path, text: str = "", mtime_ns: int = 1_000_000_000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    os.utime(path, ns=(mtime_ns, mtime_ns))


def _identity_for(root: Path) -> WorkspaceIdentity:
    root_s = str(root.resolve())
    return WorkspaceIdentity(
        canonical_root=root_s,
        identity_hash=WorkspaceIdentity.compute_identity_hash(root_s),
        original_input=root_s,
        path_type="posix",
        is_git_repo=False,
    )


def _load_pr6_fixtures() -> List[Dict[str, object]]:
    p = (
        Path(__file__).resolve().parents[1]
        / "retrieval"
        / "fixtures"
        / "pr6_mandatory_anchor_debug_queries.v1.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    return list(data["fixtures"])


def _load_pr6_ambiguous_fixtures() -> List[Dict[str, object]]:
    p = (
        Path(__file__).resolve().parents[1]
        / "retrieval"
        / "fixtures"
        / "pr6_ambiguous_debug_queries.v1.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    return list(data["fixtures"])


def _load_pr6_symbol_fixture() -> List[Dict[str, object]]:
    p = (
        Path(__file__).resolve().parents[1]
        / "index"
        / "fixtures"
        / "pr6_mandatory_symbol_inventory.v1.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    return list(data["entries"])


def _setup_pr6_tree(root: Path) -> None:
    """Same layout as ``write_noisy_aiops_workspace`` (motadata-prefixed PR-6 tree)."""
    write_noisy_aiops_workspace(root)


def _first_relevant_rank(hits: List[str], anchors: List[str]) -> int | None:
    anchor_set = set(anchors)
    for i, p in enumerate(hits):
        if p in anchor_set:
            return i + 1
    return None


def test_pr6_symbol_inventory_is_deterministic_and_contains_expected_fields():
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        _setup_pr6_tree(root)
        idx = build_file_index(_identity_for(root))

        inv_a = build_symbol_inventory(idx)
        inv_b = build_symbol_inventory(idx)
        assert inv_a.canonical_json() == inv_b.canonical_json()
        assert inv_a.schema_version == "layer5.symbol_inventory.v1"
        assert len(inv_a.entries) >= 8

        sample = inv_a.entries[0]
        assert sample.symbol_name
        assert sample.relative_path.startswith("motadata/src/main/java/com/mindarray/aiops/")
        assert isinstance(sample.package, str)
        assert isinstance(sample.module, str)
        assert isinstance(sample.normalized_tokens, tuple)
        assert all(isinstance(t, str) for t in sample.normalized_tokens)

        frozen_entries = _load_pr6_symbol_fixture()
        generated = {(e.symbol_name, e.relative_path, e.module): set(e.normalized_tokens) for e in inv_a.entries}
        for expected in frozen_entries:
            key = (str(expected["symbol_name"]), str(expected["relative_path"]), str(expected["module"]))
            assert key in generated, f"missing mandatory symbol: {key}"
            for tok in expected["normalized_tokens"]:
                assert str(tok) in generated[key], f"missing token '{tok}' for symbol {key}"


def test_pr6_fixtures_meet_anchor_and_dominance_requirements():
    fixtures = _load_pr6_fixtures()
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        _setup_pr6_tree(root)
        idx = build_file_index(_identity_for(root))
        cfg = LexicalRetrievalConfig()

        for fixture in fixtures:
            query = str(fixture["query"])
            anchors = [str(x) for x in fixture["expected_anchor_paths"]]
            top_k = int(fixture["required_top_k"])
            min_top3 = int(fixture["min_anchor_hits_top_3"])
            max_noise = float(fixture["max_noise_ratio_top_5"])

            result = retrieve_lexical(idx, query, top_k=top_k, config=cfg)
            top_paths = [h.relative_path for h in result.hits]
            top1 = top_paths[0] if top_paths else ""
            top3 = top_paths[:3]
            anchor_hits_top3 = sum(1 for p in top3 if p in set(anchors))
            first_rank = _first_relevant_rank(top_paths, anchors)

            top5_classes = [classify_file(p).file_class for p in top_paths[:5]]
            top5_noise = sum(1 for c in top5_classes if c in {"tests", "logs", "vendor_static", "generated_metrics_data"})
            noise_ratio = (top5_noise / max(1, len(top_paths[:5])))
            code_ratio = 1.0 - noise_ratio

            assert first_rank is not None, f"{fixture['id']}: no relevant anchor in top-k"
            assert anchor_hits_top3 >= min_top3, f"{fixture['id']}: insufficient top-3 anchor coverage"
            assert noise_ratio <= max_noise, f"{fixture['id']}: noise dominance too high"
            assert code_ratio >= 0.6, f"{fixture['id']}: code dominance too low"
            assert top1 in anchors or first_rank <= 3, f"{fixture['id']}: weak top ranking: top1={top1}"


def test_package_private_methods_in_symbol_inventory():
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        rel = "motadata/src/main/java/com/mindarray/aiops/testpkg/PkgOnly.java"
        _touch(
            root / rel,
            "package com.mindarray.aiops.testpkg;\n"
            "class PkgOnly {\n"
            "  void packagePrivateFoo() {}\n"
            "  void packagePrivateBar() {}\n"
            "}\n",
        )
        idx = build_file_index(_identity_for(root))
        inv = build_symbol_inventory(idx)
        names = {e.symbol_name for e in inv.entries if e.relative_path == rel}
        assert "packagePrivateFoo" in names
        assert "packagePrivateBar" in names


def test_ambiguous_fixtures_against_noisy_workspace():
    fixtures = _load_pr6_ambiguous_fixtures()
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        write_noisy_aiops_workspace(root)
        idx = build_file_index(_identity_for(root))
        cfg = LexicalRetrievalConfig()
        for fixture in fixtures:
            result = retrieve_lexical(
                idx,
                str(fixture["query"]),
                top_k=int(fixture["required_top_k"]),
                config=cfg,
            )
            anchors = set(str(x) for x in fixture["expected_anchor_paths"])
            top3 = [h.relative_path for h in result.hits[:3]]
            assert any(p in anchors for p in top3), f"{fixture['id']}: no anchor in top-3"


def test_retrieval_hit_includes_diagnostics_when_enabled():
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        _setup_pr6_tree(root)
        idx = build_file_index(_identity_for(root))
        r = retrieve_lexical(
            idx,
            "alert correlation engine",
            top_k=2,
            config=LexicalRetrievalConfig(include_score_diagnostics=True),
        )
        assert r.hits[0].diagnostics is not None
        assert "symbol_inventory_boost" in (r.hits[0].diagnostics or {})


def test_inventory_token_lookup_excludes_package_shards():
    """Package segments must not be copied into per-file lookup sets (avoids package-wide flattening)."""
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        _setup_pr6_tree(root)
        idx = build_file_index(_identity_for(root))
        inv = build_symbol_inventory(idx)
        lookup = inventory_token_lookup(inv)
        for _path, toks in lookup.items():
            assert "mindarray" not in toks
            assert "com" not in toks
            assert "aiops" not in toks


def test_resolve_symbol_lookup_for_index_is_cached_per_fingerprint():
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        _setup_pr6_tree(root)
        idx = build_file_index(_identity_for(root))
        a = resolve_symbol_lookup_for_index(idx)
        b = resolve_symbol_lookup_for_index(idx)
        assert a is b


def test_query_prefers_class_specific_file_over_same_package_sibling():
    """Symbol tokens must not uniformly boost every file sharing a package."""
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        _touch(
            root / "motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java",
            (
                "package com.mindarray.aiops.correlation;\n"
                "public class AlertCorrelationEngine {\n"
                "  public void correlateDuplicateIncidents() {}\n"
                "}\n"
            ),
        )
        _touch(
            root / "motadata/src/main/java/com/mindarray/aiops/correlation/CorrelationUtils.java",
            (
                "package com.mindarray.aiops.correlation;\n"
                "public class CorrelationUtils {\n"
                "  public void helper() {}\n"
                "}\n"
            ),
        )
        idx = build_file_index(_identity_for(root))
        r = retrieve_lexical(
            idx,
            "Debug AlertCorrelationEngine correlate duplicate incidents",
            top_k=2,
            config=LexicalRetrievalConfig(),
        )
        assert r.hits[0].relative_path.endswith("AlertCorrelationEngine.java")
