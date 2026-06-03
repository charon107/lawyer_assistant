"""Helper: serialize list/dict schema fields to JSON text for storage.

The employment-legal models store list/dict fields as TEXT columns. Services
call ``dump_for_db`` to turn a Pydantic payload into repo kwargs, JSON-encoding
any field named in ``json_fields``.
"""

import json
from typing import Any

from pydantic import BaseModel


def dump_for_db(data: BaseModel, json_fields: set[str]) -> dict[str, Any]:
    raw = data.model_dump(exclude_unset=True)
    out: dict[str, Any] = {}
    for key, value in raw.items():
        if key in json_fields and isinstance(value, (list, dict)):
            out[key] = json.dumps(value, ensure_ascii=False)
        else:
            out[key] = value
    return out
