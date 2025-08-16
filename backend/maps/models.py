from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from pgvector.django import VectorField, IvfflatIndex

# Map authors
class Author(models.Model):
    id = models.IntegerField(primary_key=True, unique=True)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'author'
        indexes = [
            GinIndex(
                name='author_name_trgm',
                fields=['name'],
                opclasses=['gin_trgm_ops']
            )
        ]

# Maps
class Map(models.Model):
    code = models.IntegerField(primary_key=True)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='maps'
    )
    category = models.PositiveSmallIntegerField(db_index=True)

    xml = models.TextField()
    tags = ArrayField(models.CharField(max_length=64), default=list, blank=True)

    embedding = VectorField(dimensions=128)

    class Meta:
        db_table = 'map'
        indexes = [
            models.Index(fields=['category'], name='map_category_idx'), # Index by category
            models.Index(fields=['author'], name='map_author_idx'), # Index by author
            GinIndex(
                name='map_tags_gin',
                fields=['tags']
            ), # GIN index for tags
            GinIndex(
                name='map_xml_trgm',
                fields=['xml'],
                opclasses=['gin_trgm_ops'],
            ), # GIN index for XML content
            IvfflatIndex(
                name='map_emb_ivf',
                fields=['embedding'],
                lists=100,
                opclasses=['vector_l2_ops'],
            ), # IVF index for map image embeddings
        ]

    def __str__(self):
        return f"Map @{self.code} by {self.author.name}"

# One row per (author, category) with the count of maps
class AuthorCategoryCounter(models.Model):
    author = models.ForeignKey('Author', on_delete=models.CASCADE, related_name='category_counters')
    category = models.PositiveSmallIntegerField(db_index=True)
    map_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'author_category_counter'
        unique_together = (('author', 'category'),)
        indexes = [
            models.Index(fields=['category', 'map_count'], name='acc_category_count_idx'),
            models.Index(fields=['author'], name='acc_author_idx'),
        ]

    def __str__(self):
        return f'ACC(author={self.author_id}, category={self.category}, count={self.map_count})'

# One row per (author, tag) with the count of maps
class AuthorTagCounter(models.Model):
    author = models.ForeignKey('Author', on_delete=models.CASCADE, related_name='tag_counters')
    tag = models.CharField(max_length=64, db_index=True)
    map_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'author_tag_counter'
        unique_together = (('author', 'tag'),)
        indexes = [
            models.Index(fields=['tag', 'map_count'], name='atc_tag_count_idx'),
            models.Index(fields=['author'], name='atc_author_idx'),
        ]

    def __str__(self):
        return f'ATC(author={self.author_id}, tag={self.tag}, count={self.map_count})'