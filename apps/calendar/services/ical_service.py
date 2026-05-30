import requests
from icalendar import Calendar as iCal
from datetime import datetime
from ..models import CalendarEvent

class ICalService:
    def sync_from_url(self, calendar, url):
        resp = requests.get(url, timeout=10)
        ical = iCal.from_ical(resp.content)
        for component in ical.walk('VEVENT'):
            uid = str(component.get('uid'))
            start = component.get('dtstart').dt
            end = component.get('dtend').dt
            summary = str(component.get('summary', ''))
            if isinstance(start, datetime) and not CalendarEvent.objects.filter(calendar=calendar, external_uid=uid).exists():
                CalendarEvent.objects.create(
                    calendar=calendar, title=summary[:500],
                    start=start, end=end, description=str(component.get('description','')),
                    location=str(component.get('location','')), external_uid=uid
                )
        calendar.last_synced = timezone.now()
        calendar.save()
