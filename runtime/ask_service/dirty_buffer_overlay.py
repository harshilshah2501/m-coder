from __future__ import annotations

from typing import Any, Dict, List, Tuple

from runtime.context.contracts import ContextBundle, ContextBundleLimits, ContextItem
from runtime.layer5.retrieval.path_resolve import workspace_path_key


def extract_dirty_buffers(client_context: Any) -> Tuple[Dict[str, Tuple[str, str]], Dict[str, Any]]:
    """
    Parse dirty buffer payload from client_context.

    Returns key -> (original_path, content), where key is workspace-normalized.
    Last duplicate path wins for deterministic behavior.
    """
    out: Dict[str, Tuple[str, str]] = {}
    stats: Dict[str, Any] = {
        "payload_present": False,
        "provided_count": 0,
        "valid_count": 0,
        "invalid_count": 0,
    }
    if not isinstance(client_context, dict):
        return out, stats
    stats["payload_present"] = "dirty_buffers" in client_context
    raw = client_context.get("dirty_buffers")
    if raw is None:
        return out, stats
    if not isinstance(raw, list):
        stats["invalid_count"] = 1
        return out, stats
    stats["provided_count"] = len(raw)
    for item in raw:
        if not isinstance(item, dict):
            stats["invalid_count"] += 1
            continue
        path = str(item.get("path") or "").strip()
        content = item.get("content")
        if not path or not isinstance(content, str):
            stats["invalid_count"] += 1
            continue
        out[workspace_path_key(path)] = (path, content)
    stats["valid_count"] = len(out)
    return out, stats


def apply_dirty_buffer_overlay(
    bundle: ContextBundle,
    dirty_buffers: Dict[str, Tuple[str, str]],
) -> Tuple[ContextBundle, Dict[str, Any]]:
    """
    Overlay unsaved file content onto matching ContextBundle items.

    This only changes in-memory bundle content for the request. It does not mutate
    on-disk files or index artifacts.
    """
    if not dirty_buffers:
        return bundle, {"used": False, "applied_count": 0, "requested_count": 0, "applied_paths": []}

    applied_paths: List[str] = []
    new_items: List[ContextItem] = []
    changed = False
    for item in bundle.items:
        key = workspace_path_key(item.path)
        if key in dirty_buffers:
            _, content = dirty_buffers[key]
            new_items.append(
                ContextItem(
                    path=item.path,
                    content=content,
                    byte_size=len(content.encode("utf-8")),
                    selection_reason=item.selection_reason,
                )
            )
            applied_paths.append(item.path)
            changed = True
        else:
            new_items.append(item)

    if not changed:
        return bundle, {
            "used": False,
            "applied_count": 0,
            "requested_count": len(dirty_buffers),
            "applied_paths": [],
        }

    new_limits = ContextBundleLimits(
        max_files=bundle.limits.max_files,
        max_bytes=sum(i.byte_size for i in new_items),
        truncated=bundle.limits.truncated,
    )
    return (
        ContextBundle(
            task_id=bundle.task_id,
            revision=bundle.revision,
            created_at_utc=bundle.created_at_utc,
            items=new_items,
            limits=new_limits,
            provenance=bundle.provenance,
        ),
        {
            "used": True,
            "applied_count": len(applied_paths),
            "requested_count": len(dirty_buffers),
            "applied_paths": applied_paths,
        },
    )
