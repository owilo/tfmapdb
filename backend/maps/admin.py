from django.contrib import admin
from .models import Author, Map

admin.site.register([Author, Map])