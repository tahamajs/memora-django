from django.contrib import admin
from django.utils.html import format_html
from .models import Note, Category, Tag, NoteVersion, Attachment, ResearchNote

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'note_count', 'sort_order', 'is_active']
    list_editable = ['sort_order', 'is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def note_count(self, obj):
        return obj.notes.count()
    note_count.short_description = 'Number of Notes'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'usage_count']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


class NoteVersionInline(admin.TabularInline):
    model = NoteVersion
    extra = 0
    readonly_fields = ['version_number', 'created_at']
    can_delete = False


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'priority', 'is_favorite', 'is_pinned', 'word_count', 'updated_at']
    list_filter = ['status', 'priority', 'category', 'is_favorite', 'is_pinned', 'created_at']
    search_fields = ['title', 'content', 'tags__name']
    readonly_fields = ['id', 'word_count', 'reading_time', 'created_at', 'updated_at', 'git_commit_hash']
    inlines = [NoteVersionInline, AttachmentInline]
    date_hierarchy = 'created_at'
    actions = ['make_published', 'make_archived', 'mark_as_favorite']

    def make_published(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} notes marked as published.')
    make_published.short_description = 'Mark selected notes as published'

    def make_archived(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} notes archived.')
    make_archived.short_description = 'Archive selected notes'

    def mark_as_favorite(self, request, queryset):
        updated = queryset.update(is_favorite=True)
        self.message_user(request, f'{updated} notes added to favorites.')
    mark_as_favorite.short_description = 'Mark selected notes as favorite'

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'content', 'markdown_content', 'author')
        }),
        ('Organization', {
            'fields': ('category', 'tags', 'collaborators')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'is_favorite', 'is_pinned', 'is_locked')
        }),
        ('AI & Git', {
            'fields': ('ai_summary', 'ai_sentiment', 'ai_keywords', 'git_commit_hash', 'git_branch')
        }),
        ('Metadata', {
            'fields': ('word_count', 'reading_time', 'version', 'metadata', 'created_at', 'updated_at', 'published_at')
        }),
    )


@admin.register(ResearchNote)
class ResearchNoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']