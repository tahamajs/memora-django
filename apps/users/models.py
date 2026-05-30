"""
User models for Local Notion Clone.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


class UserManager(BaseUserManager):
    """Custom user manager."""
    
    def create_user(self, email, username, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not username:
            raise ValueError(_('The Username field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    """Custom user model with additional fields."""
    
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        EDITOR = 'editor', _('Editor')
        AUTHOR = 'author', _('Author')
        VIEWER = 'viewer', _('Viewer')
    
    class Theme(models.TextChoices):
        LIGHT = 'light', _('Light')
        DARK = 'dark', _('Dark')
        SYSTEM = 'system', _('System')
    
    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    
    # Profile fields
    bio = models.TextField(_('bio'), max_length=500, blank=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', blank=True, null=True)
    website = models.URLField(_('website'), blank=True)
    location = models.CharField(_('location'), max_length=100, blank=True)
    company = models.CharField(_('company'), max_length=100, blank=True)
    job_title = models.CharField(_('job title'), max_length=100, blank=True)
    
    # Preferences
    role = models.CharField(
        _('role'), max_length=20, choices=Role.choices, default=Role.AUTHOR
    )
    theme = models.CharField(
        _('theme'), max_length=10, choices=Theme.choices, default=Theme.SYSTEM
    )
    language = models.CharField(_('language'), max_length=10, default='en')
    timezone = models.CharField(_('timezone'), max_length=50, default='UTC')
    
    # Settings
    email_notifications = models.BooleanField(_('email notifications'), default=True)
    ai_features_enabled = models.BooleanField(_('AI features'), default=True)
    git_sync_enabled = models.BooleanField(_('Git sync'), default=False)
    auto_save = models.BooleanField(_('auto save'), default=True)
    auto_save_interval = models.IntegerField(_('auto save interval'), default=30)  # seconds
    
    # API access
    api_key = models.CharField(_('API key'), max_length=64, unique=True, blank=True, null=True)
    api_calls_count = models.IntegerField(_('API calls'), default=0)
    api_calls_limit = models.IntegerField(_('API calls limit'), default=1000)
    
    # Activity tracking
    last_active = models.DateTimeField(_('last active'), null=True, blank=True)
    total_notes_created = models.IntegerField(_('total notes'), default=0)
    total_words_written = models.BigIntegerField(_('total words'), default=0)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return self.username or self.email
    
    def get_full_name(self):
        """Return full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_short_name(self):
        """Return short name."""
        return self.first_name or self.username
    
    def update_last_active(self):
        """Update last active timestamp."""
        self.last_active = timezone.now()
        self.save(update_fields=['last_active'])
    
    def can_use_ai(self) -> bool:
        """Check if user can use AI features."""
        return self.ai_features_enabled and self.api_calls_count < self.api_calls_limit
    
    def increment_api_calls(self, count: int = 1):
        """Increment API calls count."""
        self.api_calls_count += count
        self.save(update_fields=['api_calls_count'])
    
    def reset_api_calls(self):
        """Reset API calls count."""
        self.api_calls_count = 0
        self.save(update_fields=['api_calls_count'])
    
    def generate_api_key(self):
        """Generate new API key."""
        import secrets
        self.api_key = secrets.token_hex(32)
        self.save(update_fields=['api_key'])
        return self.api_key
    
    @property
    def note_count(self):
        """Get total notes count."""
        return self.notes.count()
    
    @property
    def storage_used(self):
        """Calculate storage used in bytes."""
        total_size = 0
        for note in self.notes.all():
            total_size += len(note.content.encode('utf-8'))
            for attachment in note.attachments.all():
                total_size += attachment.size
        return total_size


class UserProfile(models.Model):
    """Extended user profile with additional settings."""
    
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    
    # Editor preferences
    editor_font_size = models.IntegerField(default=16)
    editor_font_family = models.CharField(max_length=50, default='monospace')
    editor_line_numbers = models.BooleanField(default=False)
    editor_spell_check = models.BooleanField(default=True)
    editor_tab_size = models.IntegerField(default=4)
    editor_word_wrap = models.BooleanField(default=True)
    
    # Display preferences
    show_word_count = models.BooleanField(default=True)
    show_reading_time = models.BooleanField(default=True)
    default_view = models.CharField(
        max_length=10, 
        choices=[('edit', 'Edit'), ('preview', 'Preview'), ('split', 'Split')],
        default='edit'
    )
    
    # Notification preferences
    notify_on_share = models.BooleanField(default=True)
    notify_on_comment = models.BooleanField(default=True)
    notify_on_mention = models.BooleanField(default=True)
    notify_digest = models.CharField(
        max_length=10,
        choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('never', 'Never')],
        default='daily'
    )
    
    # Backup preferences
    auto_backup = models.BooleanField(default=False)
    backup_frequency = models.CharField(
        max_length=10,
        choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')],
        default='daily'
    )
    backup_location = models.CharField(max_length=255, blank=True)
    
    # Social links
    github_username = models.CharField(max_length=100, blank=True)
    twitter_username = models.CharField(max_length=100, blank=True)
    linkedin_url = models.URLField(blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"


class UserActivity(models.Model):
    """Track user activity."""
    
    class ActionType(models.TextChoices):
        CREATE = 'create', 'Created'
        UPDATE = 'update', 'Updated'
        DELETE = 'delete', 'Deleted'
        VIEW = 'view', 'Viewed'
        SEARCH = 'search', 'Searched'
        EXPORT = 'export', 'Exported'
        SHARE = 'share', 'Shared'
        LOGIN = 'login', 'Logged In'
        LOGOUT = 'logout', 'Logged Out'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=20, choices=ActionType.choices)
    entity_type = models.CharField(max_length=50)  # 'note', 'tag', 'category', etc.
    entity_id = models.CharField(max_length=100, null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'user activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.action} {self.entity_type} at {self.created_at}"