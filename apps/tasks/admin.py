from django.contrib import admin
from .models import TaskList, Task

@admin.register(TaskList)
class TaskListAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'list', 'status', 'priority', 'due_date', 'assigned_to']
    list_filter = ['status', 'priority', 'list']
    search_fields = ['title', 'description']
