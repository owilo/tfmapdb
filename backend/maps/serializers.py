from rest_framework import serializers
from .models import Map, Author, Category
from .utils import extract_map_data

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'mapcount']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class MapSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Map
        fields = ['code', 'xml', 'embedding', 'author', 'category']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        grounds_count, objects_count, joints_count = extract_map_data(instance.xml)
        data.update({
            'map_data':{
                'grounds_count': grounds_count,
                'objects_count': objects_count,
                'joints_count': joints_count,
            }
        })
        return data

class MinimalMapSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)
    category_id = serializers.IntegerField(source='category.id', read_only=True)

    class Meta:
        model = Map
        fields = ['code', 'author_name', 'category_id']