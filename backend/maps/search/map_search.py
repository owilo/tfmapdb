import re
from typing import List, Tuple, Optional
from django.db.models import Q, QuerySet, F, Value, ExpressionWrapper, FloatField
from django.db.models.functions import Greatest

from pgvector.django import CosineDistance

from maps.models import Map
from maps.constants import CATEGORIES_MAP

from .search_base import TokenHandler, split_includes_excludes

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
    tag_re = re.compile(r'#(\d{4})$')

    def detect(self, token: str) -> bool:
        return bool(self.author_re.match(token))

    def _parse_author(self, raw: str):
        name = raw.lstrip('!')
        
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

    def apply(self, qs, tokens, request=None):
        if not tokens:
            return qs
        inc, exc = split_includes_excludes(tokens)
        q = Q()
        any_inc = False
        
        for token in inc:
            base_name, tag = self._parse_author(token)
            if tag:
                q |= Q(author__name=f"{base_name}#{tag}")
            else:
                q |= Q(author__name__regex=rf"^{re.escape(base_name)}#\d{{4}}$")
            any_inc = True
            
        for token in exc:
            base_name, tag = self._parse_author(token)
            if tag:
                q &= ~Q(author__name=f"{base_name}#{tag}")
            else:
                q &= ~Q(author__name__regex=rf"^{re.escape(base_name)}#\d{{4}}$")
            
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
        norm = token.lstrip('!')[1:].lower()
        return norm in CATEGORIES_MAP

    def apply(self, qs, tokens, request=None):
        if not tokens:
            return qs

        inc, exc = split_includes_excludes(tokens)

        def term_to_q(term):
            norm = term[1:].strip()
            if not norm:
                return None
            categories = CATEGORIES_MAP.get(norm.lower())
            sh = Q(category__in=categories) if categories else None
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

    
class TagHandler(TokenHandler):
    name = 'tag'
    allow_prefix = True
    sortable = False
    tag_re = re.compile(r'^!?\$[A-Za-z0-9_-]+$')

    def detect(self, token: str) -> bool:
        return bool(self.tag_re.match(token))

    def apply(self, qs: QuerySet, tokens: List[str], request=None) -> QuerySet:
        if not tokens:
            return qs

        inc, exc = split_includes_excludes(tokens)

        q_obj = Q()
        any_inc = False

        for t in inc:
            norm = t.lstrip('!').lstrip('$').strip()
            if not norm:
                continue
            any_inc = True
            q_obj |= Q(tags__contains=[norm])

        if not any_inc and not exc:
            return qs

        for t in exc:
            norm = t.lstrip('!').lstrip('$').strip()
            if not norm:
                continue
            q_obj &= ~Q(tags__contains=[norm])

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
            vec = Map.objects.filter(code=code_int).values_list('embedding', flat=True).get()
            if vec is None:
                continue
            parsed.append((vec, float(thresh), 'inc'))

        for raw in exc_raw:
            code_int, thresh = self._parse_code_and_threshold(raw)
            if code_int is None:
                continue
            vec = Map.objects.filter(code=code_int).values_list('embedding', flat=True).get()
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