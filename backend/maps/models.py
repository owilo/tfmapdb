from django.db import models
from django.contrib.postgres.indexes import GinIndex
from pgvector.django import VectorField, IvfflatIndex


class Author(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    mapcount = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name


class Category(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Map(models.Model):
    code = models.IntegerField(primary_key=True)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='maps'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='maps'
    )
    xml = models.TextField()
    embedding = VectorField(dimensions=96)

    class Meta:
        db_table = 'map'
        indexes = [
            models.Index(fields=['author']),
            models.Index(fields=['category']),
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