from rest_framework import serializers
from .models import TaskList, Task

class TaskSerializer(serializers.ModelSerializer):
    source_note_title = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']

    def get_source_note_title(self, obj):
        return obj.source_note.title if obj.source_note else None


class TaskListSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()
    completed_count = serializers.SerializerMethodField()

    class Meta:
        model = TaskList
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'user']

    def get_task_count(self, obj):
        return obj.tasks.count()

    def get_completed_count(self, obj):
        return obj.tasks.filter(status='done').count()
