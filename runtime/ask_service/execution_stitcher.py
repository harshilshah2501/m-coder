from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, Iterable, Optional, Sequence, Set, Tuple

from runtime.context.contracts import ContextBundle


_KEYWORDS = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "return",
    "throw",
    "new",
    "try",
    "synchronized",
    "super",
    "this",
}


@dataclass(frozen=True)
class StitchResult:
    stitched: bool
    edge_type: str  # none|direct_call|store_service|registration
    owner_method_window: str
    target_file: str
    target_method: str
    target_window: str
    confidence: str  # none|partial|visible
    stitched_edge_count: int
    call_site_candidates_detected: bool
    call_site_candidate_count: int
    call_site_resolution_state: str  # none|unresolved|resolved_visible
    resolved_from_method: str
    resolved_to_method: str
    resolved_to_file: str
    reason: str


def _norm(p: str) -> str:
    return p.replace("\\", "/").strip().lower()


def _line_count(text: str) -> int:
    if not text:
        return 0
    return len(str(text).splitlines())


def _class_from_path(path: str) -> str:
    b = str(path or "").replace("\\", "/").rsplit("/", 1)[-1]
    if "." in b:
        b = b.rsplit(".", 1)[0]
    return b.strip()


def _item_content(bundle: ContextBundle, rel_path: str) -> str:
    reln = _norm(rel_path)
    for item in bundle.items:
        p = _norm(item.path)
        if p == reln or p.endswith("/" + reln):
            return str(item.content or "")
    return ""


def _extract_method_window(content: str, method: str, *, max_lines: int) -> str:
    txt = str(content or "")
    m = str(method or "").strip()
    if not txt or not m:
        return ""
    esc = re.escape(m)
    sig = re.search(
        rf"(?:public|private|protected|static|final|synchronized|\s)+"
        rf"[A-Za-z_][A-Za-z0-9_<>\[\],\s?]*\s+"
        rf"(?<![.\w]){esc}\s*\([^;\n\r]*\)\s*\{{?",
        txt,
        flags=re.IGNORECASE,
    )
    if sig is None:
        sig = re.search(rf"\b{esc}\s*\(", txt)
    if sig is None:
        return ""
    start = txt.rfind("\n", 0, sig.start())
    start = 0 if start < 0 else start + 1
    rem = txt[start:]
    lines = rem.splitlines()
    return "\n".join(lines[: max(1, int(max_lines))]).strip()


def _method_decl_present(content: str, method: str) -> bool:
    if not content or not method:
        return False
    esc = re.escape(method)
    return bool(
        re.search(
            rf"(?:public|private|protected|static|final|synchronized|\s)+"
            rf"[A-Za-z_][A-Za-z0-9_<>\[\],\s?]*\s+"
            rf"(?<![.\w]){esc}\s*\(",
            content,
            flags=re.IGNORECASE,
        )
    )


def _extract_calls(method_window: str, owner_method: str) -> Sequence[Tuple[str, str, str]]:
    """
    Returns tuples of (call_type, class_hint, method_name):
    - call_type: direct_call|store_service|registration
    """
    out: list[Tuple[str, str, str]] = []
    txt = str(method_window or "")
    if not txt:
        return out

    for cls, meth in re.findall(r"\b([A-Z][A-Za-z0-9_]*)\s*\.\s*([A-Za-z_]\w*)\s*\(", txt):
        if meth in _KEYWORDS or meth == owner_method:
            continue
        et = "store_service" if meth.lower() in {"getstore", "save", "update", "publish", "send", "execute"} else "direct_call"
        out.append((et, cls, meth))

    for meth in re.findall(r"\b([A-Za-z_]\w*)\s*\(", txt):
        ml = meth.lower()
        if ml in _KEYWORDS or meth == owner_method:
            continue
        if ml in {"route", "handler", "consumer"}:
            out.append(("registration", "", meth))
        elif ml in {"save", "update", "publish", "send", "execute"}:
            out.append(("store_service", "", meth))
        else:
            out.append(("direct_call", "", meth))
    return out


def _dedupe_calls(calls: Sequence[Tuple[str, str, str]]) -> Sequence[Tuple[str, str, str]]:
    seen: Set[Tuple[str, str, str]] = set()
    out: list[Tuple[str, str, str]] = []
    for c in calls:
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
    return out


def _none_result(owner_method_window: str, reason: str, *, confidence: str = "none") -> StitchResult:
    return StitchResult(
        stitched=False,
        edge_type="none",
        owner_method_window=owner_method_window,
        target_file="",
        target_method="",
        target_window="",
        confidence=confidence,
        stitched_edge_count=0,
        call_site_candidates_detected=False,
        call_site_candidate_count=0,
        call_site_resolution_state="none",
        resolved_from_method="",
        resolved_to_method="",
        resolved_to_file="",
        reason=reason,
    )


def stitch_first_hop(
    *,
    bundle: ContextBundle,
    owner_file: str,
    owner_class: str,
    owner_method: str,
    owner_method_window: str,
    collaborator_paths: Iterable[str],
    max_stitches_per_answer: int = 1,
    max_methods_total: int = 2,
    max_additional_files: int = 1,
    max_total_stitch_lines: int = 40,
) -> StitchResult:
    if (
        not owner_file
        or not owner_class
        or not owner_method
        or not owner_method_window
        or max_stitches_per_answer < 1
        or max_methods_total < 2
        or max_additional_files < 1
    ):
        return _none_result(owner_method_window, "insufficient_owner_method")

    if _line_count(owner_method_window) > max_total_stitch_lines:
        return _none_result(owner_method_window, "owner_window_over_budget", confidence="partial")

    owner_content = _item_content(bundle, owner_file)
    calls = _dedupe_calls(_extract_calls(owner_method_window, owner_method))
    candidate_count = len(calls)
    if not calls:
        return _none_result(owner_method_window, "no_visible_downstream_call", confidence="partial")

    collab_by_class: Dict[str, str] = {}
    collab_norms: Set[str] = set()
    for p in collaborator_paths:
        cls = _class_from_path(str(p))
        if cls:
            collab_by_class[cls.lower()] = str(p)
        collab_norms.add(_norm(str(p)))

    owner_class_l = owner_class.lower()
    for edge_type, class_hint, meth in calls:
        # 1) same-file helper has highest priority
        if _method_decl_present(owner_content, meth) and meth != owner_method:
            target_window = _extract_method_window(owner_content, meth, max_lines=max_total_stitch_lines // 2)
            if target_window:
                return StitchResult(
                    True,
                    "direct_call",
                    owner_method_window,
                    owner_file,
                    meth,
                    target_window,
                    "visible",
                    1,
                        True,
                        candidate_count,
                        "resolved_visible",
                        owner_method,
                        meth,
                        owner_file,
                    "same_file_helper",
                )

        # 2) explicit class-qualified collaborator call
        if class_hint:
            path = collab_by_class.get(class_hint.lower())
            if path:
                content = _item_content(bundle, path)
                tw = _extract_method_window(content, meth, max_lines=max_total_stitch_lines // 2)
                if tw:
                    return StitchResult(
                        True,
                        edge_type,
                        owner_method_window,
                        path,
                        meth,
                        tw,
                        "visible",
                        1,
                        True,
                        candidate_count,
                        "resolved_visible",
                        owner_method,
                        meth,
                        path,
                        "collaborator_class_qualified",
                    )

        # 3) same-domain collaborator method match
        for cp in collaborator_paths:
            cpn = _norm(str(cp))
            if cpn in collab_norms and owner_class_l not in cpn:
                content = _item_content(bundle, str(cp))
                if _method_decl_present(content, meth):
                    tw = _extract_method_window(content, meth, max_lines=max_total_stitch_lines // 2)
                    if tw:
                        return StitchResult(
                            True,
                            edge_type,
                            owner_method_window,
                            str(cp),
                            meth,
                            tw,
                            "visible",
                            1,
                            True,
                            candidate_count,
                            "resolved_visible",
                            owner_method,
                            meth,
                            str(cp),
                            "collaborator_method_match",
                        )

    return StitchResult(
        stitched=False,
        edge_type="none",
        owner_method_window=owner_method_window,
        target_file="",
        target_method="",
        target_window="",
        confidence="partial",
        stitched_edge_count=0,
        call_site_candidates_detected=True,
        call_site_candidate_count=candidate_count,
        call_site_resolution_state="unresolved",
        resolved_from_method=owner_method,
        resolved_to_method="",
        resolved_to_file="",
        reason="target_not_resolved_within_bounds",
    )
