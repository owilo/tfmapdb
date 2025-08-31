import re
from typing import List, Dict, Tuple, Optional
from django.db.models import QuerySet

class TokenHandler:
    name: str = ''
    allow_prefix: bool = False
    sortable: bool = False
    sort_key: Optional[str] = None

    def detect(self, token: str) -> bool:
        """Return True if this handler recognizes token without an explicit prefix."""
        return False

    def parse_value(self, token_value: str):
        """Normalize the token value (strip flags). Return handler-specific value(s)."""
        return token_value

    def apply(self, qs: QuerySet, included_values: List[str], excluded_values: List[str], request=None) -> QuerySet:
        """Apply filtering for these token values and return modified queryset."""
        return qs

SORT_RE = re.compile(r'^(?P<name>[A-Za-z_]+)-(?P<dir>asc|desc)$', re.IGNORECASE)

class SearchEngine:
    """
    Generic search engine
    """
    def __init__(self, handlers: List[TokenHandler], fallback_order: Optional[List[str]] = None):
        self.handlers = handlers
        self.handlers_by_name = {h.name.lower(): h for h in handlers}
        self.fallback_order = list(fallback_order) if fallback_order else []

    def parse(self, raw: str):
        """
        Returns (grouped_includes, grouped_excludes, sort_specs)
        grouped_includes: {handler_name: [val, ...], ...}
        grouped_excludes: {handler_name: [val, ...], ...}
        sort_specs: list of (name, dir) tuples in the order encountered
        """
        grouped_includes = {name: [] for name in self.handlers_by_name.keys()}
        grouped_excludes = {name: [] for name in self.handlers_by_name.keys()}
        sort_specs = []
        if not raw:
            return grouped_includes, grouped_excludes, sort_specs

        tokens = [t for t in re.split(r'\s+', raw.strip()) if t]
        for tok in tokens:
            # Handle sort tokens first
            if tok.lower().startswith('sort:'):
                raw_sort = tok[5:]
                parts = [p.strip() for p in raw_sort.split(',') if p.strip()]
                for part in parts:
                    m = SORT_RE.match(part)
                    if m:
                        name = m.group('name').lower()
                        dir_ = m.group('dir').lower()
                        sort_specs.append((name, dir_))
                continue

            # Check for exclude prefix
            is_exclude = tok.startswith('!')
            clean_tok = tok[1:] if is_exclude else tok

            if ':' in clean_tok:
                prefix, val = clean_tok.split(':', 1)
                prefix = prefix.lower()
                if prefix in self.handlers_by_name:
                    if is_exclude:
                        grouped_excludes[prefix].append(val)
                    else:
                        grouped_includes[prefix].append(val)
                continue

            # Handle unprefixed tokens
            for h in self.handlers:
                if h.detect(clean_tok):
                    if is_exclude:
                        grouped_excludes[h.name].append(clean_tok)
                    else:
                        grouped_includes[h.name].append(clean_tok)
                    break

        return grouped_includes, grouped_excludes, sort_specs

    def apply_filters(self, qs: QuerySet, grouped_includes: Dict[str, List[str]], grouped_excludes: Dict[str, List[str]], request=None) -> QuerySet:
        """
        Apply handlers' filtering in the order handlers are declared.
        Returns the filtered queryset with no ordering changes here.
        """
        for h in self.handlers:
            included = grouped_includes.get(h.name) or []
            excluded = grouped_excludes.get(h.name) or []
            if included or excluded:
                qs = h.apply(qs, included, excluded, request=request)
        return qs

    def _is_orderable_field(self, qs: QuerySet, field_name: str) -> bool:
        annotations = getattr(qs.query, "annotations", None) or {}
        if field_name in annotations:
            return True

        cur_model = getattr(qs, "model", None)
        if cur_model is None:
            return False

        parts = field_name.split('__')
        try:
            for i, part in enumerate(parts):
                field = cur_model._meta.get_field(part)
                if i < len(parts) - 1:
                    rel_model = getattr(field, 'related_model', None) or getattr(field, 'remote_field', None) and getattr(field.remote_field, 'model', None)
                    if rel_model is None:
                        return False
                    cur_model = rel_model
            return True
        except Exception:
            return False

    def apply_sorting(self, qs: QuerySet, sort_specs: Optional[List[Tuple[str,str]]] = None, request=None) -> QuerySet:
        specs = list(sort_specs) if sort_specs else []

        final_order_fields = []
        
        if specs:
            order_fields = []
            for name, dir_ in specs:
                name = name.lower()
                if name in self.handlers_by_name:
                    h = self.handlers_by_name[name]
                    if not h.sortable:
                        continue
                    key = h.sort_key or name
                    if self._is_orderable_field(qs, key):
                        order_fields.append(key if dir_ == 'asc' else f"-{key}")
                else:
                    if self._is_orderable_field(qs, name):
                        order_fields.append(name if dir_ == 'asc' else f"-{name}")
            if order_fields:
                final_order_fields.extend(order_fields)
        
        if self.fallback_order:
            fallback_order_fields = []
            working_qs = qs
            for raw_field in self.fallback_order:
                field = raw_field.lstrip('-')
                if self._is_orderable_field(working_qs, field):
                    fallback_order_fields.append(raw_field)
            
            if fallback_order_fields:
                existing_fields = set(final_order_fields)
                for field in fallback_order_fields:
                    if field not in existing_fields and f"-{field.lstrip('-')}" not in existing_fields:
                        final_order_fields.append(field)
        
        if final_order_fields:
            return qs.order_by(*final_order_fields)
        
        return qs

    def apply(self, qs: QuerySet, grouped_includes: Dict[str, List[str]], grouped_excludes: Dict[str, List[str]], sort_specs: Optional[List[Tuple[str,str]]] = None, request=None) -> QuerySet:
        qs = self.apply_filters(qs, grouped_includes, grouped_excludes, request=request)
        qs = self.apply_sorting(qs, sort_specs=sort_specs, request=request)
        return qs