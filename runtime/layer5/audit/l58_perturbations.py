from __future__ import annotations

from dataclasses import replace
from typing import Iterable, List

from runtime.layer5.audit.l58_dataset import GoldenCase, PerturbationInfo


def _split_camel_tokens(text: str) -> str:
    out: List[str] = []
    for token in text.split():
        buf = []
        for i, ch in enumerate(token):
            if i > 0 and ch.isupper() and token[i - 1].islower():
                buf.append(" ")
            buf.append(ch)
        out.append("".join(buf))
    return " ".join(out)


def _typo_light(text: str) -> str:
    # deterministic, minimal typo-like perturbation
    return text.replace("ingestion", "ingetsion").replace("correlation", "correaltion")


def _phrasing_shift(text: str) -> str:
    return f"why/where/fix: {text}"


def _package_omitted(text: str) -> str:
    return text.replace("com.mindarray.", "")


def _abbreviated_symbol(text: str) -> str:
    return text.replace("MetricsParser", "MP").replace("TopologyEngine", "TopoEngine")


def generate_deterministic_variants(base_cases: Iterable[GoldenCase]) -> List[GoldenCase]:
    generated: List[GoldenCase] = []
    for case in sorted(base_cases, key=lambda c: c.id):
        if case.perturbation.kind != "base":
            continue
        transforms = [
            ("abbreviated_symbol", _abbreviated_symbol),
            ("package_omitted", _package_omitted),
            ("camelcase_split", _split_camel_tokens),
            ("typo_light_wording", _typo_light),
            ("phrasing_shift", _phrasing_shift),
        ]
        for kind, fn in transforms:
            new_id = f"{case.id}::{kind}"
            generated.append(
                replace(
                    case,
                    id=new_id,
                    query=fn(case.query),
                    perturbation=PerturbationInfo(
                        family_id=case.perturbation.family_id,
                        kind=kind,
                        source_case_id=case.id,
                    ),
                )
            )
    return generated


def expand_cases_with_perturbations(cases: Iterable[GoldenCase], include_generated: bool = True) -> List[GoldenCase]:
    base = sorted(list(cases), key=lambda c: c.id)
    if not include_generated:
        return base
    generated = generate_deterministic_variants(base)
    return sorted(base + generated, key=lambda c: c.id)
