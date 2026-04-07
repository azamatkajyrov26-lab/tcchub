from rest_framework import serializers

from .models import CertificateTemplate, IssuedCertificate


class CertificateTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateTemplate
        fields = ["id", "course", "name", "template_html", "is_active"]
        read_only_fields = ["id"]


class IssuedCertificateSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = IssuedCertificate
        fields = [
            "id", "template", "user", "user_name", "course", "course_title",
            "issued_at", "certificate_number", "pdf_file",
        ]
        read_only_fields = ["id", "issued_at", "certificate_number"]
