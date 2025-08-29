from rest_framework import generics, status
from rest_framework.response import Response
from maps.search import (
    SearchEngine, CodeHandler, AuthorHandler, CategoryHandler, SimilarityHandler
)
from maps.serializers import MinimalMapSerializer
from maps.models import Map
from maps.pagination import encode_cursor, decode_cursor, build_keyset_q, default_model_field_cast, ensure_stable_ordering

MAP_SEARCH_ENGINE = SearchEngine([
    SimilarityHandler(),
    CodeHandler(),
    CategoryHandler(),
    AuthorHandler(),
])

DEFAULT_LIMIT = 20
MAX_LIMIT = 100

class MapListView(generics.ListAPIView):
    serializer_class = MinimalMapSerializer
    queryset = Map.objects.all()

    def list(self, request, *args, **kwargs):
        raw = request.GET.get('s', '').strip()
        grouped, sort_specs = MAP_SEARCH_ENGINE.parse(raw)
        
        has_similarity_tokens = bool(grouped.get('sim'))
        has_explicit_similarity_sort = any(name == 'sim' for name, _ in sort_specs)
        
        sort_specs = sort_specs or []

        try:
            limit = min(int(request.GET.get('limit', DEFAULT_LIMIT)), MAX_LIMIT)
            if limit <= 0:
                limit = DEFAULT_LIMIT
        except Exception:
            limit = DEFAULT_LIMIT

        cursor_token = request.GET.get('cursor')
        last_values = []
        if cursor_token:
            last_values = decode_cursor(cursor_token)

        qs = super().get_queryset()
        qs = MAP_SEARCH_ENGINE.apply(qs, grouped, sort_specs=sort_specs, request=request)

        final_sort_specs = []

        if sort_specs:
            for name, dir_ in sort_specs:
                if name in MAP_SEARCH_ENGINE.handlers_by_name:
                    h = MAP_SEARCH_ENGINE.handlers_by_name[name]
                    if h.sortable:
                        key = h.sort_key or name
                        if key == 'similarity' and 'similarity' not in qs.query.annotations:
                            continue
                        final_sort_specs.append((key, dir_))
            
            if (has_similarity_tokens and not has_explicit_similarity_sort and 
                'similarity' in qs.query.annotations and
                not any(key == 'similarity' for key, _ in final_sort_specs)):
                final_sort_specs.append(('similarity', 'desc'))
            
            if not any(key == 'code' for key, _ in final_sort_specs):
                final_sort_specs.append(('code', 'desc'))
        else:
            if 'similarity' in qs.query.annotations:
                final_sort_specs = [('similarity', 'desc'), ('code', 'desc')]
            else:
                final_sort_specs = [('code', 'desc')]

        if last_values:
            if len(last_values) != len(final_sort_specs):
                return Response({'detail': 'Invalid cursor'}, status=status.HTTP_400_BAD_REQUEST)
            keyset_q = build_keyset_q(final_sort_specs, last_values, model_field_cast=default_model_field_cast)
            qs = qs.filter(keyset_q)

        order_fields = []
        for key, dir_ in final_sort_specs:
            if key == 'similarity' and 'similarity' not in qs.query.annotations:
                continue
            order_fields.append(key if dir_ == 'asc' else f"-{key}")

        qs = qs.order_by(*order_fields)
        items = list(qs[: limit + 1])

        next_cursor = None
        if len(items) > limit:
            last_item = items[limit - 1]
            vals = []
            for key, _ in final_sort_specs:
                if key == 'similarity' and 'similarity' not in qs.query.annotations:
                    continue
                parts = key.split('__')
                v = getattr(last_item, parts[0], None)
                for p in parts[1:]:
                    v = getattr(v, p, None)
                v = default_model_field_cast(key, v)
                vals.append(v)
            next_cursor = encode_cursor(vals)
            items = items[:limit]

        serializer = self.get_serializer(items, many=True, context=self.get_serializer_context())
        return Response({
            'results': serializer.data,
            'next_cursor': next_cursor,
        })