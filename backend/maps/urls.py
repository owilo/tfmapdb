from django.urls import path
from django.views.generic import RedirectView
from .views import *

urlpatterns = [
    path('', RedirectView.as_view(url='gallery/', permanent=False)),
    path('gallery/', MapListView.as_view(), name='map-list'),
    path('map/<int:code>/', MapDetailView.as_view(), name='map-detail'),
    path('map/<int:code>/image.png', MapImageView.as_view(), name='map-image'),
    path('authors/', AuthorListView.as_view(), name='author-list'),
    path('author/<str:name>/', AuthorProfileView.as_view(), name='author-profile'),
    path('categories/', CategoriesListView.as_view(), name='categories-list'),
]