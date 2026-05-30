from rest_framework import viewsets
from .models import Calendar, CalendarEvent
from .serializers import CalendarSerializer, CalendarEventSerializer

class CalendarViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarSerializer
    def get_queryset(self): return Calendar.objects.filter(user=self.request.user)
    def perform_create(self, serializer): serializer.save(user=self.request.user)

class CalendarEventViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarEventSerializer
    def get_queryset(self): return CalendarEvent.objects.filter(calendar__user=self.request.user)
