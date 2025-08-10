from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from pgvector.django import VectorField, IvfflatIndex

class Author(models.Model):
    id = models.AutoField(primary_key=True)
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


class Map(models.Model):
    code = models.IntegerField(primary_key=True)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='maps'
    )
    category = models.PositiveSmallIntegerField(db_index=True)

    xml = models.TextField()
    tags = ArrayField(models.CharField(max_length=100), default=list, blank=True)

    embedding = VectorField(dimensions=128)

    class Meta:
        db_table = 'map'
        indexes = [
            models.Index(fields=['category'], name='map_category_idx'),
            models.Index(fields=['author'], name='map_author_idx'),
            models.Index(fields=['category', 'author'], name='map_category_author_idx'),
            GinIndex(
                name='map_tags_gin',
                fields=['tags']
            ),
            GinIndex(
                name='map_xml_trgm',
                fields=['xml'],
                opclasses=['gin_trgm_ops'],
            ),
            IvfflatIndex(
                name='map_emb_ivf',
                fields=['embedding'],
                lists=100,
                opclasses=['vector_l2_ops'],
            ),
        ]

    def __str__(self):
        return f"Map {self.code} by {self.author.name}"