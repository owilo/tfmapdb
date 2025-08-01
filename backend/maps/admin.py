from django.contrib import admin
from .models import Author, Category, Map

admin.site.register([Author, Category, Map])