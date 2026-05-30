from apscheduler.schedulers.background import BackgroundScheduler
from django.core.mail import send_mail
from datetime import datetime

scheduler = BackgroundScheduler()

def check_reminders():
    from apps.notes.models import Reminder
    now = datetime.now()
    reminders = Reminder.objects.filter(remind_at__lte=now, sent=False)
    for reminder in reminders:
        send_mail(
            f'Reminder: {reminder.note.title}',
            f'Your note "{reminder.note.title}" is due.',
            'noreply@memora.io',
            [reminder.user.email],
        )
        reminder.sent = True
        reminder.save()

scheduler.add_job(check_reminders, 'interval', minutes=1)
scheduler.start()
