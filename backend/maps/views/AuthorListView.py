# AuthorListView.py (replaced content)

from django.db.models import Q, Sum, IntegerField, Value, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.contrib.postgres.aggregates import ArrayAgg

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from maps.models import Author, AuthorCategoryCounter
from maps.serializers import MinimalAuthorSerializer
from maps.constants import *
from maps.pagination import KeysetPagination

from maps.search.author_search import (
    AuthorCodeHandler,
    AuthorCategoryHandler,
    AuthorTagHandler,
    AuthorNameHandler,
    AuthorCountHandler,
)
from maps.search.search_base import SearchEngine

AUTHOR_SEARCH_ENGINE = SearchEngine(
    handlers=[
        AuthorCodeHandler(),
        AuthorCategoryHandler(),
        AuthorTagHandler(),
        AuthorNameHandler(),
        AuthorCountHandler(),
    ],
    fallback_order=['name']
)

class AuthorListView(generics.ListAPIView):
    serializer_class = MinimalAuthorSerializer
    pagination_class = KeysetPagination

    def list(self, request, *args, **kwargs):
        raw = request.GET.get('s', '').strip()
        grouped_includes, grouped_excludes, sort_specs = AUTHOR_SEARCH_ENGINE.parse(raw)

        qs = Author.objects.all()

        total_sub = AuthorCategoryCounter.objects.filter(author=OuterRef('pk')) \
            .values('author') \
            .annotate(total=Coalesce(Sum('map_count'), Value(0))) \
            .values('total')[:1]

        high_sub = AuthorCategoryCounter.objects.filter(author=OuterRef('pk'), category__in=CATEGORIES_HIGH) \
            .values('author') \
            .annotate(total=Coalesce(Sum('map_count'), Value(0))) \
            .values('total')[:1]

        qs = qs.annotate(
            total_maps=Coalesce(Subquery(total_sub, output_field=IntegerField()), Value(0)),
            total_high_perms=Coalesce(Subquery(high_sub, output_field=IntegerField()), Value(0)),
            category_tags=ArrayAgg(
                'category_counters__category',
                filter=Q(category_counters__category__in=CATEGORIES_TAG),
                distinct=True
            ),
        )

        qs = AUTHOR_SEARCH_ENGINE.apply(qs, grouped_includes, grouped_excludes, sort_specs=sort_specs, request=request)

        paginator = self.pagination_class()
        try:
            items, next_cursor = paginator.paginate_queryset(qs, request)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(items, many=True, context=self.get_serializer_context())
        return Response({
            'results': serializer.data,
            'next_cursor': next_cursor,
        })