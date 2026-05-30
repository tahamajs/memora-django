from django.http import JsonResponse
from apps.notes.models import Note, Attachment

class QuotaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check note count
            note_limit = getattr(settings, 'QUOTA_MAX_NOTES', 100)
            if Note.objects.filter(author=request.user).count() >= note_limit:
                return JsonResponse({'error': 'Note quota exceeded'}, status=402)

            # Check storage
            storage_limit = getattr(settings, 'QUOTA_MAX_STORAGE_MB', 100) * 1024 * 1024
            total_size = Attachment.objects.filter(
                note__author=request.user
            ).aggregate(total=models.Sum('size'))['total'] or 0
            if total_size >= storage_limit:
                return JsonResponse({'error': 'Storage quota exceeded'}, status=402)

        return self.get_response(request)
