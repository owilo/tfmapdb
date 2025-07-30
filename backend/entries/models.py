from django.db import models

class Entry(models.Model):
    id   = models.IntegerField(primary_key=True)
    text = models.TextField()

    def __str__(self):
        return f"{self.id}: {self.text[:20]}..."