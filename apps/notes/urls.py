from django.urls import path, include
from rest_framework_nested import routers

router = routers.DefaultRouter()
router.register(r'notes', NoteViewSet)
router.register(r'templates', TemplateViewSet)
router.register(r'schemas', SchemaViewSet)

notes_router = routers.NestedDefaultRouter(router, r'notes', lookup='note')
notes_router.register(r'comments', CommentViewSet, basename='note-comments')
notes_router.register(r'reminders', ReminderViewSet, basename='note-reminders')
notes_router.register(r'shares', ShareViewSet, basename='note-shares')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(notes_router.urls)),
]

router.register(r'api-keys', APIKeyViewSet, basename='api-keys')
