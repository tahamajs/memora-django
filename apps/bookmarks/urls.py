from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookmarkCollectionViewSet, BookmarkViewSet

router = DefaultRouter()
router.register(r'collections', BookmarkCollectionViewSet, basename='bookmark-collection')
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')

urlpatterns = [
    path('', include(router.urls)),
]
