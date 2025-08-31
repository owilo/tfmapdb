import re
import math
from typing import List, Dict, Tuple, Optional
from django.db.models import Q, QuerySet, F, Value, ExpressionWrapper, FloatField
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.functions import Greatest

from pgvector.django import CosineDistance

from maps.models import Map
from maps.constants import (
    CATEGORIES_HIGH,
    CATEGORIES_LOW,
    CATEGORIES_DISC,
    CATEGORIES_STANDARD,
    CATEGORIES_UNUSED,
)

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

    def apply(self, qs: QuerySet, values: List[str], request=None) -> QuerySet:
        """Apply filtering for these token values and return modified queryset."""
        return qs

    def ensure_sort_annotation(self, qs: QuerySet, request=None) -> QuerySet:
        """
        Optionally annotate qs with whatever computed fields sorting requires.
        E.g. SimilarityHandler will annotate 'similarity'.
        Called during sorting phase even if handler didn't get tokens.
        """
        return qs

def split_includes_excludes(tokens: List[str]) -> Tuple[List[str], List[str]]:
    inc, exc = [], []
    for t in tokens:
        if not t:
            continue
        if t.startswith('!'):
            exc.append(t[1:])
        else:
            inc.append(t)
    return inc, exc

class CodeHandler(TokenHandler):
    name = 'code'
    allow_prefix = True
    sortable = True
    sort_key = 'code'
    code_re = re.compile(r"^!?((@?\d+(-@?\d*)?)|(-@?\d+))$")

    def detect(self, token: str) -> bool:
        return bool(self.code_re.match(token))

    def apply(self, qs, tokens, request=None):
        if not tokens:
            return qs
        inc, exc = split_includes_excludes(tokens)

        def term_to_q(term):
            norm = term.lstrip('@Pp#').strip()
            if not norm:
                return None
            if '-' in norm:
                lo, hi = norm.split('-', 1)
                q = Q()
                if lo.strip() != '':
                    try:
                        q &= Q(code__gte=int(lo.strip()))
                    except ValueError:
                        return None
                if hi.strip() != '':
                    try:
                        q &= Q(code__lte=int(hi.strip()))
                    except ValueError:
                        return None
                return q
            else:
                try:
                    return Q(code=int(norm))
                except ValueError:
                    return None

        q_obj = Q()
        any_inc = False
        for t in inc:
            q = term_to_q(t)
            if q is None:
                continue
            any_inc = True
            q_obj |= q

        if not any_inc and not exc:
            return qs

        for t in exc:
            q = term_to_q(t)
            if q is None:
                continue
            q_obj &= ~q

        return qs.filter(q_obj)


class AuthorHandler(TokenHandler):
    name = 'author'
    allow_prefix = True
    sortable = True
    sort_key = 'author__name'
    author_re = re.compile(r'^!?\+?[A-Za-z]\w*(?:#\d{4})?$', re.IGNORECASE)
    tag_re = re.compile(r'#\d{4}$')

    def detect(self, token: str) -> bool:
        return bool(self.author_re.match(token))

    def _norm(self, raw: str) -> str:
        name = raw.lstrip('!+')
        name = name.capitalize()
        if not self.tag_re.search(name):
            name = f"{name}#0000"
        return name

    def apply(self, qs, tokens, request=None):
        if not tokens:
            return qs
        inc, exc = split_includes_excludes(tokens)
        q = Q()
        any_inc = False
        for a in inc:
            q |= Q(author__name=self._norm(a))
            any_inc = True
        for a in exc:
            q &= ~Q(author__name=self._norm(a))
        if any_inc or exc:
            return qs.filter(q)
        return qs


class CategoryHandler(TokenHandler):
    name = 'category'
    allow_prefix = True
    sortable = True
    sort_key = 'category'
    cat_re = re.compile(r"^!?[Pp#]((\d+(-\d*)?)|(-\d+))$", re.IGNORECASE)

    def detect(self, token: str) -> bool:
        if self.cat_re.match(token):
            return True
        norm = token.lstrip('!Pp#').lower()
        if norm in ('h','high','l','low','d','disc','discussion','s','standard','u','unused'):
            return True
        return False


    def apply(self, qs, tokens, request=None):
        if not tokens:
            return qs

        def shorthand_q(norm: str):
            n = norm.lower()
            if n in ('h', 'high'):
                return Q(category__in=CATEGORIES_HIGH)
            if n in ('l', 'low'):
                return Q(category__in=CATEGORIES_LOW)
            if n in ('d', 'disc', 'discussion'):
                return Q(category__in=CATEGORIES_DISC)
            if n in ('s', 'standard'):
                return Q(category__in=CATEGORIES_STANDARD)
            if n in ('u', 'unused'):
                return Q(category__in=CATEGORIES_UNUSED)
            return None

        inc, exc = split_includes_excludes(tokens)

        def term_to_q(term):
            norm = term.lstrip('Pp#').strip()
            if not norm:
                return None
            sh = shorthand_q(norm)
            if sh is not None:
                return sh
            if '-' in norm:
                lo, hi = norm.split('-', 1)
                q_ = Q()
                if lo.strip() != '':
                    try:
                        q_ &= Q(category__gte=int(lo.strip()))
                    except ValueError:
                        return None
                if hi.strip() != '':
                    try:
                        q_ &= Q(category__lte=int(hi.strip()))
                    except ValueError:
                        return None
                return q_
            else:
                try:
                    return Q(category=int(norm))
                except ValueError:
                    return None

        q_obj = Q()
        any_inc = False
        for t in inc:
            q = term_to_q(t)
            if q is None:
                continue
            any_inc = True
            q_obj |= q
        if not any_inc and not exc:
            return qs
        for t in exc:
            q = term_to_q(t)
            if q is None:
                continue
            q_obj &= ~q
        return qs.filter(q_obj)


class SimilarityHandler(TokenHandler):
    name = 'sim'
    allow_prefix = True
    sortable = True
    sort_key = 'similarity'

    def __init__(self, default_threshold: float = 0.85, aggregation: str = 'max'):
        self.default_threshold = float(default_threshold)
        assert aggregation in ('max', 'avg'), "aggregation must be 'max' or 'avg'"
        self.aggregation = aggregation

    def detect(self, token: str) -> bool:
        # Require explicit prefix sim so no free-form detection.
        return False

    def _parse_code_and_threshold(self, raw: str) -> Tuple[Optional[int], float]:
        raw = raw.strip()
        if '~' in raw:
            val_part, thresh_part = raw.rsplit('~', 1)
            try:
                thresh = float(thresh_part)
            except Exception:
                thresh = self.default_threshold
        else:
            val_part = raw
            thresh = self.default_threshold

        try:
            thresh = float(thresh)
        except Exception:
            thresh = self.default_threshold
        thresh = max(0.0, min(1.0, thresh))

        code_txt = val_part.lstrip('@!').strip()
        try:
            code_int = int(code_txt)
        except Exception:
            return None, thresh
        return code_int, thresh

    def _get_embedding_for_code(self, code_int: int):
        try:
            vec = Map.objects.filter(code=code_int).values_list('embedding', flat=True).get()
        except ObjectDoesNotExist:
            return None

        if vec is None:
            return None

        try:
            if hasattr(vec, 'tolist'):
                vec = vec.tolist()
            elif isinstance(vec, (bytes, bytearray, memoryview)):
                # Defensive, unlikely for pgvector
                vec = list(vec)
            elif not isinstance(vec, (list, tuple)):
                vec = list(vec)
        except TypeError:
            return None

        validated = []
        for x in vec:
            try:
                fx = float(x)
            except Exception:
                return None
            if math.isnan(fx) or math.isinf(fx):
                return None
            validated.append(fx)
        return validated

    def _annotate_similarities(self, qs: QuerySet, vecs: List[List[float]]):
        similarity_field_names = []
        for idx, vec in enumerate(vecs):
            dist_name = f"sim_dist_{idx}"
            sim_name = f"similarity_{idx}"
            qs = qs.annotate(**{dist_name: CosineDistance('embedding', vec)})
            qs = qs.annotate(**{
                sim_name: ExpressionWrapper(Value(1.0) - F(dist_name), output_field=FloatField())
            })
            similarity_field_names.append(sim_name)

        if len(similarity_field_names) == 1:
            qs = qs.annotate(similarity=F(similarity_field_names[0]))
        else:
            if self.aggregation == 'max':
                qs = qs.annotate(similarity=Greatest(*[F(n) for n in similarity_field_names]))
            else:  # avg
                total = None
                for name in similarity_field_names:
                    if total is None:
                        total = F(name)
                    else:
                        total = total + F(name)
                avg_expr = ExpressionWrapper(total / Value(len(similarity_field_names)), output_field=FloatField())
                qs = qs.annotate(similarity=avg_expr)

        return qs, similarity_field_names

    def apply(self, qs: QuerySet, tokens: List[str], request=None) -> QuerySet:
        if not tokens:
            return qs

        inc_raw, exc_raw = split_includes_excludes(tokens)

        parsed = []
        for raw in inc_raw:
            code_int, thresh = self._parse_code_and_threshold(raw)
            if code_int is None:
                continue
            vec = self._get_embedding_for_code(code_int)
            if vec is None:
                continue
            parsed.append((vec, float(thresh), 'inc'))

        for raw in exc_raw:
            code_int, thresh = self._parse_code_and_threshold(raw)
            if code_int is None:
                continue
            vec = self._get_embedding_for_code(code_int)
            if vec is None:
                continue
            parsed.append((vec, float(thresh), 'exc'))

        if not parsed:
            return qs

        vecs = [item[0] for item in parsed]
        qs, sim_field_names = self._annotate_similarities(qs, vecs)

        inc_q = Q()
        exc_q = Q()
        for idx, (_, thresh, kind) in enumerate(parsed):
            fld = f"{sim_field_names[idx]}__gte"
            if kind == 'inc':
                inc_q |= Q(**{fld: float(thresh)})
            else:
                exc_q |= Q(**{fld: float(thresh)})

        if inc_q:
            qs = qs.filter(inc_q)

        if exc_q:
            qs = qs.exclude(exc_q)

        return qs

    def ensure_sort_annotation(self, qs: QuerySet, request=None) -> QuerySet:
        return qs


SORT_RE = re.compile(r'^(?P<name>[A-Za-z_]+)-(?P<dir>asc|desc)$', re.IGNORECASE)

class SearchEngine:
    def __init__(self, handlers: List[TokenHandler]):
        self.handlers = handlers
        self.handlers_by_name = {h.name: h for h in handlers}

    def parse(self, raw: str):
        grouped = {name: [] for name in self.handlers_by_name.keys()}
        sort_specs = []
        if not raw:
            return grouped, sort_specs

        tokens = [t for t in re.split(r'\s+', raw.strip()) if t]
        for tok in tokens:
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

            if ':' in tok:
                prefix, val = tok.split(':', 1)
                prefix = prefix.lower()
                if prefix in self.handlers_by_name:
                    grouped[prefix].append(val)
                continue

            for h in self.handlers:
                if h.detect(tok):
                    grouped[h.name].append(tok)
                    break
        return grouped, sort_specs


    def apply(self, qs: QuerySet, grouped_tokens: Dict[str, List[str]], sort_specs: Optional[List[Tuple[str,str]]] = None, request=None) -> QuerySet:
        for h in self.handlers:
            toks = grouped_tokens.get(h.name) or []
            if toks:
                qs = h.apply(qs, toks, request=request)

        specs = list(sort_specs or [])
        if not specs and request is not None:
            sort_param = request.GET.get('sort')
            if sort_param:
                for part in [p.strip() for p in sort_param.split(',') if p.strip()]:
                    m = SORT_RE.match(part)
                    if m:
                        specs.append((m.group('name').lower(), m.group('dir').lower()))

        if specs:
            order_fields = []
            for name, dir_ in specs:
                if name in self.handlers_by_name:
                    h = self.handlers_by_name[name]
                    if not h.sortable:
                        continue
                    qs = h.ensure_sort_annotation(qs, request=request)
                    key = h.sort_key or name

                    if key == "similarity" and "similarity" not in qs.query.annotations:
                        continue

                    if dir_ == 'asc':
                        order_fields.append(key)
                    else:
                        order_fields.append(f"-{key}")
                else:
                    continue

            if order_fields:
                if 'code' not in [f.lstrip('-') for f in order_fields]:
                    order_fields.append('-code')
                return qs.order_by(*order_fields)
            
        if 'similarity' in qs.query.annotations:
            return qs.order_by('-similarity', '-code')

        return qs.order_by('-code')