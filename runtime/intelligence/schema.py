"""Schema validators for Lane A intelligence documents."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


MECHANISM_TYPES = {"EVENTBUS", "DIRECT_CALL", "API_ROUTE", "STORE", "OTHER"}
QUERY_MATCH_STRATEGIES = {"exact", "token", "fuzzy"}


class IntelligenceSchemaError(ValueError):
    """Raised when an intelligence document violates contract."""


def _expect_mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise IntelligenceSchemaError(f"{path} must be a mapping")
    return value


def _expect_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IntelligenceSchemaError(f"{path} must be a non-empty string")
    return value


def _expect_list(value: Any, path: str) -> Sequence[Any]:
    if not isinstance(value, list):
        raise IntelligenceSchemaError(f"{path} must be a list")
    return value


def _expect_string_list(value: Any, path: str) -> Sequence[str]:
    items = _expect_list(value, path)
    for idx, item in enumerate(items):
        if not isinstance(item, str) or not item.strip():
            raise IntelligenceSchemaError(f"{path}[{idx}] must be a non-empty string")
    return items


def _validate_mechanism(mechanism: Any, path: str) -> None:
    record = _expect_mapping(mechanism, path)
    mechanism_type = _expect_string(record.get("type"), f"{path}.type")
    if mechanism_type not in MECHANISM_TYPES:
        raise IntelligenceSchemaError(f"{path}.type must be one of {sorted(MECHANISM_TYPES)}")

    common = {"type", "source_symbol", "target_symbol", "file_paths"}
    allowed_by_type = {
        "EVENTBUS": common | {"address"},
        "DIRECT_CALL": common,
        "API_ROUTE": common,
        "STORE": common | {"store_class", "config_key", "config_bound"},
        "OTHER": common,
    }
    allowed_keys = allowed_by_type[mechanism_type]

    extra_keys = set(record.keys()) - allowed_keys
    if extra_keys:
        extras = ", ".join(sorted(extra_keys))
        raise IntelligenceSchemaError(
            f"{path} contains fields not allowed for type={mechanism_type}: {extras}"
        )

    if "source_symbol" in record:
        _expect_string(record["source_symbol"], f"{path}.source_symbol")
    if "target_symbol" in record:
        _expect_string(record["target_symbol"], f"{path}.target_symbol")
    if "file_paths" in record:
        _expect_string_list(record["file_paths"], f"{path}.file_paths")

    if mechanism_type == "EVENTBUS":
        _expect_string(record.get("address"), f"{path}.address")
    elif "address" in record:
        raise IntelligenceSchemaError(f"{path}.address only valid for EVENTBUS")

    if mechanism_type == "STORE":
        _expect_string(record.get("store_class"), f"{path}.store_class")
        config_bound = bool(record.get("config_bound", False))
        if "config_bound" in record and not isinstance(record["config_bound"], bool):
            raise IntelligenceSchemaError(f"{path}.config_bound must be boolean")
        if config_bound:
            _expect_string(record.get("config_key"), f"{path}.config_key")
        elif "config_key" in record and (not isinstance(record["config_key"], str) or not record["config_key"].strip()):
            raise IntelligenceSchemaError(f"{path}.config_key must be non-empty when present")
    else:
        for forbidden in ("store_class", "config_key", "config_bound"):
            if forbidden in record:
                raise IntelligenceSchemaError(f"{path}.{forbidden} only valid for STORE")


def _validate_data_transformations(items: Any, path: str) -> None:
    for idx, item in enumerate(_expect_list(items, path)):
        record = _expect_mapping(item, f"{path}[{idx}]")
        required = ("input", "operation", "output")
        for key in required:
            _expect_string(record.get(key), f"{path}[{idx}].{key}")
        if "conditions" in record:
            _expect_string(record["conditions"], f"{path}[{idx}].conditions")
        if "produced_fields" in record:
            _expect_string_list(record["produced_fields"], f"{path}[{idx}].produced_fields")


def _validate_known_failure_modes(items: Any, path: str) -> None:
    for idx, item in enumerate(_expect_list(items, path)):
        record = _expect_mapping(item, f"{path}[{idx}]")
        _expect_string(record.get("symptom"), f"{path}[{idx}].symptom")
        if "diagnostic_files" not in record:
            raise IntelligenceSchemaError(f"{path}[{idx}].diagnostic_files is required")
        _expect_string_list(record["diagnostic_files"], f"{path}[{idx}].diagnostic_files")


def _validate_query_aliases(items: Any, path: str) -> None:
    for idx, item in enumerate(_expect_list(items, path)):
        record = _expect_mapping(item, f"{path}[{idx}]")
        _expect_string(record.get("alias"), f"{path}[{idx}].alias")
        strategy = _expect_string(record.get("match_strategy"), f"{path}[{idx}].match_strategy")
        if strategy not in QUERY_MATCH_STRATEGIES:
            raise IntelligenceSchemaError(
                f"{path}[{idx}].match_strategy must be one of {sorted(QUERY_MATCH_STRATEGIES)}"
            )
        if strategy == "fuzzy":
            guardrails = _expect_mapping(record.get("fuzzy_guardrails"), f"{path}[{idx}].fuzzy_guardrails")
            required = ("min_score", "min_token_overlap", "max_candidates")
            for key in required:
                if key not in guardrails:
                    raise IntelligenceSchemaError(f"{path}[{idx}].fuzzy_guardrails.{key} is required")
            min_score = guardrails["min_score"]
            if not isinstance(min_score, (int, float)) or not (0 <= float(min_score) <= 1):
                raise IntelligenceSchemaError(f"{path}[{idx}].fuzzy_guardrails.min_score must be in [0,1]")
            for key in ("min_token_overlap", "max_candidates"):
                value = guardrails[key]
                if not isinstance(value, int) or value < 1:
                    raise IntelligenceSchemaError(f"{path}[{idx}].fuzzy_guardrails.{key} must be >= 1")
        elif "fuzzy_guardrails" in record:
            raise IntelligenceSchemaError(
                f"{path}[{idx}].fuzzy_guardrails only allowed when match_strategy='fuzzy'"
            )


def validate_behavior_flows_document(document: Mapping[str, Any]) -> None:
    """Validate the behavior flows contract."""
    root = _expect_mapping(document, "behavior_flows")
    _expect_string(root.get("schema_version"), "behavior_flows.schema_version")
    behaviors = _expect_list(root.get("behavior_flows"), "behavior_flows.behavior_flows")
    if not behaviors:
        raise IntelligenceSchemaError("behavior_flows.behavior_flows must not be empty")

    for idx, behavior in enumerate(behaviors):
        bpath = f"behavior_flows.behavior_flows[{idx}]"
        record = _expect_mapping(behavior, bpath)
        _expect_string(record.get("behavior_id"), f"{bpath}.behavior_id")
        _expect_string(record.get("summary"), f"{bpath}.summary")
        _expect_string(record.get("priority"), f"{bpath}.priority")

        stages = _expect_list(record.get("stages"), f"{bpath}.stages")
        if not stages:
            raise IntelligenceSchemaError(f"{bpath}.stages must not be empty")
        for sidx, stage in enumerate(stages):
            spath = f"{bpath}.stages[{sidx}]"
            stage_record = _expect_mapping(stage, spath)
            _expect_string(stage_record.get("name"), f"{spath}.name")
            mechanisms = _expect_list(stage_record.get("mechanisms"), f"{spath}.mechanisms")
            if not mechanisms:
                raise IntelligenceSchemaError(f"{spath}.mechanisms must not be empty")
            for midx, mechanism in enumerate(mechanisms):
                _validate_mechanism(mechanism, f"{spath}.mechanisms[{midx}]")

        if "data_transformations" in record:
            _validate_data_transformations(record["data_transformations"], f"{bpath}.data_transformations")
        if "known_failure_modes" in record:
            _validate_known_failure_modes(record["known_failure_modes"], f"{bpath}.known_failure_modes")
        if "query_aliases" in record:
            _validate_query_aliases(record["query_aliases"], f"{bpath}.query_aliases")


def validate_convention_playbooks_document(document: Mapping[str, Any]) -> None:
    """Validate convention playbooks required-step contract."""
    root = _expect_mapping(document, "convention_playbooks")
    _expect_string(root.get("schema_version"), "convention_playbooks.schema_version")
    playbooks = _expect_list(root.get("convention_playbooks"), "convention_playbooks.convention_playbooks")
    if not playbooks:
        raise IntelligenceSchemaError("convention_playbooks.convention_playbooks must not be empty")

    for pidx, playbook in enumerate(playbooks):
        ppath = f"convention_playbooks.convention_playbooks[{pidx}]"
        record = _expect_mapping(playbook, ppath)
        _expect_string(record.get("playbook_id"), f"{ppath}.playbook_id")
        _expect_string(record.get("summary"), f"{ppath}.summary")
        steps = _expect_list(record.get("required_steps"), f"{ppath}.required_steps")
        if not steps:
            raise IntelligenceSchemaError(f"{ppath}.required_steps must not be empty")
        for sidx, step in enumerate(steps):
            spath = f"{ppath}.required_steps[{sidx}]"
            step_record = _expect_mapping(step, spath)
            order = step_record.get("order")
            if not isinstance(order, int) or order < 1:
                raise IntelligenceSchemaError(f"{spath}.order must be an integer >= 1")
            _expect_string(step_record.get("action"), f"{spath}.action")
            _expect_string(step_record.get("verification"), f"{spath}.verification")
            _expect_string(step_record.get("file_template"), f"{spath}.file_template")
