from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskListViewSet, TaskViewSet

router = DefaultRouter()
router.register(r'lists', TaskListViewSet, basename='tasklist')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
]
