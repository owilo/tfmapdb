import re
import json
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
        return bool(self.cat_re.match(token))

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
            norm = term.lstrip('Pp#@').strip()
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

    def __init__(self, default_threshold: float = 0.85, aggregation: str = 'avg'):
        self.default_threshold = float(default_threshold)
        assert aggregation in ('max', 'avg'), "aggregation must be 'max' or 'avg'"
        self.aggregation = aggregation

    def detect(self, token: str) -> bool:
        return False

    def _resolve_anchor_vector_from_code(self, code_token: str):
        code = code_token.lstrip('@!')
        try:
            code_int = int(code)
        except ValueError:
            return None
        try:
            m = Map.objects.only('embedding').get(code=code_int)
        except ObjectDoesNotExist:
            return None
        return m.embedding

    def _parse_value_and_threshold(self, raw_val: str):
        """
        Parse '@123', '@123~0.9', 'vec:[..]', 'vec:[..]~0.8', '[..]~0.7'
        Returns (vec_list_or_None, threshold_float)
        """
        if '~' in raw_val:
            val_part, thresh_part = raw_val.rsplit('~', 1)
            try:
                thresh = float(thresh_part)
            except Exception:
                thresh = self.default_threshold
        else:
            val_part = raw_val
            thresh = self.default_threshold

        val_part = val_part.strip()
        vec = None

        if val_part.startswith('vec:'):
            vec_text = val_part.split(':', 1)[1].strip()
            try:
                vec = json.loads(vec_text)
            except Exception:
                """try:
                    vec = eval(vec_text)  # Avoid in prod
                except Exception:"""
                vec = None
        elif val_part.startswith('['):
            try:
                vec = json.loads(val_part)
            except Exception:
                try:
                    vec = eval(val_part)
                except Exception:
                    vec = None
        else:
            vec = self._resolve_anchor_vector_from_code(val_part)

        try:
            thresh = float(thresh)
        except Exception:
            thresh = self.default_threshold
        thresh = max(0.0, min(1.0, thresh))

        if vec is None:
            return None, thresh
        return list(vec), thresh

    def _annotate_similarities(self, qs, vecs_and_thresholds):
        """
        Annotate the queryset with per-anchor similarity fields.
        Returns (qs, similarity_field_names, any_threshold_positive, filters_q)
        """
        similarity_field_names = []
        filters_q = Q()
        any_threshold_positive = False

        for idx, (vec, thresh) in enumerate(vecs_and_thresholds):
            dist_name = f"sim_dist_{idx}"
            sim_name = f"similarity_{idx}"
            qs = qs.annotate(**{dist_name: CosineDistance('embedding', vec)})
            qs = qs.annotate(**{
                sim_name: ExpressionWrapper(Value(1.0) - F(dist_name), output_field=FloatField())
            })
            similarity_field_names.append(sim_name)
            if thresh > 0.0:
                any_threshold_positive = True
                filters_q |= Q(**{f"{sim_name}__gte": float(thresh)})

        if len(similarity_field_names) == 1:
            qs = qs.annotate(similarity=F(similarity_field_names[0]))
        else:
            if self.aggregation == 'max':
                greatest_expr = Greatest(*[F(name) for name in similarity_field_names])
                qs = qs.annotate(max_similarity=greatest_expr)
                qs = qs.annotate(similarity=F('max_similarity'))
            else: # avg
                total = None
                for name in similarity_field_names:
                    if total is None:
                        total = F(name)
                    else:
                        total = total + F(name)
                avg_expr = ExpressionWrapper(total / Value(len(similarity_field_names)), output_field=FloatField())
                qs = qs.annotate(avg_similarity=avg_expr)
                qs = qs.annotate(similarity=F('avg_similarity'))

        return qs, similarity_field_names, any_threshold_positive, filters_q

    def apply(self, qs, tokens, request=None):
        if not tokens:
            return qs

        vecs_and_thresholds = []
        for raw in tokens:
            vec, thresh = self._parse_value_and_threshold(raw)
            if vec is None:
                continue
            vecs_and_thresholds.append((vec, thresh))

        if not vecs_and_thresholds:
            return qs

        qs, sim_field_names, any_threshold_positive, filters_q = self._annotate_similarities(qs, vecs_and_thresholds)

        if any_threshold_positive:
            qs = qs.filter(filters_q)

        return qs

    def ensure_sort_annotation(self, qs: QuerySet, request=None) -> QuerySet:
        """
        If user wants to sort by similarity but did not pass sim: tokens,
        accept GET hints: ?sim_anchor=7411140 or ?sim_vec=[...]
        Annotate single similarity field (similarity) so sorting works.
        """
        # prefer sim_vec then sim_anchor
        sim_vec_txt = None
        sim_anchor = None
        if request is not None:
            sim_vec_txt = request.GET.get('sim_vec')
            sim_anchor = request.GET.get('sim_anchor')

        vec = None
        if sim_vec_txt:
            try:
                vec = json.loads(sim_vec_txt)
            except Exception:
                try:
                    vec = eval(sim_vec_txt)
                except Exception:
                    vec = None
        elif sim_anchor:
            vec = self._resolve_anchor_vector_from_code(sim_anchor)

        if vec is None:
            return qs

        qs = qs.annotate(sim_distance=CosineDistance('embedding', list(vec)))
        qs = qs.annotate(similarity=ExpressionWrapper(Value(1.0) - F('sim_distance'), output_field=FloatField()))
        return qs


SORT_RE = re.compile(r'^(?P<name>[A-Za-z_]+)-(?P<dir>asc|desc)$', re.IGNORECASE)

class SearchEngine:
    def __init__(self, handlers: List[TokenHandler]):
        self.handlers = handlers
        self.handlers_by_name = {h.name: h for h in handlers}

    SORT_RE = re.compile(r'^(?P<name>[A-Za-z_]+)-(?P<dir>asc|desc)$', re.IGNORECASE)

    def parse(self, raw: str):
        """
        Returns (grouped_tokens, sort_specs)
        grouped_tokens: {handler_name: [val, ...], ...}
        sort_specs: list of (name, dir) tuples in the order encountered
        """
        grouped = {name: [] for name in self.handlers_by_name.keys()}
        sort_specs = []
        if not raw:
            return grouped, sort_specs

        tokens = [t for t in re.split(r'\s+', raw.strip()) if t]
        for tok in tokens:
            if tok.lower().startswith('sort:'):
                raw_sort = tok[5:]
                # Support comma-separated sorts in a single token: sort:author-asc,sim-desc
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

            # Try detection in handler order when no specified prefix
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
                # Comma-separated sorts
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