#!/usr/bin/env python3
"""
PR-6 Slice 2: run retrieval against a real AIOps root (env) or bundled noisy fixture.

Usage (from repo root):
  PR6_AIOPS_ROOT=/path/to/Motadata python3 runtime/layer5/audit/pr6_real_repo_audit.py

If PR6_AIOPS_ROOT is unset or invalid, uses runtime/layer5/audit/fixture_noisy_aiops_workspace/
(after running noisy_workspace_fixture.write_noisy_aiops_workspace on that path once).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from runtime.layer5.audit.noisy_workspace_fixture import write_noisy_aiops_workspace
from runtime.layer5.index import build_file_index
from runtime.layer5.retrieval import LexicalRetrievalConfig, classify_file, retrieve_lexical
from runtime.layer5.workspace.identity import WorkspaceIdentity

_LAYER5 = Path(__file__).resolve().parents[1]
_FIX_MANDATORY = _LAYER5 / "retrieval" / "fixtures" / "pr6_mandatory_anchor_debug_queries.v1.json"
_FIX_AMBIG = _LAYER5 / "retrieval" / "fixtures" / "pr6_ambiguous_debug_queries.v1.json"
_REPORT = Path(__file__).resolve().parent / "pr6_real_repo_run_report.md"
_BUNDLED_ROOT = Path(__file__).resolve().parent / "fixture_noisy_aiops_workspace"


def _identity(root: Path) -> WorkspaceIdentity:
    root_s = str(root.resolve())
    return WorkspaceIdentity(
        canonical_root=root_s,
        identity_hash=WorkspaceIdentity.compute_identity_hash(root_s),
        original_input=root_s,
        path_type="posix",
        is_git_repo=False,
    )


def _noise_ratio_top5(paths: List[str]) -> float:
    if not paths:
        return 0.0
    top = paths[:5]
    n = sum(
        1
        for p in top
        if classify_file(p).file_class
        in {"tests", "logs", "vendor_static", "generated_metrics_data"}
    )
    return n / max(1, len(top))


def _first_anchor_rank(paths: List[str], anchors: List[str]) -> Optional[int]:
    a = set(anchors)
    for i, p in enumerate(paths):
        if p in a:
            return i + 1
    return None


def _load_queries() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for label, path in (("mandatory", _FIX_MANDATORY), ("ambiguous", _FIX_AMBIG)):
        data = json.loads(path.read_text(encoding="utf-8"))
        for f in data["fixtures"]:
            entry = dict(f)
            entry["_fixture_group"] = label
            out.append(entry)
    return out


def _resolve_workspace_root() -> Tuple[Path, str]:
    env = (os.environ.get("PR6_AIOPS_ROOT") or os.environ.get("MOTADATA_AIOPS_REPO_ROOT") or "").strip()
    if env:
        p = Path(env).resolve()
        if p.is_dir():
            return p, f"environment `PR6_AIOPS_ROOT` / `MOTADATA_AIOPS_REPO_ROOT` → `{p}`"
    _BUNDLED_ROOT.parent.mkdir(parents=True, exist_ok=True)
    write_noisy_aiops_workspace(_BUNDLED_ROOT)
    return _BUNDLED_ROOT.resolve(), (
        f"bundled noisy fixture (no real AIOps checkout found): `{_BUNDLED_ROOT}` "
        "(set `PR6_AIOPS_ROOT` to evaluate a real tree)"
    )


def _diagnostic_note(top_hit_path: str, anchors: List[str], diag: Optional[Dict[str, int]]) -> str:
    if top_hit_path in anchors:
        return "top-1 is an expected anchor."
    if not diag:
        return "no diagnostics on hit (unexpected)."
    mb = diag.get("module_bias", 0)
    inv = diag.get("symbol_inventory_boost", 0)
    ct = diag.get("content", 0)
    pp = diag.get("path_prior", 0)
    parts = []
    if mb > inv and mb > ct:
        parts.append("module_bias >= symbol_inventory and >= content — path token overlap may dominate")
    if inv < pp:
        parts.append("path_prior exceeds symbol_inventory on this file — class policy prior strong")
    if not parts:
        parts.append("inspect content vs symbol_inventory vs lexical path overlap")
    return "; ".join(parts)


def main() -> None:
    root, repo_note = _resolve_workspace_root()
    ident = _identity(root)
    idx = build_file_index(ident)
    cfg = LexicalRetrievalConfig(include_score_diagnostics=True)
    queries = _load_queries()

    top1_hits = 0
    top3_hits = 0
    ranks: List[int] = []
    noise_ratios: List[float] = []
    failures: List[str] = []

    lines: List[str] = []
    lines.append("# PR-6 real-repo (or bundled) retrieval audit\n")
    lines.append("## Workspace source\n")
    lines.append(f"- {repo_note}\n")
    lines.append(f"- **Indexed files:** {len(idx.files)}\n")
    lines.append(f"- **Queries run:** {len(queries)}\n")
    lines.append("\n## Per-query results\n")

    for q in queries:
        qid = str(q["id"])
        group = str(q.get("_fixture_group", ""))
        raw = str(q["query"])
        anchors = [str(x) for x in q["expected_anchor_paths"]]
        top_k = int(q["required_top_k"])
        result = retrieve_lexical(idx, raw, top_k=top_k, config=cfg)
        paths = [h.relative_path for h in result.hits]
        scores = [h.score for h in result.hits]
        top1 = paths[0] if paths else ""
        fr = _first_anchor_rank(paths, anchors)
        nr = _noise_ratio_top5(paths)
        noise_ratios.append(nr)

        if top1 in anchors:
            top1_hits += 1
        if any(p in set(anchors) for p in paths[:3]):
            top3_hits += 1
        if fr is not None:
            ranks.append(fr)
        else:
            failures.append(qid)

        lines.append(f"### `{qid}` ({group})\n")
        lines.append(f"- **query:** {raw}\n")
        lines.append(f"- **first relevant rank:** {fr}\n")
        lines.append(f"- **top-3 anchor hit:** {'yes' if any(p in set(anchors) for p in paths[:3]) else 'no'}\n")
        lines.append(f"- **noise dominance ratio (top-5):** {nr:.2f}\n")
        lines.append("- **top-5 (path | score):**\n")
        for i, (p, s) in enumerate(zip(paths[:5], scores[:5])):
            mark = " ✓" if p in anchors else ""
            lines.append(f"  {i + 1}. `{p}` — {s}{mark}\n")
            if i == 0 and result.hits:
                d = result.hits[0].diagnostics
                lines.append(
                    f"  - **diagnostics (top-1):** {d}\n"
                    if d
                    else "  - **diagnostics:** n/a\n"
                )
                lines.append(f"  - **note:** {_diagnostic_note(top1, anchors, d)}\n")
        lines.append("\n")

    nq = len(queries)
    mean_rank = sum(ranks) / max(1, len(ranks))
    mean_noise = sum(noise_ratios) / max(1, len(noise_ratios))

    lines.append("## Aggregate metrics\n")
    lines.append(f"- **top-1 accuracy:** {top1_hits}/{nq} = {top1_hits / max(1, nq):.2f}\n")
    lines.append(f"- **top-3 anchor hit rate:** {top3_hits}/{nq} = {top3_hits / max(1, nq):.2f}\n")
    lines.append(f"- **mean first relevant rank:** {mean_rank:.2f}\n")
    lines.append(f"- **mean noise dominance ratio (top-5):** {mean_noise:.2f}\n")

    lines.append("\n## Failure analysis\n")
    if not failures:
        lines.append("- No queries missed all anchors in top-k (first relevant rank defined for all).\n")
    else:
        for qid in failures:
            lines.append(f"- **{qid}:** no anchor in top-k (inspect diagnostics on top rows).\n")

    lines.append("\n## Caveat validation\n")
    lines.append(
        "- **Package-private methods:** extractor extended (regex); see unit test "
        "`test_package_private_methods_in_symbol_inventory`.\n"
    )
    lines.append(
        "- **Module/path bias:** `RetrievalHit.diagnostics` exposes `module_bias` vs "
        "`symbol_inventory_boost` vs `content` for top-1 rows above.\n"
    )

    lines.append("\n## Adjustments made in this slice\n")
    lines.append(
        "- Diagnostics-only (`include_score_diagnostics`) + package-private regex extension; "
        "**no retrieval weight tuning** in this pass (failures classified first).\n"
    )

    lines.append("\n## Verdict\n")
    if top1_hits / max(1, nq) >= 0.55 and top3_hits / max(1, nq) >= 0.85 and mean_noise <= 0.45:
        lines.append("**READY** for next slice (subject to real-checkout confirmation).\n")
    else:
        lines.append("**NOT READY** — review failure analysis and real `PR6_AIOPS_ROOT` run.\n")

    _REPORT.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {_REPORT}")


if __name__ == "__main__":
    main()
