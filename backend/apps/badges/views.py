from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsTeacherOrAbove

from .models import Badge, BadgeIssuance
from .serializers import BadgeIssuanceSerializer, BadgeSerializer


class BadgeViewSet(viewsets.ModelViewSet):
    queryset = Badge.objects.select_related("course", "created_by").all()
    serializer_class = BadgeSerializer
    permission_classes = [IsTeacherOrAbove]
    filterset_fields = ["course", "is_active"]
    search_fields = ["name"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class BadgeIssuanceViewSet(viewsets.ModelViewSet):
    serializer_class = BadgeIssuanceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["badge", "user"]

    def get_queryset(self):
        user = self.request.user
        if user.role in ("admin", "manager", "teacher"):
            return BadgeIssuance.objects.select_related("badge", "user", "issued_by").all()
        return BadgeIssuance.objects.select_related("badge", "issued_by").filter(user=user)

    def perform_create(self, serializer):
        serializer.save(issued_by=self.request.user)
