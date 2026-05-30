"""
ViewSets and views for notes.
"""
from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
import logging

from .models import (
    Note, NoteVersion, Category, Tag,
    Attachment, ResearchNote
)
from .serializers import (
    NoteListSerializer, NoteDetailSerializer,
    NoteCreateSerializer, NoteUpdateSerializer,
    NoteVersionSerializer, CategorySerializer,
    TagSerializer, AttachmentSerializer,
    ResearchNoteSerializer
)
from .filters import NoteFilter, ResearchNoteFilter
from .permissions import IsAuthorOrCollaborator, IsAuthorOrReadOnly
from .services import NoteService, SearchService

logger = logging.getLogger(__name__)


class NoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Note CRUD operations with advanced features.
    """
    queryset = Note.objects.select_related('author', 'category')\
                          .prefetch_related('tags', 'collaborators')\
                          .all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NoteFilter
    search_fields = ['title', 'content', 'tags__name', 'category__name']
    ordering_fields = ['created_at', 'updated_at', 'title', 'priority', 'word_count']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return NoteListSerializer
        elif self.action in ['create']:
            return NoteCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NoteUpdateSerializer
        return NoteDetailSerializer

    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthorOrCollaborator()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filter by user's notes or public notes
        if user.is_authenticated:
            queryset = queryset.filter(
                Q(author=user) |
                Q(collaborators=user) |
                Q(status='published')
            ).distinct()
        else:
            queryset = queryset.filter(status='published')

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'])
    def my_notes(self, request):
        """Get current user's notes."""
        notes = self.get_queryset().filter(author=request.user)
        page = self.paginate_queryset(notes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(notes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def favorites(self, request):
        """Get favorite notes."""
        notes = self.get_queryset().filter(is_favorite=True)
        serializer = self.get_serializer(notes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pinned(self, request):
        """Get pinned notes."""
        notes = self.get_queryset().filter(is_pinned=True)
        serializer = self.get_serializer(notes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recently updated notes."""
        days = int(request.query_params.get('days', 7))
        since = timezone.now() - timedelta(days=days)
        notes = self.get_queryset().filter(updated_at__gte=since)
        serializer = self.get_serializer(notes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive or unarchive a note."""
        note = self.get_object()
        if note.is_archived:
            note.unarchive()
            return Response({'status': 'unarchived'})
        else:
            note.archive()
            return Response({'status': 'archived'})

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle favorite status."""
        note = self.get_object()
        note.toggle_favorite()
        return Response({
            'status': 'favorited' if note.is_favorite else 'unfavorited',
            'is_favorite': note.is_favorite
        })

    @action(detail=True, methods=['post'])
    def toggle_pin(self, request, pk=None):
        """Toggle pin status."""
        note = self.get_object()
        note.toggle_pin()
        return Response({
            'status': 'pinned' if note.is_pinned else 'unpinned',
            'is_pinned': note.is_pinned
        })

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a note."""
        original = self.get_object()
        note = NoteService.duplicate_note(original, request.user)
        serializer = self.get_serializer(note)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Get version history."""
        note = self.get_object()
        versions = note.versions.all()
        serializer = NoteVersionSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def restore_version(self, request, pk=None):
        """Restore a previous version."""
        note = self.get_object()
        version_id = request.data.get('version_id')
        version = get_object_or_404(note.versions, id=version_id)

        note.content = version.content
        note.title = version.title
        note.save()

        serializer = self.get_serializer(note)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get note statistics."""
        note = self.get_object()
        stats = {
            'word_count': note.word_count,
            'reading_time': note.reading_time,
            'version_count': note.versions.count(),
            'attachment_count': note.attachments.count(),
            'collaborator_count': note.collaborators.count(),
            'days_since_created': (timezone.now() - note.created_at).days,
            'days_since_updated': (timezone.now() - note.updated_at).days,
        }
        return Response(stats)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search across notes."""
        query = request.query_params.get('q', '')
        if not query:
            return Response([])

        cache_key = f'note_search_{query}'
        cached_results = cache.get(cache_key)

        if cached_results:
            return Response(cached_results)

        results = SearchService.search(query, request.user)
        cache.set(cache_key, results, timeout=300)  # Cache for 5 minutes

        return Response(results)

    @action(detail=False, methods=['get'])
    def stats_overview(self, request):
        """Get overview statistics."""
        user_notes = Note.objects.filter(author=request.user)

        stats = {
            'total_notes': user_notes.count(),
            'total_words': user_notes.aggregate(Sum('word_count'))['word_count__sum'] or 0,
            'avg_words_per_note': user_notes.aggregate(Avg('word_count'))['word_count__avg'] or 0,
            'favorites': user_notes.filter(is_favorite=True).count(),
            'pinned': user_notes.filter(is_pinned=True).count(),
            'archived': user_notes.filter(status='archived').count(),
            'published': user_notes.filter(status='published').count(),
            'notes_by_category': user_notes.values('category__name')\
                                          .annotate(count=Count('id'))\
                                          .order_by('-count'),
            'notes_by_tag': Tag.objects.filter(notes__author=request.user)\
                                      .annotate(count=Count('notes'))\
                                      .order_by('-count')[:10]\
                                      .values('name', 'count', 'color'),
            'recent_activity': user_notes.order_by('-updated_at')[:5]\
                                        .values('id', 'title', 'updated_at'),
        }

        return Response(stats)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for categories."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['get'])
    def notes(self, request, pk=None):
        """Get notes in a category."""
        category = self.get_object()
        notes = Note.objects.filter(category=category, status='published')
        serializer = NoteListSerializer(notes, many=True)
        return Response(serializer.data)


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for tags."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most popular tags."""
        tags = Tag.objects.annotate(note_count=Count('notes'))\
                          .order_by('-note_count')[:20]
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def notes(self, request, pk=None):
        """Get notes with this tag."""
        tag = self.get_object()
        notes = Note.objects.filter(tags=tag, status='published')
        serializer = NoteListSerializer(notes, many=True)
        return Response(serializer.data)


class AttachmentViewSet(viewsets.ModelViewSet):
    """ViewSet for file attachments."""
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class ResearchNoteViewSet(viewsets.ModelViewSet):
    """ViewSet for research notes."""
    queryset = ResearchNote.objects.select_related('author', 'note').all()
    serializer_class = ResearchNoteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ResearchNoteFilter
    search_fields = ['title', 'content', 'key_findings']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def add_source(self, request, pk=None):
        """Add a source to research note."""
        research_note = self.get_object()
        source = request.data.get('source', '')
        if source:
            sources = research_note.sources or []
            sources.append(source)
            research_note.sources = sources
            research_note.save()
        return Response({'sources': research_note.sources})

    @action(detail=True, methods=['post'])
    def add_finding(self, request, pk=None):
        """Add a key finding."""
        research_note = self.get_object()
        finding = request.data.get('finding', '')
        if finding:
            findings = research_note.key_findings or []
            findings.append(finding)
            research_note.key_findings = findings
            research_note.save()
        return Response({'key_findings': research_note.key_findings})

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Reminder, NoteTemplate, Comment, Share, CustomSchema
from .serializers import ReminderSerializer, NoteTemplateSerializer, CommentSerializer, ShareSerializer

class ReminderViewSet(viewsets.ModelViewSet):
    queryset = Reminder.objects.all()
    serializer_class = ReminderSerializer

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer

    def get_queryset(self):
        note_id = self.kwargs['note_pk']
        return Comment.objects.filter(note_id=note_id, parent=None)  # top‑level

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, note_id=self.kwargs['note_pk'])

class ShareViewSet(viewsets.ModelViewSet):
    serializer_class = ShareSerializer

    def get_queryset(self):
        return Share.objects.filter(note__author=self.request.user)

    def perform_create(self, serializer):
        serializer.save()

class TemplateViewSet(viewsets.ModelViewSet):
    queryset = NoteTemplate.objects.all()
    serializer_class = NoteTemplateSerializer

class SchemaViewSet(viewsets.ModelViewSet):
    queryset = CustomSchema.objects.all()
    serializer_class = CustomSchemaSerializer


from .models import APIKey
from .serializers import APIKeySerializer

class APIKeyViewSet(viewsets.ModelViewSet):
    serializer_class = APIKeySerializer

    def get_queryset(self):
        return APIKey.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        raw_key = APIKeyService().generate_key(self.request.user, serializer.validated_data['name'], serializer.validated_data.get('scopes', []))
        # return the raw key in response (only time it's visible)
        return Response({'raw_key': raw_key, 'key': serializer.data}, status=status.HTTP_201_CREATED)
