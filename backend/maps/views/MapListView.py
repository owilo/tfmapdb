from rest_framework import generics
from maps.search import (
    SearchEngine, CodeHandler, AuthorHandler, CategoryHandler, SimilarityHandler
)
from maps.serializers import MinimalMapSerializer
from maps.models import Map

MAP_SEARCH_ENGINE = SearchEngine([
    SimilarityHandler(),
    CodeHandler(),
    CategoryHandler(),
    AuthorHandler(),
])

class MapListView(generics.ListAPIView):
    serializer_class = MinimalMapSerializer
    queryset = Map.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        raw = self.request.GET.get('s', '').strip()

        grouped, sort_specs = MAP_SEARCH_ENGINE.parse(raw)

        self.include_similarity = bool(grouped.get('sim'))

        qs = MAP_SEARCH_ENGINE.apply(qs, grouped, sort_specs=sort_specs, request=self.request)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['include_similarity'] = getattr(self, 'include_similarity', False)
        return ctx
