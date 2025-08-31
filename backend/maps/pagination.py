import json
import base64
from typing import List, Any, Tuple
from django.db.models import Q
from rest_framework.exceptions import ValidationError

DEFAULT_LIMIT = 25
MAX_LIMIT = 100

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

class KeysetPagination:    
    def __init__(self, default_limit=DEFAULT_LIMIT, max_limit=MAX_LIMIT):
        self.default_limit = default_limit
        self.max_limit = max_limit
    
    def get_limit(self, request):
        """Extract and validate limit from request"""
        try:
            limit = min(int(request.GET.get('limit', self.default_limit)), self.max_limit)
            return limit if limit > 0 else self.default_limit
        except (ValueError, TypeError):
            return self.default_limit
    
    def get_cursor_values(self, request, expected_length):
        """Extract and decode cursor from request"""
        cursor_token = request.GET.get('cursor')
        if not cursor_token:
            return None
        
        try:
            values = decode_cursor(cursor_token)
            if len(values) != expected_length:
                raise ValidationError('Invalid cursor')
            return values
        except Exception:
            raise ValidationError('Invalid cursor')
    
    def extract_sort_specs_from_queryset(self, queryset):
        """Extract sorting specifications from the queryset"""
        order_by = getattr(queryset.query, 'order_by', [])
        sort_specs = []
        
        for field in order_by:
            if field.startswith('-'):
                sort_specs.append((field[1:], 'desc'))
            else:
                sort_specs.append((field, 'asc'))
        
        return sort_specs
    
    def paginate_queryset(self, queryset, request):
        """
        Paginate a queryset using keyset pagination
        """
        sort_specs = self.extract_sort_specs_from_queryset(queryset)
        
        limit = self.get_limit(request)
        last_values = self.get_cursor_values(request, len(sort_specs)) if sort_specs else None
        
        if last_values:
            keyset_q = build_keyset_q(sort_specs, last_values, model_field_cast=default_model_field_cast)
            queryset = queryset.filter(keyset_q)
        
        items = list(queryset[:limit + 1])
        
        next_cursor = None
        if len(items) > limit and sort_specs:
            last_item = items[limit - 1]
            vals = []
            for key, _ in sort_specs:
                parts = key.split('__')
                v = getattr(last_item, parts[0], None)
                for p in parts[1:]:
                    v = getattr(v, p, None) if v is not None else None
                v = default_model_field_cast(key, v)
                vals.append(v)
            next_cursor = encode_cursor(vals)
            items = items[:limit]
        
        return items, next_cursor