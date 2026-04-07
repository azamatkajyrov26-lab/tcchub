from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsTeacherOrAbove

from .models import CertificateTemplate, IssuedCertificate
from .serializers import CertificateTemplateSerializer, IssuedCertificateSerializer


class CertificateTemplateViewSet(viewsets.ModelViewSet):
    queryset = CertificateTemplate.objects.select_related("course").all()
    serializer_class = CertificateTemplateSerializer
    permission_classes = [IsTeacherOrAbove]
    filterset_fields = ["course", "is_active"]


class IssuedCertificateViewSet(viewsets.ModelViewSet):
    serializer_class = IssuedCertificateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["course", "user"]
    search_fields = ["certificate_number"]

    def get_queryset(self):
        user = self.request.user
        if user.role in ("admin", "manager", "teacher"):
            return IssuedCertificate.objects.select_related("user", "course", "template").all()
        return IssuedCertificate.objects.select_related("course", "template").filter(user=user)
