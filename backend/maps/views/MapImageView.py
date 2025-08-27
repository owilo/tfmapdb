from io import BytesIO

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import views

from maps.models import Map
from maps.serializers import *
from maps.constants import *
from maps.utils import xml_to_image

class MapImageView(views.APIView):
    def get(self, request, code, format=None):
        map_obj = get_object_or_404(Map, code=code)

        try:
            scale = float(request.GET.get('scale', 1.0))
        except ValueError:
            scale = 1.0

        if not (0 < scale <= 1):
            scale = 1.0

        xml_text = map_obj.xml or ''

        map_data = extract_map_data(xml_text)
        image = xml_to_image(xml_text, (map_data["length"], map_data["height"]), scale)
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return HttpResponse(buffer, content_type='image/png')