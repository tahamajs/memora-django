from django.contrib import admin
from .models import BookmarkCollection, Bookmark

@admin.register(BookmarkCollection)
class BookmarkCollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['title', 'url', 'collection', 'is_read', 'is_favorite', 'created_at']
    list_filter = ['is_read', 'is_favorite', 'collection']
    search_fields = ['title', 'url', 'description']
