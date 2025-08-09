import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from django.db.models import Q, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import views, generics
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import Map, Author
from .serializers import MapSerializer, MinimalMapSerializer, MinimalAuthorSerializer, HIGH_CATEGORIES

class MapListView(generics.ListAPIView):
    serializer_class = MinimalMapSerializer
    queryset = Map.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.GET

        # Split and classify includes/excludes
        def split_terms(raw):
            includes, excludes = [], []
            for term in raw.split(','):
                term = term.strip()
                if not term:
                    continue
                if term.startswith('!'):
                    excludes.append(term[1:])
                else:
                    includes.append(term)
            return includes, excludes

        # Authors
        raw_authors = params.get('author', '')
        if raw_authors:
            inc_authors, exc_authors = split_terms(raw_authors)
            author_q = Q()
            # Include
            for a in inc_authors:
                # Ensure tag
                if not re.search(r'#\d{4}$', a):
                    a = f'{a}#0000'
                author_q |= Q(author__name=a)
            # Exclude
            for a in exc_authors:
                if not re.search(r'#\d{4}$', a):
                    a = f'{a}#0000'
                author_q &= ~Q(author__name=a)
            qs = qs.filter(author_q)

        # Range parser
        def build_range_q(field_name, raw):
            inc, exc = split_terms(raw)
            q_obj = Q()
            # lo-hi, -hi, lo- or single
            def make_q(val):
                if '-' in val:
                    lo, hi = val.split('-', 1)
                    lo = int(lo) if lo.strip() else None
                    hi = int(hi) if hi.strip() else None
                    sub = Q()
                    if lo is not None:
                        sub &= Q(**{f"{field_name}__gte": lo})
                    if hi is not None:
                        sub &= Q(**{f"{field_name}__lte": hi})
                    return sub
                else:
                    return Q(**{field_name: int(val)})
            # Includes
            for term in inc:
                q_obj |= make_q(term)
            # Excludes
            for term in exc:
                q_obj &= ~make_q(term)
            return q_obj

        # Codes
        raw_codes = params.get('code', '')
        if raw_codes:
            qs = qs.filter(build_range_q('code', raw_codes))

        # Categories
        raw_cats = params.get('category', '')
        if raw_cats:
            qs = qs.filter(build_range_q('category__id', raw_cats))

        # Sorting
        # TODO Maybe add more sorting options later
        sort = params.get('sort', 'desc').lower()
        if sort == 'asc':
            qs = qs.order_by('code')
        else:
            qs = qs.order_by('-code')

        return qs

class MapDetailView(generics.RetrieveAPIView):
    queryset = Map.objects.select_related('author', 'category')
    serializer_class = MapSerializer
    lookup_field = 'code'

class MapImageView(views.APIView):
    # TODO Generate actual map images
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
        image = image.resize((350, 175), Image.Resampling.LANCZOS)
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return HttpResponse(buffer, content_type='image/png')

class AuthorListView(ListAPIView):
    serializer_class = MinimalAuthorSerializer
    pagination_class = None # TODO Later implement pagination

    def get_queryset(self):
        return Author.objects.annotate(
            total_maps=Count('maps'),
            total_high_categories=Count(
                'maps__category',
                filter=Q(maps__category__id__in=HIGH_CATEGORIES),
                distinct=True
            ),
            total_high_perms=Count(
                'maps',
                filter=Q(maps__category__id__in=HIGH_CATEGORIES)
            )
        ).order_by('id')
