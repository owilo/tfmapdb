from rest_framework.generics import RetrieveAPIView
from .models import Entry
from .serializers import EntrySerializer

class EntryDetailAPI(RetrieveAPIView):
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer
    lookup_field = 'id'