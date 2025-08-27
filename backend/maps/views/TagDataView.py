from django.db.models import Sum
from django.db.models.functions import Coalesce

from rest_framework import views, response, status

from maps.models import Map, AuthorCategoryCounter, AuthorTagCounter
from maps.serializers import *

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