from rest_framework import generics
from .models import Map
from .serializers import MapSerializer

class MapDetailView(generics.RetrieveAPIView):
    queryset = Map.objects.select_related('author', 'category')
    serializer_class = MapSerializer
    lookup_field = 'code'