import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from django.db.models import Q, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import views, generics
from rest_framework.generics import ListAPIView

from .models import Map, Author
from .serializers import MapSerializer, MinimalMapSerializer, MinimalAuthorSerializer, CATEGORIES_HIGH, CATEGORIES_LOW, CATEGORIES_DISC, CATEGORIES_STANDARD, CATEGORIES_UNUSED, CATEGORIES_BOOTCAMP

map_code_regex = re.compile(r"^!?((@?\d+(-@?\d*)?)|(-@?\d+))$")
author_regex = re.compile(r'^!?\+?[A-Za-z]\w*(?:#\d{4})?$', re.IGNORECASE)
category_regex = re.compile(r"^!?[Pp#]((\d+(-\d*)?)|(-\d+))$", re.IGNORECASE)

# TODO Too many regexes, refactor later
category_high_regex = re.compile(r"^!?[Pp#]h(igh)?$", re.IGNORECASE)
category_low_regex = re.compile(r"^!?[Pp#]l(ow)?$", re.IGNORECASE)
category_disc_regex = re.compile(r"^!?[Pp#]d(isc(ussion)?)?$", re.IGNORECASE)
category_standard_regex = re.compile(r"^!?[Pp#]s(tandard)?$", re.IGNORECASE)
category_unused_regex = re.compile(r"^!?[Pp#]u(nused)?$", re.IGNORECASE)
category_bootcamp_regex = re.compile(r"^!?[Pp#]b(c|ootcamp)?$", re.IGNORECASE)

class MapListView(generics.ListAPIView):
    serializer_class = MinimalMapSerializer
    queryset = Map.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.GET

        raw = params.get('s', '').strip()
        if not raw:
            sort = params.get('sort', 'desc').lower()
            if sort == 'asc':
                return qs.order_by('code')
            return qs.order_by('-code')

        items = re.split(r'\s+', raw)

        codes_tokens = []
        authors_tokens = []
        categories_tokens = []

        for it in items:
            if not it:
                continue
            if map_code_regex.match(it):
                codes_tokens.append(it)
            elif category_regex.match(it) or category_high_regex.match(it) or category_low_regex.match(it) or category_disc_regex.match(it) or category_standard_regex.match(it) or category_unused_regex.match(it) or category_bootcamp_regex.match(it):
                categories_tokens.append(it)
            elif author_regex.match(it):
                authors_tokens.append(it)
            else:
                continue

        def split_includes_excludes(tokens):
            inc, exc = [], []
            for t in tokens:
                if t.startswith('!'):
                    exc.append(t[1:])
                else:
                    inc.append(t)
            return inc, exc

        def build_range_q_for_tokens(field_name, tokens, is_category=False):
            if not tokens:
                return None

            inc_terms, exc_terms = split_includes_excludes(tokens)

            def term_to_q(term):
                norm = term.lstrip('@Pp#')
                if not norm:
                    return None
                
                if norm in ['h', 'high']:
                    return Q(category__id__in=CATEGORIES_HIGH)
                if norm in ['l', 'low']:
                    return Q(category__id__in=CATEGORIES_LOW)
                if norm in ['d', 'disc', 'discussion']:
                    return Q(category__id__in=CATEGORIES_DISC)
                if norm in ['s', 'standard']:
                    return Q(category__id__in=CATEGORIES_STANDARD)
                if norm in ['u', 'unused']:
                    return Q(category__id__in=CATEGORIES_UNUSED)

                if '-' in norm:
                    lo, hi = norm.split('-', 1)
                    lo = lo.strip()
                    hi = hi.strip()
                    q_sub = Q()
                    if lo != '':
                        try:
                            q_sub &= Q(**{f"{field_name}__gte": int(lo)})
                        except ValueError:
                            return None
                    if hi != '':
                        try:
                            q_sub &= Q(**{f"{field_name}__lte": int(hi)})
                        except ValueError:
                            return None
                    return q_sub
                else:
                    try:
                        return Q(**{field_name: int(norm)})
                    except ValueError:
                        return None

            q_obj = Q()
            any_inc = False
            for t in inc_terms:
                q = term_to_q(t)
                if q is None:
                    continue
                any_inc = True
                q_obj |= q

            if not any_inc and not exc_terms:
                return None

            for t in exc_terms:
                q = term_to_q(t)
                if q is None:
                    continue
                q_obj &= ~q

            return q_obj

        # Authors
        if authors_tokens:
            inc_authors, exc_authors = split_includes_excludes(authors_tokens)
            author_q = Q()
            any_inc = False
            tag_re = re.compile(r'#\d{4}$')
            for a in inc_authors:
                name = a.capitalize()
                if not tag_re.search(name):
                    name = f'{name}#0000'
                author_q |= Q(author__name=name)
                any_inc = True

            for a in exc_authors:
                name = a.capitalize()
                if name.startswith('+'):
                    name = name[1:]
                if not tag_re.search(name):
                    name = f'{name}#0000'
                author_q &= ~Q(author__name=name)

            if any_inc or exc_authors:
                qs = qs.filter(author_q)

        # Map codes
        codes_q = build_range_q_for_tokens('code', codes_tokens)
        if codes_q is not None:
            qs = qs.filter(codes_q)

        # Categories
        cats_q = build_range_q_for_tokens('category__id', categories_tokens, is_category=True)
        if cats_q is not None:
            qs = qs.filter(cats_q)

        # Sorting
        # TODO Allow sorting by author, category, etc.
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
                filter=Q(maps__category__id__in=CATEGORIES_HIGH),
                distinct=True
            ),
            total_high_perms=Count(
                'maps',
                filter=Q(maps__category__id__in=CATEGORIES_HIGH)
            )
        ).order_by('id')
