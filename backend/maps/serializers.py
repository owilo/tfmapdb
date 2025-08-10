from rest_framework import serializers
from .models import Map, Author, Category
from .utils import extract_map_data
from django.db.models import Count

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

class MinimalAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'mapcount']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['mapcount'] = instance.map_set.count()
        return data

CATEGORIES_HIGH = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 17, 18, 19, 24]
CATEGORIES_LOW = [1, 13]
CATEGORIES_DISC = [20, 21, 23, 24, 32, 34, 38, 42]
CATEGORIES_STANDARD = [0, 22, 43, 44]
CATEGORIES_UNUSED = [2, 19]
CATEGORIES_BOOTCAMP = [3, 13]

# serializers.py
from rest_framework import serializers

class MinimalAuthorSerializer(serializers.ModelSerializer):
    total_maps = serializers.IntegerField(read_only=True)
    total_high_perms = serializers.IntegerField(read_only=True)

    high_categories = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = (
            'name',
            'total_maps',
            'high_categories',
            'total_high_perms',
        )

    def get_high_categories(self, obj):
        return getattr(obj, 'high_categories') or []

class AuthorDetailSerializer(serializers.ModelSerializer):
    categories = serializers.ListField(read_only=True)

    class Meta:
        model = Author
        fields = ('id', 'name', 'categories')

    def to_representation(self, instance):
        category_list = self.context.get('category_list')
        if category_list is None:
            counts = Map.objects.filter(author=instance).values('category_id').annotate(count=Count('code'))
            category_list = [{'category': c['category_id'], 'count': c['count']} for c in counts]

        data = super().to_representation(instance)
        data['categories'] = category_list
        return data