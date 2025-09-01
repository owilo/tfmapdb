# search_base.py (modified)

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

    def detect_sort_name(self, sort_name: str) -> bool:
        """
        Return True if this handler can handle a sort token named `sort_name`.
        """
        return False

    def parse_value(self, token_value: str):
        """Normalize the token value (strip flags). Return handler-specific value(s)."""
        return token_value

    def apply(self, qs: QuerySet, included_values: List[str], excluded_values: List[str], request=None) -> QuerySet:
        """Apply filtering for these token values and return modified queryset."""
        return qs

    def prepare_sort(self, qs: QuerySet, sort_name: str, direction: str, request=None):
        """
        Optionally annotate the queryset and return a field name that can be used for ordering.
        If the handler cannot prepare sorting for sort_name, return (qs, None).
        Default behaviour uses self.sort_key if present and sortable.
        Handlers may return a modified queryset (with annotations) and the field name string.
        """
        if not self.sortable:
            return qs, None
        if self.sort_key:
            return qs, self.sort_key
        return qs, None


SORT_RE = re.compile(r'^(?P<name>.+)-(?P<dir>asc|desc)$', re.IGNORECASE)

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
                        name = m.group('name').strip()
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
            for raw_name, dir_ in specs:
                name = raw_name
                lname = name.lower()
                # Exact handler name match first
                if lname in self.handlers_by_name:
                    h = self.handlers_by_name[lname]
                    # Allow handler to prepare (annotate) and supply a key
                    qs, key = h.prepare_sort(qs, name, dir_, request=request)
                    if not key:
                        continue
                    if self._is_orderable_field(qs, key):
                        order_fields.append(key if dir_ == 'asc' else f"-{key}")
                else:
                    # Ask handlers whether they can handle this sort token dynamically
                    key_selected = None
                    working_qs = qs
                    for h in self.handlers:
                        if h.detect_sort_name(name):
                            working_qs, key = h.prepare_sort(working_qs, name, dir_, request=request)
                            if key and self._is_orderable_field(working_qs, key):
                                key_selected = (working_qs, key)
                                break
                    if key_selected:
                        qs = key_selected[0]
                        key = key_selected[1]
                        order_fields.append(key if dir_ == 'asc' else f"-{key}")
                    else:
                        # maybe the name refers to a raw model field
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
