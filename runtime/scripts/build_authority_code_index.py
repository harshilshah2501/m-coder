#!/usr/bin/env python3
"""
Build and persist authority code index with progress reporting.

Usage:
  PYTHONPATH=. python3 runtime/scripts/build_authority_code_index.py \
    --workspace-root "/home/harshil/Projects/Motadata"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from runtime.layer5.authority.code_index_builder import CodeIndexBuilder
from runtime.layer5.authority.code_index_models import (
    CallConfidence,
    CallEdge,
    ClassRecord,
    CodeIndex,
    EntryPointRecord,
    EntryPointType,
    FileRecord,
)


def _now() -> float:
    return time.perf_counter()


def _is_test_file(relative_path: str) -> bool:
    p = relative_path.lower()
    stem = Path(relative_path).stem.lower()
    return (
        "/test/" in p
        or "/tests/" in p
        or p.endswith("test.java")
        or p.endswith("tests.java")
        or "test" in stem
    )


def _discover_source_dirs(workspace_root: Path, explicit: Iterable[str] | None) -> List[str]:
    if explicit:
        out = [str(x).strip() for x in explicit if str(x).strip()]
        if out:
            return out
    candidates = [
        "src/main/java",
        "src",
        "motadata/src/main/java",
        "app/src/main/java",
        "core/src/main/java",
    ]
    found = [c for c in candidates if (workspace_root / c).exists()]
    return found or ["."]


def _meta_path_for_index(out_path: Path) -> Path:
    return out_path.with_suffix(out_path.suffix + ".meta.json")


def _resolve_out_path(workspace_root: Path, out: str | None) -> Path:
    if out:
        return Path(out).expanduser().resolve()
    key = hashlib.sha256(str(workspace_root).lower().encode("utf-8")).hexdigest()[:12]
    return (Path("runtime/.cache") / f"authority_code_index.{key}.json").resolve()


class ProgressBar:
    """Lightweight terminal progress bar with elapsed time."""

    def __init__(self, total: int, *, width: int = 28, enabled: bool = True, label: str = "progress") -> None:
        self.total = max(1, int(total))
        self.width = max(10, int(width))
        self.enabled = bool(enabled)
        self.label = label
        self.start = _now()
        self._last_render = 0.0

    def update(self, current: int, *, extra: str = "") -> None:
        if not self.enabled:
            return
        now = _now()
        # Throttle repaint to keep logs readable.
        if current < self.total and (now - self._last_render) < 0.08:
            return
        self._last_render = now
        cur = max(0, min(current, self.total))
        ratio = cur / self.total
        filled = int(self.width * ratio)
        bar = "#" * filled + "-" * (self.width - filled)
        elapsed = now - self.start
        eta = (elapsed / ratio - elapsed) if ratio > 0 else 0.0
        line = (
            f"\r{self.label}: [{bar}] {cur}/{self.total} ({ratio * 100:5.1f}%) "
            f"elapsed={elapsed:6.1f}s eta={eta:6.1f}s"
        )
        if extra:
            line += f" | {extra}"
        print(line, end="", flush=True)

    def finish(self, *, extra: str = "") -> None:
        if not self.enabled:
            return
        self.update(self.total, extra=extra)
        print("", flush=True)


def _can_incremental(
    *,
    out_path: Path,
    workspace_root: Path,
    source_dirs: List[str],
    include_tests: bool,
    max_files: int,
) -> Tuple[bool, str]:
    meta_path = _meta_path_for_index(out_path)
    if not out_path.exists() or not meta_path.exists():
        return (False, "cache artifacts missing")
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return (False, "meta unreadable")
    if not isinstance(meta, dict):
        return (False, "meta malformed")

    if str(meta.get("workspace_root", "")) != str(workspace_root):
        return (False, "workspace_root changed")
    if list(meta.get("source_dirs", [])) != list(source_dirs):
        return (False, "source_dirs changed")
    if bool(meta.get("include_tests", False)) != bool(include_tests):
        return (False, "include_tests changed")
    if int(meta.get("max_files", 0)) != int(max_files):
        return (False, "max_files changed")
    return (True, "cache + meta compatible")


def _file_sig(path: Path) -> Dict[str, int]:
    st = path.stat()
    return {"mtime_ns": int(st.st_mtime_ns), "size": int(st.st_size)}


def _discover_java_files(
    workspace_root: Path,
    source_dirs: List[str],
    include_tests: bool,
    max_files: int,
) -> Tuple[List[Path], Dict[str, Path], Dict[str, Dict[str, int]]]:
    files: List[Path] = []
    by_rel: Dict[str, Path] = {}
    sigs: Dict[str, Dict[str, int]] = {}
    for src in source_dirs:
        root = workspace_root / src
        if not root.exists():
            print(f"      - skip missing source dir: {src}")
            continue
        for p in sorted(root.rglob("*.java")):
            rel = str(p.relative_to(workspace_root)).replace("\\", "/")
            if not include_tests and _is_test_file(rel):
                continue
            if rel in by_rel:
                continue
            files.append(p)
            by_rel[rel] = p
            sigs[rel] = _file_sig(p)
            if len(files) >= max_files:
                break
        if len(files) >= max_files:
            break
    return files, by_rel, sigs


def _load_index(index_path: Path) -> CodeIndex:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    idx = CodeIndex()
    files_raw = data.get("files") if isinstance(data, dict) else {}
    if isinstance(files_raw, dict):
        for rel, fr in files_raw.items():
            if not isinstance(fr, dict):
                continue
            classes: List[ClassRecord] = []
            for c in fr.get("classes", []) or []:
                if not isinstance(c, dict):
                    continue
                classes.append(
                    ClassRecord(
                        name=str(c.get("name", "")),
                        file_path=str(rel),
                        package=str(c.get("package", "")),
                        superclass=str(c.get("superclass")) if c.get("superclass") is not None else None,
                        interfaces=tuple(str(x) for x in (c.get("interfaces") or [])),
                        annotations=tuple(str(x) for x in (c.get("annotations") or [])),
                        methods=tuple(str(x) for x in (c.get("methods") or [])),
                    )
                )
            idx.files[str(rel)] = FileRecord(
                relative_path=str(rel),
                package=str(fr.get("package", "")),
                module=str(fr.get("module", "")),
                classes=tuple(classes),
                imports=frozenset(str(x) for x in (fr.get("imports") or [])),
                is_test=bool(fr.get("is_test", False)),
                line_count=int(fr.get("line_count", 0)),
            )

    for ep in data.get("entry_points", []) or []:
        if not isinstance(ep, dict):
            continue
        et = str(ep.get("entry_type", EntryPointType.UNKNOWN.value))
        idx.entry_points.append(
            EntryPointRecord(
                entry_type=EntryPointType(et) if et in {e.value for e in EntryPointType} else EntryPointType.UNKNOWN,
                relative_path=str(ep.get("relative_path", "")),
                class_name=str(ep.get("class_name", "")),
                method_name=str(ep.get("method_name", "")),
                metadata=dict(ep.get("metadata") or {}),
                invokes=tuple(str(x) for x in (ep.get("invokes") or [])),
                pattern_matched=str(ep.get("pattern_matched", "")),
            )
        )

    for ce in data.get("call_edges", []) or []:
        if not isinstance(ce, dict):
            continue
        conf = str(ce.get("confidence", CallConfidence.MEDIUM.value))
        idx.call_edges.append(
            CallEdge(
                source_file=str(ce.get("source_file", "")),
                source_class=str(ce.get("source_class", "")),
                source_method=str(ce.get("source_method", "")),
                target_class=str(ce.get("target_class", "")),
                target_method=str(ce.get("target_method", "")),
                confidence=CallConfidence(conf) if conf in {c.value for c in CallConfidence} else CallConfidence.MEDIUM,
                target_file=str(ce.get("target_file")) if ce.get("target_file") is not None else None,
            )
        )
    idx.build_indices()
    return idx


def _write_meta(
    meta_path: Path,
    *,
    workspace_root: Path,
    source_dirs: List[str],
    include_tests: bool,
    max_files: int,
    signatures: Dict[str, Dict[str, int]],
) -> None:
    meta = {
        "workspace_root": str(workspace_root),
        "source_dirs": source_dirs,
        "include_tests": bool(include_tests),
        "max_files": int(max_files),
        "file_signatures": signatures,
    }
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")


def build_index_with_progress(
    workspace_root: Path,
    source_dirs: List[str],
    include_tests: bool,
    max_files: int,
    progress_every: int,
) -> CodeIndex:
    t0 = _now()
    print(f"[1/4] Discovering Java files under: {workspace_root}")
    print(f"      source_dirs={source_dirs}")
    print(f"      include_tests={include_tests}, max_files={max_files}")

    files, _, _ = _discover_java_files(workspace_root, source_dirs, include_tests, max_files)

    total = len(files)
    print(f"[2/4] Candidate files to process: {total}")
    if total == 0:
        return CodeIndex()

    builder = CodeIndexBuilder(workspace_root, include_tests=include_tests, max_files=max_files)
    index = CodeIndex()
    kept = 0
    skipped = 0

    print("[3/4] Extracting file/class/method/call graph data")
    bar = ProgressBar(total, enabled=True, label="extract")
    for i, java_file in enumerate(files, start=1):
        rel = str(java_file.relative_to(workspace_root)).replace("\\", "/")
        rec = builder._process_file(java_file, rel)  # reuse existing extraction logic
        if rec is None:
            skipped += 1
        else:
            index.files[rel] = rec
            kept += 1
            index.entry_points.extend(builder._extract_entry_points(java_file, rel))
            try:
                content = java_file.read_text(encoding="utf-8", errors="replace")
                for cls in rec.classes:
                    index.call_edges.extend(builder.extractor.extract_call_edges(content, rel, cls.name))
            except (OSError, PermissionError):
                pass

        bar.update(i, extra=f"kept={kept} skipped={skipped}")

    bar.finish(extra=f"kept={kept} skipped={skipped}")
    print("[4/4] Building derived indices")
    index.build_indices()
    print(f"      done in {(_now() - t0):.2f}s | stats={json.dumps(index.stats, sort_keys=True)}")
    return index


def refresh_index_incremental(
    workspace_root: Path,
    source_dirs: List[str],
    include_tests: bool,
    max_files: int,
    progress_every: int,
    out_path: Path,
) -> CodeIndex:
    meta_path = _meta_path_for_index(out_path)
    if not out_path.exists() or not meta_path.exists():
        print("incremental cache missing; falling back to full build")
        idx = build_index_with_progress(workspace_root, source_dirs, include_tests, max_files, progress_every)
        files, _, sigs = _discover_java_files(workspace_root, source_dirs, include_tests, max_files)
        _write_meta(
            meta_path,
            workspace_root=workspace_root,
            source_dirs=source_dirs,
            include_tests=include_tests,
            max_files=max_files,
            signatures=sigs,
        )
        return idx

    t0 = _now()
    print(f"[1/5] Loading cached index: {out_path}")
    idx = _load_index(out_path)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    old_sigs = meta.get("file_signatures", {}) if isinstance(meta, dict) else {}
    if not isinstance(old_sigs, dict):
        old_sigs = {}

    print("[2/5] Discovering current Java files")
    files, by_rel, new_sigs = _discover_java_files(workspace_root, source_dirs, include_tests, max_files)
    del files  # by_rel/new_sigs are used for refresh

    old_keys = set(old_sigs.keys())
    new_keys = set(new_sigs.keys())
    removed = sorted(old_keys - new_keys)
    added = sorted(new_keys - old_keys)
    changed = sorted(k for k in (old_keys & new_keys) if old_sigs.get(k) != new_sigs.get(k))
    touched = added + changed

    print(
        f"[3/5] Delta summary: added={len(added)} changed={len(changed)} removed={len(removed)} unchanged={len(new_keys) - len(touched)}"
    )
    if not touched and not removed:
        print("[4/5] No changes detected; keeping cached index")
        idx.build_indices()
        _write_meta(
            meta_path,
            workspace_root=workspace_root,
            source_dirs=source_dirs,
            include_tests=include_tests,
            max_files=max_files,
            signatures=new_sigs,
        )
        print(f"[5/5] done in {(_now() - t0):.2f}s | stats={json.dumps(idx.stats, sort_keys=True)}")
        return idx

    builder = CodeIndexBuilder(workspace_root, include_tests=include_tests, max_files=max_files)
    touched_set = set(touched)

    # Drop stale records before re-adding updated ones.
    for rel in removed + touched:
        idx.files.pop(rel, None)
    idx.entry_points = [ep for ep in idx.entry_points if ep.relative_path not in touched_set and ep.relative_path not in set(removed)]
    idx.call_edges = [ce for ce in idx.call_edges if ce.source_file not in touched_set and ce.source_file not in set(removed)]

    print("[4/5] Reprocessing touched files")
    kept = 0
    skipped = 0
    total = len(touched)
    bar = ProgressBar(max(1, total), enabled=True, label="refresh")
    for i, rel in enumerate(touched, start=1):
        p = by_rel.get(rel)
        if p is None:
            skipped += 1
            bar.update(i, extra=f"refreshed={kept} skipped={skipped}")
            continue
        rec = builder._process_file(p, rel)
        if rec is None:
            skipped += 1
        else:
            idx.files[rel] = rec
            kept += 1
            idx.entry_points.extend(builder._extract_entry_points(p, rel))
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                for cls in rec.classes:
                    idx.call_edges.extend(builder.extractor.extract_call_edges(content, rel, cls.name))
            except (OSError, PermissionError):
                pass
        bar.update(i, extra=f"refreshed={kept} skipped={skipped}")

    if total:
        bar.finish(extra=f"refreshed={kept} skipped={skipped}")
    print("[5/5] Rebuilding derived indices")
    idx.build_indices()
    _write_meta(
        meta_path,
        workspace_root=workspace_root,
        source_dirs=source_dirs,
        include_tests=include_tests,
        max_files=max_files,
        signatures=new_sigs,
    )
    print(f"      done in {(_now() - t0):.2f}s | stats={json.dumps(idx.stats, sort_keys=True)}")
    return idx


def main() -> int:
    ap = argparse.ArgumentParser(description="Build authority code index with progress")
    ap.add_argument("--workspace-root", required=True, help="Workspace root path")
    ap.add_argument(
        "--source-dir",
        action="append",
        default=[],
        help="Source directory relative to workspace (repeatable)",
    )
    ap.add_argument("--include-tests", action="store_true", help="Include test Java files")
    ap.add_argument("--max-files", type=int, default=50000, help="Hard cap on files processed")
    ap.add_argument(
        "--progress-every",
        type=int,
        default=100,
        help="Deprecated: retained for backward compatibility (ignored; dynamic progress bar is always used)",
    )
    ap.add_argument(
        "--out",
        default="",
        help="Output JSON path (default: runtime/.cache/authority_code_index.<workspace-hash>.json)",
    )
    ap.add_argument(
        "--refresh-mode",
        choices=("auto", "full", "incremental"),
        default="auto",
        help="Build mode: auto (smart full/incremental), full, or incremental",
    )
    args = ap.parse_args()

    workspace_root = Path(args.workspace_root).expanduser().resolve()
    if not workspace_root.exists() or not workspace_root.is_dir():
        raise SystemExit(f"workspace root not found or not a directory: {workspace_root}")

    source_dirs = _discover_source_dirs(workspace_root, args.source_dir)
    out_path = _resolve_out_path(workspace_root, args.out or None)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    max_files = max(1, int(args.max_files))
    progress_every = max(0, int(args.progress_every))
    mode = str(args.refresh_mode or "auto")
    if mode == "auto":
        ok, reason = _can_incremental(
            out_path=out_path,
            workspace_root=workspace_root,
            source_dirs=source_dirs,
            include_tests=bool(args.include_tests),
            max_files=max_files,
        )
        mode = "incremental" if ok else "full"
        print(f"[mode] auto -> {mode} ({reason})")

    if mode == "incremental":
        index = refresh_index_incremental(
            workspace_root=workspace_root,
            source_dirs=source_dirs,
            include_tests=bool(args.include_tests),
            max_files=max_files,
            progress_every=progress_every,
            out_path=out_path,
        )
    else:
        index = build_index_with_progress(
            workspace_root=workspace_root,
            source_dirs=source_dirs,
            include_tests=bool(args.include_tests),
            max_files=max_files,
            progress_every=progress_every,
        )
        _, _, sigs = _discover_java_files(workspace_root, source_dirs, bool(args.include_tests), max_files)
        _write_meta(
            _meta_path_for_index(out_path),
            workspace_root=workspace_root,
            source_dirs=source_dirs,
            include_tests=bool(args.include_tests),
            max_files=max_files,
            signatures=sigs,
        )
    index.save(out_path)
    print(f"saved_index: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
