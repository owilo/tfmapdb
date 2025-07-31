from django.urls import path
from .views import MapListView, MapDetailView, MapImageView

urlpatterns = [
    path('', MapListView.as_view(), name='map-list'),
    path('map/<int:code>/', MapDetailView.as_view(), name='map-detail'),
    path('map/<int:code>/image.png', MapImageView.as_view(), name='map-image'),
]