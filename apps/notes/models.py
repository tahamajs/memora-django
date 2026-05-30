"""
Note models for Local Notion Clone.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import MinLengthValidator, MaxLengthValidator
import uuid

User = get_user_model()


class Category(models.Model):
    """Note categories for organization."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    color = models.CharField(max_length=7, default='#4F46E5')
    icon = models.CharField(max_length=10, default='📁')
    description = models.TextField(blank=True, default='')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='children'
    )
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['sort_order', 'name']),
            models.Index(fields=['slug']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def note_count(self):
        return self.notes.count()


class Tag(models.Model):
    """Tags for flexible note organization."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    color = models.CharField(max_length=7, default='#808080')
    description = models.TextField(blank=True, default='')
    usage_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-usage_count', 'name']
        indexes = [
            models.Index(fields=['-usage_count']),
            models.Index(fields=['name']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.name}"

    def update_usage_count(self):
        self.usage_count = self.notes.count()
        self.save(update_fields=['usage_count'])


class Note(models.Model):
    """Main note model with full feature support."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(
        max_length=500,
        default='Untitled',
        validators=[MinLengthValidator(1), MaxLengthValidator(500)]
    )
    content = models.TextField(blank=True, default='')
    markdown_content = models.TextField(blank=True, default='')
    html_content = models.TextField(blank=True, default='')

    # Organization
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notes'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='notes')
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )

    # User relations
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notes'
    )
    collaborators = models.ManyToManyField(
        User, blank=True, related_name='collaborating_notes'
    )

    # State flags
    is_favorite = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    # Content metadata
    word_count = models.IntegerField(default=0)
    reading_time = models.IntegerField(default=0)  # in minutes
    excerpt = models.TextField(blank=True, default='')

    # AI generated
    ai_summary = models.TextField(blank=True, default='')
    ai_sentiment = models.CharField(max_length=20, blank=True, default='')
    ai_keywords = models.JSONField(default=list, blank=True)

    # Git sync
    git_commit_hash = models.CharField(max_length=40, blank=True, default='')
    git_branch = models.CharField(max_length=100, blank=True, default='main')

    # Version tracking
    version = models.IntegerField(default=1)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-is_pinned', '-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['status', '-updated_at']),
            models.Index(fields=['category', '-updated_at']),
            models.Index(fields=['author', '-updated_at']),
            models.Index(fields=['is_favorite']),
            models.Index(fields=['is_pinned']),
            models.Index(fields=['priority']),
        ]

    def save(self, *args, **kwargs):
        # Update word count and reading time
        if self.content:
            self.word_count = len(self.content.split())
            self.reading_time = max(1, self.word_count // 200)

            # Generate excerpt
            self.excerpt = self.content[:200] + '...' if len(self.content) > 200 else self.content

            # Generate HTML from markdown
            if self.markdown_content:
                import markdown
                self.html_content = markdown.markdown(
                    self.markdown_content,
                    extensions=[
                        'markdown.extensions.extra',
                        'markdown.extensions.codehilite',
                        'markdown.extensions.toc',
                        'markdown.extensions.tables',
                        'markdown.extensions.fenced_code',
                    ]
                )

        # Set published date
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

        # Increment version
        if self.pk:
            self.version += 1

        super().save(*args, **kwargs)

        # Update tag usage counts
        for tag in self.tags.all():
            tag.update_usage_count()

    def __str__(self):
        return self.title or 'Untitled'

    @property
    def is_archived(self):
        return self.status == self.Status.ARCHIVED

    @property
    def tag_list(self):
        return list(self.tags.values_list('name', flat=True))

    @property
    def collaborator_list(self):
        return list(self.collaborators.values_list('username', flat=True))

    def archive(self):
        self.status = self.Status.ARCHIVED
        self.save(update_fields=['status', 'updated_at'])

    def unarchive(self):
        self.status = self.Status.DRAFT
        self.save(update_fields=['status', 'updated_at'])

    def toggle_favorite(self):
        self.is_favorite = not self.is_favorite
        self.save(update_fields=['is_favorite'])

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        self.save(update_fields=['is_pinned'])

    def add_tag(self, tag_name):
        tag, created = Tag.objects.get_or_create(name=tag_name.lower().strip())
        self.tags.add(tag)
        tag.update_usage_count()

    def remove_tag(self, tag_name):
        try:
            tag = Tag.objects.get(name=tag_name.lower().strip())
            self.tags.remove(tag)
            tag.update_usage_count()
        except Tag.DoesNotExist:
            pass

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('note-detail', kwargs={'pk': self.pk})


class NoteVersion(models.Model):
    """Version history for notes."""
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    title = models.CharField(max_length=500)
    content = models.TextField()
    commit_message = models.CharField(max_length=500, blank=True, default='')
    commit_hash = models.CharField(max_length=40, blank=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']
        unique_together = ['note', 'version_number']
        indexes = [
            models.Index(fields=['note', '-version_number']),
        ]

    def __str__(self):
        return f"{self.note.title} - v{self.version_number}"


class Attachment(models.Model):
    """File attachments for notes."""
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    filename = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    size = models.BigIntegerField()
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.original_name

    def save(self, *args, **kwargs):
        if not self.filename:
            self.filename = self.file.name
        if not self.original_name:
            self.original_name = self.file.name
        super().save(*args, **kwargs)


class ResearchNote(models.Model):
    """Dedicated research notes with methodology tracking."""

    class Status(models.TextChoices):
        PLANNING = 'planning', 'Planning'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        PUBLISHED = 'published', 'Published'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    content = models.TextField()
    note = models.ForeignKey(
        Note, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='research_notes'
    )

    # Research fields
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IN_PROGRESS
    )
    sources = models.JSONField(default=list, blank=True)
    key_findings = models.JSONField(default=list, blank=True)
    methodology = models.TextField(blank=True, default='')
    hypothesis = models.TextField(blank=True, default='')
    conclusions = models.TextField(blank=True, default='')

    # Metadata
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


import uuid
from django.db import models
from django.conf import settings

class Reminder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    note = models.ForeignKey('Note', on_delete=models.CASCADE, related_name='reminders')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    remind_at = models.DateTimeField()
    sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['remind_at']

class NoteTemplate(models.Model):
    name = models.CharField(max_length=200)
    content = models.TextField()
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class CustomSchema(models.Model):
    category = models.OneToOneField('Category', on_delete=models.CASCADE, related_name='schema')
    definition = models.JSONField(default=dict)   # JSON Schema

class Share(models.Model):
    note = models.ForeignKey('Note', on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    permission = models.CharField(max_length=20, choices=[('read','Read'),('write','Write')], default='read')
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['note', 'user']

class NoteIntegration(models.Model):
    note = models.ForeignKey('Note', on_delete=models.CASCADE, related_name='integrations')
    platform = models.CharField(max_length=50)   # 'slack', 'discord'
    webhook_url = models.URLField()
    events = models.JSONField(default=list)       # ['created','updated']

class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    note = models.ForeignKey('Note', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=100)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class APIKey(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100)
    key_hash = models.CharField(max_length=64, unique=True)
    scopes = models.CharField(max_length=200)   # comma‑separated
    revoked = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
