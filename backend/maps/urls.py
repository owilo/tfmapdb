from django.urls import path
from django.views.generic import RedirectView
from .views import MapListView, MapDetailView, MapImageView

urlpatterns = [
    path('', RedirectView.as_view(url='gallery/', permanent=False)),
    path('gallery/', MapListView.as_view(), name='map-list'),
    path('map/<int:code>/', MapDetailView.as_view(), name='map-detail'),
    path('map/<int:code>/image.png', MapImageView.as_view(), name='map-image'),
]