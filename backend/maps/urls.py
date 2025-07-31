from django.urls import path
from .views import MapDetailView

urlpatterns = [
    path('map/<int:code>/', MapDetailView.as_view(), name='map-detail'),
]