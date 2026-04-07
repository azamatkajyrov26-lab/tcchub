from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsAdmin

from .models import CourseReport, LoginLog, UserActivity
from .serializers import CourseReportSerializer, LoginLogSerializer, UserActivitySerializer


class UserActivityViewSet(viewsets.ModelViewSet):
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["user", "action", "object_type"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.role in ("admin", "manager"):
            return UserActivity.objects.select_related("user").all()
        return UserActivity.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CourseReportViewSet(viewsets.ModelViewSet):
    serializer_class = CourseReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["course", "user"]
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if user.role in ("admin", "manager", "teacher"):
            return CourseReport.objects.select_related("course", "user").all()
        return CourseReport.objects.select_related("course").filter(user=user)


class LoginLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LoginLogSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["user"]
    ordering_fields = ["logged_in_at"]

    def get_queryset(self):
        return LoginLog.objects.select_related("user").all()
