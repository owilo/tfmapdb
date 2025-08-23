import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from collections import defaultdict

from django.db.models import Q, Count, Sum, IntegerField, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.postgres.aggregates import ArrayAgg

from rest_framework import views, generics, response, status
from django.db.models import Sum, Count
from rest_framework import generics

from .models import Map, Author, AuthorCategoryCounter, AuthorTagCounter
from .serializers import *
from .constants import *
from .utils import xml_to_image

map_code_regex = re.compile(r"^!?((@?\d+(-@?\d*)?)|(-@?\d+))$")
author_regex = re.compile(r'^!?\+?[A-Za-z]\w*(?:#\d{4})?$', re.IGNORECASE)
category_regex = re.compile(r"^!?[Pp#]((\d+(-\d*)?)|(-\d+))$", re.IGNORECASE)

# TODO Too many regexes, refactor later
category_high_regex = re.compile(r"^!?[Pp#]h(igh)?$", re.IGNORECASE)
category_low_regex = re.compile(r"^!?[Pp#]l(ow)?$", re.IGNORECASE)
category_disc_regex = re.compile(r"^!?[Pp#]d(isc(ussion)?)?$", re.IGNORECASE)
category_standard_regex = re.compile(r"^!?[Pp#]s(tandard)?$", re.IGNORECASE)
category_unused_regex = re.compile(r"^!?[Pp#]u(nused)?$", re.IGNORECASE)
category_bootcamp_regex = re.compile(r"^!?[Pp#]b(c|ootcamp)?$", re.IGNORECASE)

tag_regex = re.compile(r'#\d{4}$')

# TODO Split in multiple files
class MapListView(generics.ListAPIView):
    serializer_class = MinimalMapSerializer
    queryset = Map.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.GET

        raw = params.get('s', '').strip()
        if not raw:
            sort = params.get('sort', 'desc').lower()
            if sort == 'asc':
                return qs.order_by('code')
            return qs.order_by('-code')

        items = re.split(r'\s+', raw)

        codes_tokens = []
        authors_tokens = []
        categories_tokens = []

        for it in items:
            if not it:
                continue
            if map_code_regex.match(it):
                codes_tokens.append(it)
            elif category_regex.match(it) or category_high_regex.match(it) or category_low_regex.match(it) or category_disc_regex.match(it) or category_standard_regex.match(it) or category_unused_regex.match(it) or category_bootcamp_regex.match(it):
                categories_tokens.append(it)
            elif author_regex.match(it):
                authors_tokens.append(it)
            else:
                continue

        def split_includes_excludes(tokens):
            inc, exc = [], []
            for t in tokens:
                if t.startswith('!'):
                    exc.append(t[1:])
                else:
                    inc.append(t)
            return inc, exc

        def build_range_q_for_tokens(field_name, tokens, is_category=False):
            if not tokens:
                return None

            inc_terms, exc_terms = split_includes_excludes(tokens)

            def term_to_q(term):
                norm = term.lstrip('@Pp#')
                if not norm:
                    return None
                
                if norm in ['h', 'high']:
                    return Q(category__in=CATEGORIES_HIGH)
                if norm in ['l', 'low']:
                    return Q(category__in=CATEGORIES_LOW)
                if norm in ['d', 'disc', 'discussion']:
                    return Q(category__in=CATEGORIES_DISC)
                if norm in ['s', 'standard']:
                    return Q(category__in=CATEGORIES_STANDARD)
                if norm in ['u', 'unused']:
                    return Q(category__in=CATEGORIES_UNUSED)

                if '-' in norm:
                    lo, hi = norm.split('-', 1)
                    lo = lo.strip()
                    hi = hi.strip()
                    q_sub = Q()
                    if lo != '':
                        try:
                            q_sub &= Q(**{f"{field_name}__gte": int(lo)})
                        except ValueError:
                            return None
                    if hi != '':
                        try:
                            q_sub &= Q(**{f"{field_name}__lte": int(hi)})
                        except ValueError:
                            return None
                    return q_sub
                else:
                    try:
                        return Q(**{field_name: int(norm)})
                    except ValueError:
                        return None

            q_obj = Q()
            any_inc = False
            for t in inc_terms:
                q = term_to_q(t)
                if q is None:
                    continue
                any_inc = True
                q_obj |= q

            if not any_inc and not exc_terms:
                return None

            for t in exc_terms:
                q = term_to_q(t)
                if q is None:
                    continue
                q_obj &= ~q

            return q_obj

        def format_author_name(name):
            name = a.capitalize()
            if not tag_regex.search(name):
                return f'{name}#0000'
            return name

        # Authors
        if authors_tokens:
            inc_authors, exc_authors = split_includes_excludes(authors_tokens)
            author_q = Q()
            any_inc = False
            for a in inc_authors:
                name = format_author_name(a)
                author_q |= Q(author__name=name)
                any_inc = True

            for a in exc_authors:
                name = format_author_name(a)
                author_q &= ~Q(author__name=name)

            if any_inc or exc_authors:
                qs = qs.filter(author_q)

        # Map codes
        codes_q = build_range_q_for_tokens('code', codes_tokens)
        if codes_q is not None:
            qs = qs.filter(codes_q)

        # Categories
        cats_q = build_range_q_for_tokens('category', categories_tokens, is_category=True)
        if cats_q is not None:
            qs = qs.filter(cats_q)

        # Sorting
        # TODO Allow sorting by author, category, etc.
        sort = params.get('sort', 'desc').lower()
        if sort == 'asc':
            qs = qs.order_by('code')
        else:
            qs = qs.order_by('-code')

        return qs

class MapDetailView(generics.RetrieveAPIView):
    queryset = Map.objects.select_related('author')
    serializer_class = MapSerializer
    lookup_field = 'code'

class MapImageView(views.APIView):
    def get(self, request, code, format=None):
        map_obj = get_object_or_404(Map, code=code)

        try:
            scale = float(request.GET.get('scale', 1.0))
        except ValueError:
            scale = 1.0

        if not (0 < scale <= 1):
            scale = 1.0

        xml_text = map_obj.xml or ''

        map_data = extract_map_data(xml_text)
        image = xml_to_image(xml_text, (map_data["length"], map_data["height"]), scale)
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return HttpResponse(buffer, content_type='image/png')

class AuthorListView(generics.ListAPIView):
    serializer_class = MinimalAuthorSerializer
    pagination_class = None

    def get_queryset(self):
        raw = self.request.GET.get('s', '').strip()

        qs = Author.objects.annotate(
            total_maps=Coalesce(
                Sum('category_counters__map_count'),
                Value(0, output_field=IntegerField())
            ),

            total_high_perms=Coalesce(
                Sum(
                    'category_counters__map_count',
                    filter=Q(category_counters__category__in=CATEGORIES_HIGH)
                ),
                Value(0, output_field=IntegerField())
            ),

            category_tags=ArrayAgg(
                'category_counters__category',
                filter=Q(category_counters__category__in=CATEGORIES_TAG),
                distinct=True
            ),
        )

        if raw:
            qs = qs.filter(name__icontains=raw)

        return qs.order_by('name')

class AuthorProfileView(generics.RetrieveAPIView):
    queryset = Author.objects.all()
    lookup_field = 'name'
    serializer_class = AuthorDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        author = self.get_object()

        permed_set = set(CATEGORIES_PERMED)

        high_set = set(CATEGORIES_HIGH)

        acc_qs = AuthorCategoryCounter.objects.filter(author=author)

        total_maps = acc_qs.aggregate(total=Sum('map_count'))['total'] or 0

        high_maps = acc_qs.filter(category__in=high_set).aggregate(total=Sum('map_count'))['total'] or 0

        permed_maps = acc_qs.filter(category__in=permed_set).aggregate(total=Sum('map_count'))['total'] or 0

        categories_qs = acc_qs.filter(map_count__gt=0).values('category', 'map_count').order_by('category')

        categories = [
            {
                'category': int(row['category']),
                'map_count': int(row['map_count']),
                'permanent': (row['category'] in permed_set)
            }
            for row in categories_qs
        ]

        last_exported = list(
            Map.objects.filter(author=author)
            .order_by('-code')
            .values('code', 'category')[:10]
        )

        last_permed = list(
            Map.objects.filter(author=author, category__in=permed_set)
            .order_by('-code')
            .values('code', 'category')[:10]
        )   

        payload = {
            "total_maps": int(total_maps),
            "high_maps": int(high_maps),
            "permed_maps": int(permed_maps),
            "categories": categories,
            "last_exported": last_exported,
            "last_permed": last_permed,
        }

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        return response.Response(serializer.data)

class CategoriesListView(generics.ListAPIView):
    serializer_class = CategoriesListSerializer
    pagination_class = None

    def get_queryset(self):
        qs = (
            AuthorCategoryCounter.objects
            .values('category')
            .annotate(
                maps_count=Sum('map_count'),
                authors_count=Count('author', distinct=True)
            )
            .order_by('category')
        )
        return qs

class TagsListView(generics.ListAPIView):
    serializer_class = TagsListSerializer
    pagination_class = None

    def get_queryset(self):
        qs = (
            AuthorTagCounter.objects
            .values('tag')
            .annotate(
                maps_count=Sum('map_count'),
                authors_count=Count('author', distinct=True)
            )
            .order_by('tag')
        )
        return qs
    
class TagDataView(views.APIView):

    def get(self, request, id, filter_type, *args, **kwargs):
        if filter_type == 'category':
            category = id

            agg = AuthorCategoryCounter.objects.filter(category=category).aggregate(
                total_maps=Coalesce(Sum('map_count'), 0)
            )
            total_maps = agg['total_maps'] or 0
            total_authors = AuthorCategoryCounter.objects.filter(
                category=category, map_count__gt=0
            ).count()

            maps_qs = (
                Map.objects
                .filter(category=category)
                .select_related('author')
                .order_by('-code')[:10]
            )

        elif filter_type == 'tag':
            tag = id

            # Check if it exists because of merged logic as intergers are a valid tag but points to a category. Not problematic anyway.
            tag_exists = (
                AuthorTagCounter.objects.filter(tag=tag).exists()
                or Map.objects.filter(tags__contains=[tag]).exists()
            )
            if not tag_exists:
                return response.Response(
                    {"detail": f"Tag '{tag}' not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            agg = AuthorTagCounter.objects.filter(tag=tag).aggregate(
                total_maps=Coalesce(Sum('map_count'), 0)
            )
            total_maps = agg['total_maps'] or 0
            total_authors = AuthorTagCounter.objects.filter(
                tag=tag, map_count__gt=0
            ).count()

            maps_qs = (
                Map.objects
                .filter(tags__contains=[tag])
                .select_related('author')
                .order_by('-code')[:10]
            )

        else:
            return response.Response({"detail": "invalid filter_type"}, status=400)

        last_permed_data = [
            {
                "code": m.code,
                "author": m.author.name if m.author else None,
                "category": m.category,
            }
            for m in maps_qs
        ]

        serializer = MapAuthorSummarySerializer(last_permed_data, many=True)
        return response.Response({
            "total_maps": int(total_maps),
            "total_authors": int(total_authors),
            "last_permed": serializer.data,
        })

class LeaderboardView(views.APIView):
    def get(self, request, *args, **kwargs):

        def group_distinct_counts(rows, count_key, top_k):
            rows_sorted = sorted(rows, key=lambda r: (-r[count_key], r['id']))

            buckets = []
            seen_counts = 0
            last_count = None

            for r in rows_sorted:
                cnt = r[count_key]
                if cnt == 0:
                    continue
                if last_count is None or cnt != last_count:
                    if seen_counts >= top_k:
                        break
                    buckets.append([{'id': r['id'], 'name': r['name'], 'count': cnt}])
                    seen_counts += 1
                    last_count = cnt
                else:
                    buckets[-1].append({'id': r['id'], 'name': r['name'], 'count': cnt})
            return buckets

        result = {}

        # Per-category top-5
        for cat in CATEGORIES_HIGH:
            qs = (
                AuthorCategoryCounter.objects
                .filter(category=cat)
                .select_related('author')
                .values('author_id', 'author__name', 'map_count')
                .order_by('-map_count', 'author_id')
            )
            rows = [{'id': r['author_id'], 'name': r['author__name'], 'count': r['map_count']} for r in qs]
            buckets = group_distinct_counts(rows, count_key='count', top_k=5)
            if buckets:
                result[str(cat)] = buckets

        # 2) "all": Top-5 authors by sum(map_count) across high categories
        qs_all = (
            AuthorCategoryCounter.objects
            .filter(category__in=CATEGORIES_HIGH)
            .values('author_id', 'author__name')
            .annotate(count=Sum('map_count'))
            .order_by('-count', 'author_id')
        )

        rows_all = [
            {'id': r['author_id'], 'name': r['author__name'], 'count': r['count'] or 0}
            for r in qs_all
        ]

        result['all'] = group_distinct_counts(rows_all, 'count', top_k=5)

        # 3) "cat": Top-5 authors by number of distinct high categories they have
        qs_cat = (
            AuthorCategoryCounter.objects
            .filter(category__in=CATEGORIES_HIGH)
            .values('author_id', 'author__name')
            .annotate(count=Count('category', distinct=True))
            .order_by('-count', 'author_id')
        )

        rows_cat = [
            {'id': r['author_id'], 'name': r['author__name'], 'count': r['count'] or 0}
            for r in qs_cat
        ]
        result['cat'] = group_distinct_counts(rows_cat, 'count', top_k=5)

        # 4) "total": Top-10 authors by total maps across all categories
        qs_total = (
            AuthorCategoryCounter.objects
            .values('author_id', 'author__name')
            .annotate(count=Sum('map_count'))
            .order_by('-count', 'author_id')
        )

        rows_total = [
            {'id': r['author_id'], 'name': r['author__name'], 'count': r['count'] or 0}
            for r in qs_total
        ]
        result['total'] = group_distinct_counts(rows_total, 'count', top_k=10)

        return response.Response(result)
