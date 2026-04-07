from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Event
from .serializers import EventSerializer


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["event_type", "course"]
    search_fields = ["title"]
    ordering_fields = ["start_date", "end_date"]

    def get_queryset(self):
        user = self.request.user
        if user.role in ("admin", "manager"):
            return Event.objects.select_related("course", "user").all()
        enrolled_courses = user.enrollments.values_list("course_id", flat=True)
        return Event.objects.select_related("course", "user").filter(
            Q(user=user)
            | Q(event_type=Event.EventType.SITE)
            | Q(event_type=Event.EventType.COURSE, course_id__in=enrolled_courses)
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
