"""Shared helper: decode JSON-text DB columns into Python values.

SQLite stores list/dict fields as TEXT; Pydantic doesn't auto-decode, so
`*Read` schemas run this in a `field_validator(..., mode="before")` to keep
the API surface typed regardless of storage backend.
"""

import json


def parse_json_field(v: object) -> object:
    if isinstance(v, str):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return v
    return v
