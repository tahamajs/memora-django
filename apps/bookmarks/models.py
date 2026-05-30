import uuid
from django.db import models
from django.conf import settings

class BookmarkCollection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmark_collections')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Bookmark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    collection = models.ForeignKey(BookmarkCollection, on_delete=models.CASCADE, related_name='bookmarks')
    url = models.URLField(max_length=2000)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, default='')
    favicon_url = models.URLField(blank=True, default='')
    tags = models.ManyToManyField('notes.Tag', blank=True, related_name='bookmarks')
    note = models.ForeignKey('notes.Note', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookmarks')
    is_read = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
