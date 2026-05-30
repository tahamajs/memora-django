from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notes', '0001_initial'),
    ]
    operations = [
        migrations.CreateModel(
            name='ResearchNote',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=500)),
                ('content', models.TextField()),
                ('status', models.CharField(choices=[('planning', 'Planning'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('published', 'Published')], default='in_progress', max_length=20)),
                ('sources', models.JSONField(blank=True, default=list)),
                ('key_findings', models.JSONField(blank=True, default=list)),
                ('methodology', models.TextField(blank=True, default='')),
                ('hypothesis', models.TextField(blank=True, default='')),
                ('conclusions', models.TextField(blank=True, default='')),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('note', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='research_notes', to='notes.note')),
            ],
            options={'ordering': ['-updated_at']},
        ),
    ]
