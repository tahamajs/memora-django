from django.core.serializers import serialize
from apps.notes.models import Note, Comment, Attachment
from apps.users.models import User
import json

class GDPRService:
    def export_user_data(self, user: User) -> dict:
        notes = Note.objects.filter(author=user)
        comments = Comment.objects.filter(user=user)
        attachments = Attachment.objects.filter(note__author=user)

        return {
            "user": {
                "email": user.email,
                "username": user.username,
                "date_joined": user.date_joined.isoformat(),
            },
            "notes": json.loads(serialize('json', notes)),
            "comments": json.loads(serialize('json', comments)),
            "attachments": json.loads(serialize('json', attachments)),
        }

    def delete_account(self, user: User) -> None:
        # Anonymize or delete data
        user.email = f"deleted_{user.pk}@anonymous.com"
        user.username = f"deleted_{user.pk}"
        user.is_active = False
        user.save()
        Note.objects.filter(author=user).delete()
