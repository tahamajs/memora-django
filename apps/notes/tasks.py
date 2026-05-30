from celery import shared_task
from datetime import datetime
from django.core.mail import send_mail
from .models import Reminder

@shared_task
def check_reminders():
    now = datetime.now()
    reminders = Reminder.objects.filter(remind_at__lte=now, sent=False)
    for reminder in reminders:
        send_mail(
            f'Reminder: {reminder.note.title}',
            f'Your note "{reminder.note.title}" is due.',
            'noreply@memora.io',
            [reminder.user.email],
            fail_silently=False,
        )
        reminder.sent = True
        reminder.save()
