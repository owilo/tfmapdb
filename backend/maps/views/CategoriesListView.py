from django.db.models import Count, Sum

from rest_framework import generics

from maps.models import AuthorCategoryCounter
from maps.serializers import *

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