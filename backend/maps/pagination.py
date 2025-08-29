import json
import base64
from typing import List, Any, Tuple
from django.db.models import Q

def encode_cursor(values: List[Any]) -> str:
    raw = json.dumps(values, separators=(',', ':'), ensure_ascii=False)
    return base64.urlsafe_b64encode(raw.encode()).decode()

def decode_cursor(cursor: str) -> List:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        return json.loads(raw)
    except Exception:
        return []

def build_keyset_q(sort_specs: List[Tuple[str,str]], last_values: List, model_field_cast=None):
    assert len(sort_specs) == len(last_values), "sort_specs and last_values length mismatch"

    q_total = Q()
    for i in range(len(sort_specs)):
        prefix_q = Q()
        for j in range(0, i):
            field_j, dir_j = sort_specs[j]
            vj = last_values[j]
            if model_field_cast:
                vj = model_field_cast(field_j, vj)
            prefix_q &= Q(**{f"{field_j}": vj})

        field_i, dir_i = sort_specs[i]
        vi = last_values[i]
        if model_field_cast:
            vi = model_field_cast(field_i, vi)

        if dir_i.lower() == 'desc':
            prefix_q &= Q(**{f"{field_i}__lt": vi})
        else:
            prefix_q &= Q(**{f"{field_i}__gt": vi})

        q_total |= prefix_q

    return q_total

def default_model_field_cast(field_name, value):
    if field_name == 'similarity' or field_name.startswith('similarity_'):
        try:
            return round(float(value), 6)
        except Exception:
            return value
    return value
