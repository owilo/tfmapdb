import re
from typing import List
from django.db.models import Q, QuerySet, Value, Sum, IntegerField, Count, OuterRef, Subquery
from django.db.models.functions import Coalesce
from maps.models import AuthorCategoryCounter, AuthorTagCounter
from maps.constants import CATEGORIES_MAP
from .search_base import TokenHandler

class AuthorNameHandler(TokenHandler):
    name = 'author'
    allow_prefix = True
    sortable = True
    sort_key = 'name'

    def detect(self, token: str) -> bool:
        return True

    def apply(self, qs: QuerySet, included_values: List[str], excluded_values: List[str], request=None) -> QuerySet:
        inc_q = Q()
        exc_q = Q()
        any_inc = False

        for t in included_values:
            norm = t.strip()
            if not norm:
                continue
            any_inc = True
            inc_q |= Q(name__icontains=norm)

        for t in excluded_values:
            norm = t.strip()
            if not norm:
                continue
            exc_q &= ~Q(name__icontains=norm)

        if any_inc or excluded_values:
            if any_inc:
                qs = qs.filter(inc_q)
            if excluded_values:
                qs = qs.exclude(exc_q)
            return qs
        return qs


class AuthorCodeHandler(TokenHandler):
    name = 'code'
    allow_prefix = True
    sortable = False
    code_re = re.compile(r"^((@?\d+(-@?\d*)?)|(-@?\d+))$")

    def detect(self, token: str) -> bool:
        return bool(self.code_re.match(token))

    def _term_to_q(self, term: str):
        norm = term.lstrip('@').strip()
        if not norm:
            return None
        if '-' in norm:
            lo, hi = norm.split('-', 1)
            q = Q()
            if lo.strip() != '':
                try:
                    q &= Q(maps__code__gte=int(lo.strip()))
                except ValueError:
                    return None
            if hi.strip() != '':
                try:
                    q &= Q(maps__code__lte=int(hi.strip()))
                except ValueError:
                    return None
            return q
        else:
            try:
                return Q(maps__code=int(norm))
            except ValueError:
                return None

    def apply(self, qs: QuerySet, included_values: List[str], excluded_values: List[str], request=None) -> QuerySet:
        q_obj = Q()
        any_inc = False

        for t in included_values:
            q = self._term_to_q(t)
            if q is None:
                continue
            any_inc = True
            q_obj |= q

        for t in excluded_values:
            q = self._term_to_q(t)
            if q is None:
                continue
            q_obj &= ~q

        if any_inc or excluded_values:
            return qs.filter(q_obj).distinct()
        return qs


class AuthorCategoryHandler(TokenHandler):
    name = 'category'
    allow_prefix = True
    sortable = False
    cat_re = re.compile(r"^[Pp#]((\d+(-\d*)?)|(-\d+))$", re.IGNORECASE)

    def detect(self, token: str) -> bool:
        if self.cat_re.match(token):
            return True
        norm = token[1:].lower() if token.startswith(('p', 'P', '#')) else token.lower()
        return norm in CATEGORIES_MAP

    def _term_to_categories(self, term: str):
        raw = term.strip()
        if not raw:
            return None

        if raw[0] in ('p', 'P', '#'):
            norm = raw[1:].strip().lower()
        else:
            norm = raw.strip().lower()

        if not norm:
            return None

        if norm in CATEGORIES_MAP:
            return list(CATEGORIES_MAP[norm])

        if '-' in norm:
            lo, hi = norm.split('-', 1)
            try:
                lo_v = int(lo) if lo.strip() != '' else None
                hi_v = int(hi) if hi.strip() != '' else None
            except ValueError:
                return None
            if lo_v is None and hi_v is None:
                return None
            if lo_v is None:
                return list(range(1, hi_v + 1))
            if hi_v is None:
                return None
            return list(range(lo_v, hi_v + 1))
        else:
            try:
                return [int(norm)]
            except ValueError:
                return None

    def apply(self, qs: QuerySet, included_values: List[str], excluded_values: List[str], request=None) -> QuerySet:
        q_obj = Q()
        any_inc = False

        for t in included_values:
            cats = self._term_to_categories(t)
            if not cats:
                continue
            any_inc = True
            q_obj |= Q(category_counters__category__in=cats)

        for t in excluded_values:
            cats = self._term_to_categories(t)
            if not cats:
                continue
            q_obj &= ~Q(category_counters__category__in=cats)

        if any_inc or excluded_values:
            return qs.filter(q_obj).distinct()
        return qs

    def detect_sort_name(self, sort_name: str) -> bool:
        s = sort_name.strip()
        if not s:
            return False
        if s.lower() == 'category':
            return True
        if s[0] in ('p', 'P', '#'):
            return True
        if s.lower() in CATEGORIES_MAP:
            return True
        if re.match(r'^\d+(-\d+)?$', s):
            return True
        return False

    def prepare_sort(self, qs: QuerySet, sort_name: str, direction: str, request=None):
        name = sort_name.strip()
        if not name:
            return qs, None

        if name.lower() == 'category':
            sub = AuthorCategoryCounter.objects.filter(author=OuterRef('pk')) \
                .values('author') \
                .annotate(cnt=Count('category', distinct=True)) \
                .values('cnt')[:1]
            qs = qs.annotate(unique_category_count=Coalesce(Subquery(sub, output_field=IntegerField()), Value(0)))
            return qs, 'unique_category_count'

        cats = self._term_to_categories(name)
        if not cats:
            return qs, None

        sanitized = re.sub(r'[^0-9a-zA-Z_]+', '_', name)
        field_name = f"catcount_{sanitized}"

        sub = AuthorCategoryCounter.objects.filter(author=OuterRef('pk'), category__in=cats) \
            .values('author') \
            .annotate(total=Coalesce(Sum('map_count'), Value(0))) \
            .values('total')[:1]

        qs = qs.annotate(**{
            field_name: Coalesce(Subquery(sub, output_field=IntegerField()), Value(0))
        })
        return qs, field_name


class AuthorTagHandler(TokenHandler):
    name = 'tag'
    allow_prefix = True
    sortable = False
    tag_re = re.compile(r'^\$[A-Za-z0-9_-]+$')

    def detect(self, token: str) -> bool:
        t = token.strip()
        return bool(self.tag_re.match(t))

    def apply(self, qs: QuerySet, included_values: List[str], excluded_values: List[str], request=None) -> QuerySet:
        q_obj = Q()
        any_inc = False
        for t in included_values:
            norm = t.lstrip('$').strip()
            if not norm:
                continue
            any_inc = True
            q_obj |= Q(tag_counters__tag=norm)

        for t in excluded_values:
            norm = t.lstrip('$').strip()
            if not norm:
                continue
            q_obj &= ~Q(tag_counters__tag=norm)

        if any_inc or excluded_values:
            return qs.filter(q_obj).distinct()
        return qs

    def detect_sort_name(self, sort_name: str) -> bool:
        s = sort_name.strip()
        if not s:
            return False
        if s.lower() == 'tag':
            return True
        if s.startswith('$'):
            return True
        return False

    def prepare_sort(self, qs: QuerySet, sort_name: str, direction: str, request=None):
        name = sort_name.strip()
        if not name:
            return qs, None

        if name.lower() == 'tag':
            sub = AuthorTagCounter.objects.filter(author=OuterRef('pk')) \
                .values('author') \
                .annotate(cnt=Count('tag', distinct=True)) \
                .values('cnt')[:1]
            qs = qs.annotate(unique_tag_count=Coalesce(Subquery(sub, output_field=IntegerField()), Value(0)))
            return qs, 'unique_tag_count'

        tag = name.lstrip('$')
        sanitized = re.sub(r'[^0-9a-zA-Z_]+', '_', tag)
        field_name = f"tagcount_{sanitized}"

        sub = AuthorTagCounter.objects.filter(author=OuterRef('pk'), tag=tag) \
            .values('author') \
            .annotate(total=Coalesce(Sum('map_count'), Value(0))) \
            .values('total')[:1]

        qs = qs.annotate(**{
            field_name: Coalesce(Subquery(sub, output_field=IntegerField()), Value(0))
        })
        return qs, field_name


class AuthorCountHandler(TokenHandler):
    name = 'count'
    sortable = True
    sort_key = 'total_maps'

    def prepare_sort(self, qs: QuerySet, sort_name: str, direction: str, request=None):
        sub = AuthorCategoryCounter.objects.filter(author=OuterRef('pk')) \
            .values('author') \
            .annotate(total=Coalesce(Sum('map_count'), Value(0))) \
            .values('total')[:1]

        qs = qs.annotate(total_maps=Coalesce(Subquery(sub, output_field=IntegerField()), Value(0)))
        return qs, 'total_maps'