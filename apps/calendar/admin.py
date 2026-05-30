from django.contrib import admin
from .models import Calendar, CalendarEvent

@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_primary']

@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'calendar', 'start', 'end']
