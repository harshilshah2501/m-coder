"""
Bounded deterministic score nudges applied to lexical hits before final sort.

Not a reranker backend: small integer deltas on existing ``RetrievalHit.score`` only.
"""

from __future__ import annotations

from typing import Tuple


def deterministic_rank_nudge(relative_path: str, query: str, tokens: Tuple[str, ...]) -> int:
    """
    Return a bounded delta in ``[-40, 70]`` to add to the integer lexical score.

    Empty-query / tokenless callers should pass ``tokens=()`` and get ``0``.
    """
    if not tokens:
        return 0

    pl = relative_path.replace("\\", "/").lower()
    bn = pl.rsplit("/", 1)[-1]
    stem = bn.rsplit(".", 1)[0] if "." in bn else bn
    q = query.lower()
    d = 0

    if "/test/" in pl or "test-plugin" in pl or pl.endswith(".json") or "/docs/" in pl:
        return -40

    if "/src/main/java/" in pl:
        d += 4

    for t in tokens:
        if len(t) < 4:
            continue
        if t in stem and t in q:
            d += 7

    for role in ("engine", "processor", "collector", "poller", "enricher", "datastore"):
        if role in q and role in stem:
            d += 12

    if ("handler" in stem or "uiaction" in stem) and any(
        x in q for x in ("collector", "poll", "metric", "topology", "enrich", "derived")
    ):
        if not any(k in stem for k in ("collector", "poller", "enricher", "metric")):
            d -= 20

    for seg in ("log", "aiops", "nms", "store", "datastore", "trace", "visualization"):
        if seg in q and f"/{seg}/" in pl:
            d += 14

    if ("objectconfig" in stem or "policycache" in stem) and any(
        x in q for x in ("poll", "derived", "processing", "pipeline", "metric")
    ):
        d -= 16

    return max(-40, min(70, d))
