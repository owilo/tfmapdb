from django.db.models import Q, Sum, IntegerField, Value
from django.db.models.functions import Coalesce
from django.contrib.postgres.aggregates import ArrayAgg

from rest_framework import generics

from maps.models import Author
from maps.serializers import *
from maps.constants import *

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