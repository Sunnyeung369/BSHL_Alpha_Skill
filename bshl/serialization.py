"""Strict JSON serialization for public dataclasses and enums."""
from dataclasses import fields, is_dataclass
from enum import Enum
from datetime import date, datetime
from math import isfinite
import json


def to_jsonable(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value):
        return {field.name: to_jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, float) and not isfinite(value):
        raise ValueError("JSON numbers must be finite")
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise TypeError(f"Unsupported JSON value: {type(value).__name__}")


def dumps(value):
    return json.dumps(to_jsonable(value), ensure_ascii=False, indent=2, allow_nan=False)


def loads(text):
    """Reject ambiguous duplicate fields and JSON's nonstandard NaN/Infinity."""
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON field: {key}")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError(f"Nonfinite JSON value: {value}")

    return json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)

