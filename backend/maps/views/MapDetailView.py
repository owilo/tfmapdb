from rest_framework import generics

from maps.models import Map
from maps.serializers import MapSerializer

class MapDetailView(generics.RetrieveAPIView):
    queryset = Map.objects.select_related('author')
    serializer_class = MapSerializer
    lookup_field = 'code'