"""Shared helper: decode JSON-text DB columns into Python values."""

import json


def parse_json_field(v: object) -> object:
    if isinstance(v, str):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return v
    return v
