from rest_framework import serializers
from .models import Map, Author
from .utils import extract_map_data
from .constants import *
from django.db.models import Count

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name']

class MapSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Map
        fields = ['code', 'xml', 'embedding', 'author', 'category', 'tags']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        map_data = extract_map_data(instance.xml)
        data.update({
            'map_data': map_data
        })
        return data

class MinimalMapSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)

    class Meta:
        model = Map
        fields = ['code', 'author_name', 'category']

class MinimalAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'mapcount']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['mapcount'] = instance.map_set.count()
        return data

class MinimalAuthorSerializer(serializers.ModelSerializer):
    total_maps = serializers.IntegerField(read_only=True)
    total_high_perms = serializers.IntegerField(read_only=True)

    category_tags = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = (
            'name',
            'total_maps',
            'category_tags',
            'total_high_perms',
        )

    def get_category_tags(self, obj):
        return getattr(obj, 'category_tags') or []

class CategoryCountSerializer(serializers.Serializer):
    category = serializers.IntegerField()
    permanent = serializers.BooleanField()
    map_count = serializers.IntegerField()

class MapSummarySerializer(serializers.Serializer):
    code = serializers.IntegerField()
    category = serializers.IntegerField()

class AuthorDetailSerializer(serializers.Serializer):
    total_maps = serializers.IntegerField()
    high_maps = serializers.IntegerField()
    permed_maps = serializers.IntegerField()
    categories = CategoryCountSerializer(many=True)
    last_exported = MapSummarySerializer(many=True)
    last_permed = MapSummarySerializer(many=True)

class MapAuthorSummarySerializer(serializers.Serializer):
    code = serializers.IntegerField()
    author = serializers.CharField()
    category = serializers.IntegerField()

class CategoriesListSerializer(serializers.Serializer):
    category = serializers.IntegerField()
    maps_count = serializers.IntegerField()
    authors_count = serializers.IntegerField()

class TagsListSerializer(serializers.Serializer):
    tag = serializers.CharField()
    maps_count = serializers.IntegerField()
    authors_count = serializers.IntegerField()

class AuthorCountSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    count = serializers.IntegerField()