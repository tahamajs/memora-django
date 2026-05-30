from rest_framework import serializers
from .models import BookmarkCollection, Bookmark

class BookmarkSerializer(serializers.ModelSerializer):
    tags = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Bookmark
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookmarkCollectionSerializer(serializers.ModelSerializer):
    bookmarks = BookmarkSerializer(many=True, read_only=True)
    bookmark_count = serializers.SerializerMethodField()

    class Meta:
        model = BookmarkCollection
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'user']

    def get_bookmark_count(self, obj):
        return obj.bookmarks.count()
