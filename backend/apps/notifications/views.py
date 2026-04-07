from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin

from .models import Notification, NotificationPreference, NotificationType
from .serializers import (
    NotificationPreferenceSerializer,
    NotificationSerializer,
    NotificationTypeSerializer,
)


class NotificationTypeViewSet(viewsets.ModelViewSet):
    queryset = NotificationType.objects.all()
    serializer_class = NotificationTypeSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["category"]
    search_fields = ["name", "code"]


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationPreference.objects.select_related(
            "notification_type"
        ).filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["notification_type", "is_read"]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Notification.objects.select_related(
            "notification_type"
        ).filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        count = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"marked_read": count})

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"unread_count": count})
