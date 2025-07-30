from django.urls import path
from .views import EntryDetailAPI

urlpatterns = [
    path('entry/<int:id>/', EntryDetailAPI.as_view(), name='entry-detail'),
]