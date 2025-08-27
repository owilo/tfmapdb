from django.urls import path
from .views.MapListView import MapListView
from .views.MapDetailView import MapDetailView
from .views.MapImageView import MapImageView
from .views.AuthorListView import AuthorListView
from .views.AuthorProfileView import AuthorProfileView
from .views.CategoriesListView import CategoriesListView
from .views.TagDataView import TagDataView
from .views.TagsListView import TagsListView
from .views.LeaderboardView import LeaderboardView

urlpatterns = [
    path('gallery/', MapListView.as_view(), name='map-list'),
    path('map/<int:code>/', MapDetailView.as_view(), name='map-detail'),
    path('map/<int:code>/image.png', MapImageView.as_view(), name='map-image'),
    path('authors/', AuthorListView.as_view(), name='author-list'),
    path('author/<str:name>/', AuthorProfileView.as_view(), name='author-profile'),
    path('categories/', CategoriesListView.as_view(), name='categories-list'),
    path('category/<int:id>/', TagDataView.as_view(), {'filter_type': 'category'}, name='category-data'),
    path('tags/', TagsListView.as_view(), name='tags-list'),
    path('tag/<str:id>/', TagDataView.as_view(), {'filter_type': 'tag'}, name='tag-data'),
    path('leaderboards/', LeaderboardView.as_view(), name='leaderboards'),
]