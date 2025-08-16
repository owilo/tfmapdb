from django.contrib import admin
from .models import Author, Map, AuthorCategoryCounter, AuthorTagCounter

admin.site.register([Author, Map, AuthorCategoryCounter, AuthorTagCounter])