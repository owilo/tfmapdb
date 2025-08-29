import json
import base64
from typing import List, Any, Tuple
from django.db.models import Q

def encode_cursor(values: List[Any]) -> str:
    def default_serializer(obj):
        if isinstance(obj, float):
            return repr(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    raw = json.dumps(values, default=default_serializer, separators=(',', ':'), ensure_ascii=False)
    return base64.urlsafe_b64encode(raw.encode()).decode()

def decode_cursor(cursor: str) -> List:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        values = json.loads(raw)
        
        def convert_value(value):
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    return value
            return value
        
        return [convert_value(v) for v in values]
    except Exception:
        return []

def default_model_field_cast(field_name, value):
    if field_name == 'similarity' or field_name.startswith('similarity_'):
        try:
            return float(value)
        except (ValueError, TypeError):
            return value
    return value

def build_keyset_q(sort_specs: List[Tuple[str, str]], last_values: List, model_field_cast=None):
    if len(sort_specs) != len(last_values):
        raise ValueError("sort_specs and last_values length mismatch")
    
    condition = Q()
    
    for i in range(len(sort_specs)):
        equality_conditions = Q()
        for j in range(i):
            field_j, _ = sort_specs[j]
            value_j = last_values[j]
            if model_field_cast:
                value_j = model_field_cast(field_j, value_j)
            equality_conditions &= Q(**{field_j: value_j})
        
        field_i, direction_i = sort_specs[i]
        value_i = last_values[i]
        if model_field_cast:
            value_i = model_field_cast(field_i, value_i)
        
        if direction_i.lower() == 'desc':
            inequality_condition = Q(**{f"{field_i}__lt": value_i})
        else:
            inequality_condition = Q(**{f"{field_i}__gt": value_i})
        
        step_condition = equality_conditions & inequality_condition
        
        condition |= step_condition
    
    return condition

def ensure_stable_ordering(qs, sort_specs):
    has_unique_field = any(
        spec[0] in ['id', 'code', 'pk'] or spec[0].endswith('_id') 
        for spec in sort_specs
    )
    
    if not has_unique_field:
        sort_specs = sort_specs + [('code', 'asc')]
    
    return sort_specs