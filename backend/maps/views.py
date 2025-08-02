from rest_framework import views, generics
from .models import Map
from .serializers import MapSerializer, MinimalMapSerializer
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from PIL import Image, ImageDraw, ImageFont
import re

class MapListView(generics.ListAPIView):
    serializer_class = MinimalMapSerializer

    def get_queryset(self):
        queryset = Map.objects.all()
        author = self.request.GET.get('author', None)
        if author:
            if not re.search(r'#\d{4}$', author):
                author = f'{author}#0000'
            queryset = queryset.filter(author__name=author)
        category = self.request.GET.get('category', None)
        if category:
            queryset = queryset.filter(category__id=category)
        sort = self.request.GET.get('sort', None)
        if sort == 'asc':
            queryset = queryset.order_by('code')
        else: # Most recent first
            queryset = queryset.order_by('-code')
        return queryset

class MapDetailView(generics.RetrieveAPIView):
    queryset = Map.objects.select_related('author', 'category')
    serializer_class = MapSerializer
    lookup_field = 'code'

class MapImageView(views.APIView):
    def get(self, request, code, format=None):
        map_obj = get_object_or_404(Map, code=code)

        xml_text = map_obj.xml or ''

        width, height = 800, 400
        image = Image.new('RGB', (width, height), '#6a7495')
        draw = ImageDraw.Draw(image)

        font = ImageFont.load_default(size=18)

        margin, offset = 10, 10
        for line in xml_text.splitlines():
            words = line.split(' ')
            current_line = ''
            for word in words:
                test_line = f"{current_line}{word} "
                bbox = draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]

                if line_width > width - 2 * margin:
                    draw.text((margin, offset), current_line, font=font, fill='white')
                    offset += line_height + 2
                    current_line = f"{word} "
                else:
                    current_line = test_line

            if current_line:
                draw.text((margin, offset), current_line, font=font, fill='white')
                bbox = draw.textbbox((0, 0), current_line, font=font)
                offset += (bbox[3] - bbox[1]) + 2

        buffer = BytesIO()
        # Thumbnail
        image.resize((200, 100), Image.Resampling.LANCZOS)
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return HttpResponse(buffer, content_type='image/png')