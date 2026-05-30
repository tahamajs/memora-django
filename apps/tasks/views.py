from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import TaskList, Task
from .serializers import TaskListSerializer, TaskSerializer

class TaskListViewSet(viewsets.ModelViewSet):
    serializer_class = TaskListSerializer

    def get_queryset(self):
        return TaskList.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(list__user=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        task = self.get_object()
        if task.status == Task.Status.DONE:
            task.status = Task.Status.TODO
            task.completed_at = None
        else:
            task.mark_complete()
        task.save()
        return Response(TaskSerializer(task).data)

    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        new_order = request.data.get('order')
        task = self.get_object()
        task.order = new_order
        task.save(update_fields=['order'])
        return Response({'status': 'reordered'})

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple tasks from a list (used by AI task extraction)"""
        tasks_data = request.data.get('tasks', [])
        list_id = request.data.get('list_id')
        created = []
        for item in tasks_data:
            serializer = self.get_serializer(data={
                'title': item.get('task') or item.get('title'),
                'list': list_id,
                'priority': item.get('priority', 'medium'),
            })
            serializer.is_valid(raise_exception=True)
            serializer.save()
            created.append(serializer.data)
        return Response(created, status=status.HTTP_201_CREATED)
