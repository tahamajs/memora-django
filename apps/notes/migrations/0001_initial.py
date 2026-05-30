from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=100, unique=True)),
                ('color', models.CharField(default='#4F46E5', max_length=7)),
                ('icon', models.CharField(default='📁', max_length=10)),
                ('description', models.TextField(blank=True, default='')),
                ('sort_order', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='notes.category')),
            ],
            options={'verbose_name_plural': 'categories', 'ordering': ['sort_order', 'name']},
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=50, unique=True)),
                ('color', models.CharField(default='#808080', max_length=7)),
                ('description', models.TextField(blank=True, default='')),
                ('usage_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-usage_count', 'name']},
        ),
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(default='Untitled', max_length=500)),
                ('content', models.TextField(blank=True, default='')),
                ('markdown_content', models.TextField(blank=True, default='')),
                ('html_content', models.TextField(blank=True, default='')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Published'), ('archived', 'Archived')], default='draft', max_length=20)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', max_length=10)),
                ('is_favorite', models.BooleanField(default=False)),
                ('is_pinned', models.BooleanField(default=False)),
                ('is_locked', models.BooleanField(default=False)),
                ('word_count', models.IntegerField(default=0)),
                ('reading_time', models.IntegerField(default=0)),
                ('excerpt', models.TextField(blank=True, default='')),
                ('ai_summary', models.TextField(blank=True, default='')),
                ('ai_sentiment', models.CharField(blank=True, default='', max_length=20)),
                ('ai_keywords', models.JSONField(blank=True, default=list)),
                ('git_commit_hash', models.CharField(blank=True, default='', max_length=40)),
                ('git_branch', models.CharField(blank=True, default='main', max_length=100)),
                ('version', models.IntegerField(default=1)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to=settings.AUTH_USER_MODEL)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notes', to='notes.category')),
                ('collaborators', models.ManyToManyField(blank=True, related_name='collaborating_notes', to=settings.AUTH_USER_MODEL)),
                ('tags', models.ManyToManyField(blank=True, related_name='notes', to='notes.tag')),
            ],
            options={'ordering': ['-is_pinned', '-updated_at']},
        ),
        migrations.CreateModel(
            name='NoteVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_number', models.IntegerField()),
                ('title', models.CharField(max_length=500)),
                ('content', models.TextField()),
                ('commit_message', models.CharField(blank=True, default='', max_length=500)),
                ('commit_hash', models.CharField(blank=True, default='', max_length=40)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('note', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='notes.note')),
            ],
            options={'ordering': ['-version_number'], 'unique_together': {('note', 'version_number')}},
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='attachments/%Y/%m/%d/')),
                ('filename', models.CharField(max_length=255)),
                ('original_name', models.CharField(max_length=255)),
                ('mime_type', models.CharField(max_length=100)),
                ('size', models.BigIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('note', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='notes.note')),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
