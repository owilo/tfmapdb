from django.db.models import Sum

from rest_framework import generics, response

from maps.models import Map, Author, AuthorCategoryCounter
from maps.serializers import *
from maps.constants import *

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