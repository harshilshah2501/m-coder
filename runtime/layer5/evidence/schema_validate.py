"""
Strict validation of evidence bundle dicts against ``evidence_bundle.v1.schema.json``.

Stdlib-only (no ``jsonschema`` dependency). Supports only the subset of JSON Schema
draft-07 used by the v1 evidence schema: ``type``, ``required``, ``properties``,
``additionalProperties``, ``items``, ``enum``, ``const``, ``definitions``, ``$ref``,
``minimum`` for integers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

Schema = Dict[str, Any]


class EvidenceSchemaValidationError(ValueError):
    def __init__(self, message: str, path: str = "$") -> None:
        self.path = path
        super().__init__(f"{path}: {message}")


def _resolve_ref(ref: str, root: Schema) -> Schema:
    if not ref.startswith("#/definitions/"):
        raise EvidenceSchemaValidationError(f"unsupported $ref {ref!r}")
    name = ref.split("/")[-1]
    defs = root.get("definitions") or {}
    if name not in defs:
        raise EvidenceSchemaValidationError(f"unknown definition {name!r}")
    return defs[name]


def _validate(
    instance: Any,
    schema: Schema,
    root: Schema,
    path: str,
) -> None:
    if "$ref" in schema:
        _validate(instance, _resolve_ref(schema["$ref"], root), root, path)
        return

    if "enum" in schema:
        if instance not in schema["enum"]:
            raise EvidenceSchemaValidationError(
                f"value {instance!r} not in enum {schema['enum']!r}", path
            )
        return

    if "const" in schema:
        if instance != schema["const"]:
            raise EvidenceSchemaValidationError(
                f"expected const {schema['const']!r}, got {instance!r}", path
            )
        return

    stype = schema.get("type")
    if stype == "object":
        if not isinstance(instance, dict):
            raise EvidenceSchemaValidationError(f"expected object, got {type(instance).__name__}", path)
        req = schema.get("required") or []
        for key in req:
            if key not in instance:
                raise EvidenceSchemaValidationError(f"missing required property {key!r}", path)
        props = schema.get("properties") or {}
        addl = schema.get("additionalProperties")
        for key, val in instance.items():
            if key in props:
                _validate(val, props[key], root, f"{path}.{key}")
            elif addl is False:
                raise EvidenceSchemaValidationError(f"additional property {key!r} not allowed", path)
            elif isinstance(addl, dict):
                _validate(val, addl, root, f"{path}.{key}")
        return

    if stype == "array":
        if not isinstance(instance, list):
            raise EvidenceSchemaValidationError(f"expected array, got {type(instance).__name__}", path)
        items = schema.get("items")
        if items is not None:
            for i, elem in enumerate(instance):
                _validate(elem, items, root, f"{path}[{i}]")
        return

    if stype == "string":
        if not isinstance(instance, str):
            raise EvidenceSchemaValidationError(f"expected string, got {type(instance).__name__}", path)
        return

    if stype == "integer":
        if type(instance) is not int or isinstance(instance, bool):
            raise EvidenceSchemaValidationError(f"expected integer, got {instance!r}", path)
        if "minimum" in schema and instance < schema["minimum"]:
            raise EvidenceSchemaValidationError(
                f"value {instance} below minimum {schema['minimum']}", path
            )
        return

    if stype == "boolean":
        if not isinstance(instance, bool):
            raise EvidenceSchemaValidationError(f"expected boolean, got {type(instance).__name__}", path)
        return

    raise EvidenceSchemaValidationError(f"unsupported or missing type in schema at {path!r}", path)


def load_v1_schema() -> Schema:
    p = Path(__file__).resolve().parent / "evidence_bundle.v1.schema.json"
    return json.loads(p.read_text(encoding="utf-8"))


def validate_evidence_bundle_dict(instance: Dict[str, Any]) -> None:
    """Raise ``EvidenceSchemaValidationError`` if ``instance`` violates the v1 schema."""
    root = load_v1_schema()
    _validate(instance, root, root, "$")
