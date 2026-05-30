"""
Serializers for note models.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Note, NoteVersion, Category, Tag,
    Attachment, ResearchNote
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Minimal user serializer."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class TagSerializer(serializers.ModelSerializer):
    """Tag serializer with usage count."""
    note_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'color', 'description',
                 'usage_count', 'note_count', 'created_at']
        read_only_fields = ['slug', 'usage_count']

    def get_note_count(self, obj):
        return obj.notes.count()


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer with hierarchy support."""
    children = serializers.SerializerMethodField()
    note_count = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'color', 'icon', 'description',
                 'parent', 'parent_name', 'children', 'note_count',
                 'sort_order', 'is_active', 'created_at']
        read_only_fields = ['slug']

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.all(), many=True).data
        return []

    def get_note_count(self, obj):
        return obj.notes.count()

    def get_parent_name(self, obj):
        return obj.parent.name if obj.parent else None


class NoteVersionSerializer(serializers.ModelSerializer):
    """Note version history serializer."""
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = NoteVersion
        fields = ['id', 'version_number', 'title', 'content',
                 'commit_message', 'commit_hash', 'created_by', 'created_at']


class AttachmentSerializer(serializers.ModelSerializer):
    """Attachment serializer."""
    uploaded_by = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ['id', 'file', 'file_url', 'filename', 'original_name',
                 'mime_type', 'size', 'uploaded_by', 'created_at']
        read_only_fields = ['filename', 'mime_type', 'size']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None


class NoteListSerializer(serializers.ModelSerializer):
    """Compact note serializer for list views."""
    tags = TagSerializer(many=True, read_only=True)
    category_name = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = ['id', 'title', 'excerpt', 'status', 'priority',
                 'category', 'category_name', 'tags', 'author_name',
                 'is_favorite', 'is_pinned', 'word_count', 'reading_time',
                 'version', 'created_at', 'updated_at', 'published_at']

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_author_name(self, obj):
        return obj.author.username if obj.author else None


class NoteDetailSerializer(serializers.ModelSerializer):
    """Full note serializer for detail view."""
    tags = TagSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    author = UserSerializer(read_only=True)
    collaborators = UserSerializer(many=True, read_only=True)
    versions = NoteVersionSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)

    # Write-only fields for relationships
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    category_id = serializers.IntegerField(write_only=True, required=False)
    collaborator_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = Note
        fields = '__all__'
        read_only_fields = [
            'id', 'html_content', 'word_count', 'reading_time',
            'excerpt', 'version', 'git_commit_hash', 'git_branch',
            'ai_summary', 'ai_sentiment', 'ai_keywords',
            'author', 'created_at', 'updated_at', 'published_at'
        ]

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        category_id = validated_data.pop('category_id', None)
        collaborator_ids = validated_data.pop('collaborator_ids', [])

        note = Note.objects.create(**validated_data)

        if tag_ids:
            note.tags.set(tag_ids)
        if category_id:
            note.category_id = category_id
            note.save()
        if collaborator_ids:
            note.collaborators.set(collaborator_ids)

        return note

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        category_id = validated_data.pop('category_id', None)
        collaborator_ids = validated_data.pop('collaborator_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if tag_ids is not None:
            instance.tags.set(tag_ids)
        if category_id is not None:
            instance.category_id = category_id
        if collaborator_ids is not None:
            instance.collaborators.set(collaborator_ids)

        instance.save()
        return instance


class NoteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notes."""

    class Meta:
        model = Note
        fields = ['title', 'content', 'markdown_content', 'category',
                 'tags', 'status', 'priority', 'is_favorite', 'metadata']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class NoteUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating notes."""

    class Meta:
        model = Note
        fields = ['title', 'content', 'markdown_content', 'category',
                 'tags', 'status', 'priority', 'is_favorite',
                 'is_pinned', 'metadata']
        extra_kwargs = {field: {'required': False} for field in fields}


class ResearchNoteSerializer(serializers.ModelSerializer):
    """Research note serializer."""
    author = UserSerializer(read_only=True)
    note_title = serializers.SerializerMethodField()

    class Meta:
        model = ResearchNote
        fields = '__all__'
        read_only_fields = ['author', 'created_at', 'updated_at']

    def get_note_title(self, obj):
        return obj.note.title if obj.note else None


    from .models import Reminder, NoteTemplate, Comment, Share, CustomSchema

class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = '__all__'

    def get_replies(self, obj):
        return CommentSerializer(obj.replies.all(), many=True).data

class ShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Share
        fields = '__all__'

class NoteTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteTemplate
        fields = '__all__'


from .models import APIKey

class APIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = ['id', 'name', 'scopes', 'expires_at', 'created_at', 'revoked']
        read_only_fields = ['id', 'created_at']
