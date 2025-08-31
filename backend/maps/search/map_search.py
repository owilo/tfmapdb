import re
from typing import List, Tuple, Optional
from django.db.models import Q, QuerySet, F, Value, ExpressionWrapper, FloatField
from django.db.models.functions import Greatest

from pgvector.django import CosineDistance

from maps.models import Map
from maps.constants import CATEGORIES_MAP

from .search_base import TokenHandler

class CodeHandler(TokenHandler):
    name = 'code'
    allow_prefix = True
    sortable = True
    sort_key = 'code'
    code_re = re.compile(r"^((@?\d+(-@?\d*)?)|(-@?\d+))$")

    def detect(self, token: str) -> bool:
        return bool(self.code_re.match(token))

    def apply(self, qs, included_values, excluded_values, request=None):
        def term_to_q(term):
            norm = term.lstrip('@').strip()
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
        
        # Process included values
        for t in included_values:
            q = term_to_q(t)
            if q is None:
                continue
            any_inc = True
            q_obj |= q

        # Process excluded values
        for t in excluded_values:
            q = term_to_q(t)
            if q is None:
                continue
            q_obj &= ~q

        if any_inc or excluded_values:
            return qs.filter(q_obj)
        return qs


class AuthorHandler(TokenHandler):
    name = 'author'
    allow_prefix = True
    sortable = True
    sort_key = 'author__name'
    author_re = re.compile(r'^\+?[A-Za-z]\w*(?:#\d{4})?$', re.IGNORECASE)
    tag_re = re.compile(r'#(\d{4})$')

    def detect(self, token: str) -> bool:
        return bool(self.author_re.match(token))

    def _parse_author(self, raw: str):
        name = raw
        
        match = self.tag_re.search(name)
        if match:
            base_name = name[:match.start()]
            tag = match.group(1)
        else:
            base_name = name
            tag = None

        if base_name.startswith('+') and len(base_name) > 1:
            normalized_base = '+' + base_name[1:2].upper() + base_name[2:].lower()
        elif base_name:
            normalized_base = base_name[0].upper() + base_name[1:].lower()
        else:
            normalized_base = base_name

        return normalized_base, tag

    def apply(self, qs, included_values, excluded_values, request=None):
        q = Q()
        any_inc = False
        
        # Process included values
        for token in included_values:
            base_name, tag = self._parse_author(token)
            if tag:
                q |= Q(author__name=f"{base_name}#{tag}")
            else:
                q |= Q(author__name__regex=rf"^{re.escape(base_name)}#\d{{4}}$")
            any_inc = True
            
        # Process excluded values
        for token in excluded_values:
            base_name, tag = self._parse_author(token)
            if tag:
                q &= ~Q(author__name=f"{base_name}#{tag}")
            else:
                q &= ~Q(author__name__regex=rf"^{re.escape(base_name)}#\d{{4}}$")
            
        if any_inc or excluded_values:
            return qs.filter(q)
        return qs


class CategoryHandler(TokenHandler):
    name = 'category'
    allow_prefix = True
    sortable = True
    sort_key = 'category'
    cat_re = re.compile(r"^[Pp#]((\d+(-\d*)?)|(-\d+))$", re.IGNORECASE)

    def detect(self, token: str) -> bool:
        if self.cat_re.match(token):
            return True
        norm = token[1:].lower() if token.startswith(('p', 'P', '#')) else token.lower()
        return norm in CATEGORIES_MAP

    def apply(self, qs, included_values, excluded_values, request=None):
        def term_to_q(term):
            if term.startswith(('p', 'P', '#')):
                norm = term[1:].strip().lower()
            else:
                norm = term.strip().lower()

            if not norm:
                return None

            if norm in CATEGORIES_MAP:
                categories = CATEGORIES_MAP[norm]
                return Q(category__in=categories)
                
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
        
        # Process included values
        for t in included_values:
            q = term_to_q(t)
            if q is None:
                continue
            any_inc = True
            q_obj |= q
            
        # Process excluded values
        for t in excluded_values:
            q = term_to_q(t)
            if q is None:
                continue
            q_obj &= ~q

        if any_inc or excluded_values:
            return qs.filter(q_obj)
        return qs

    
class TagHandler(TokenHandler):
    name = 'tag'
    allow_prefix = True
    sortable = False
    tag_re = re.compile(r'^\$[A-Za-z0-9_-]+$')

    def detect(self, token: str) -> bool:
        return bool(self.tag_re.match(token))

    def apply(self, qs: QuerySet, included_values: List[str], excluded_values: List[str], request=None) -> QuerySet:
        q_obj = Q()
        any_inc = False

        # Process included values
        for t in included_values:
            norm = t.lstrip('$').strip()
            if not norm:
                continue
            any_inc = True
            q_obj |= Q(tags__contains=[norm])

        # Process excluded values
        for t in excluded_values:
            norm = t.lstrip('$').strip()
            if not norm:
                continue
            q_obj &= ~Q(tags__contains=[norm])

        if any_inc or excluded_values:
            return qs.filter(q_obj)
        return qs


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

        code_txt = val_part.lstrip('@').strip()
        try:
            code_int = int(code_txt)
        except Exception:
            return None, thresh
        return code_int, thresh

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

    def apply(self, qs: QuerySet, included_values: List[str], excluded_values: List[str], request=None) -> QuerySet:
        parsed = []
        
        # Process included values
        for raw in included_values:
            code_int, thresh = self._parse_code_and_threshold(raw)
            if code_int is None:
                continue
            vec = Map.objects.filter(code=code_int).values_list('embedding', flat=True).first()
            if vec is None:
                continue
            parsed.append((vec, float(thresh), 'inc'))

        # Process excluded values
        for raw in excluded_values:
            code_int, thresh = self._parse_code_and_threshold(raw)
            if code_int is None:
                continue
            vec = Map.objects.filter(code=code_int).values_list('embedding', flat=True).first()
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