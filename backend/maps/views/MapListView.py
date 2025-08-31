from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from maps.serializers import MinimalMapSerializer
from maps.models import Map
from maps.pagination import KeysetPagination
from maps.search.map_search import CodeHandler, AuthorHandler, CategoryHandler, TagHandler, SimilarityHandler
from maps.search.search_base import SearchEngine

MAP_SEARCH_ENGINE = SearchEngine(
    handlers=[
        CodeHandler(),
        CategoryHandler(),
        TagHandler(),
        AuthorHandler(),
        SimilarityHandler(),
    ],
    fallback_order=['-similarity', '-code']
)

class MapListView(generics.ListAPIView):
    serializer_class = MinimalMapSerializer
    queryset = Map.objects.all()
    pagination_class = KeysetPagination
    
    def list(self, request, *args, **kwargs):
        raw = request.GET.get('s', '').strip()
        grouped, sort_specs = MAP_SEARCH_ENGINE.parse(raw)
        
        qs = super().get_queryset()
        qs = MAP_SEARCH_ENGINE.apply(qs, grouped, sort_specs=sort_specs, request=request)
        
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