from rest_framework import serializers
from .models import Calendar, CalendarEvent

class CalendarSerializer(serializers.ModelSerializer):
    event_count = serializers.SerializerMethodField()

    class Meta:
        model = Calendar
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'last_synced']

    def get_event_count(self, obj):
        return obj.events.count()

class CalendarEventSerializer(serializers.ModelSerializer):
    note_title = serializers.SerializerMethodField()

    class Meta:
        model = CalendarEvent
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_note_title(self, obj):
        return obj.note.title if obj.note else None
