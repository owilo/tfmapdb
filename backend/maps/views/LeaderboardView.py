from django.db.models import Count, Sum

from rest_framework import views, response

from maps.models import AuthorCategoryCounter
from maps.serializers import *
from maps.constants import *

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
