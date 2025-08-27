from django.db.models import Count, Sum

from rest_framework import generics

from maps.models import AuthorTagCounter
from maps.serializers import *
from maps.constants import *

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