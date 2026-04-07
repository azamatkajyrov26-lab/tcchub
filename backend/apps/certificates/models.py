import uuid

from django.conf import settings
from django.db import models


class CertificateTemplate(models.Model):
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="certificate_templates"
    )
    name = models.CharField(max_length=255)
    template_html = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.course.title})"


class IssuedCertificate(models.Model):
    template = models.ForeignKey(
        CertificateTemplate, on_delete=models.CASCADE, related_name="issued_certificates"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates"
    )
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="issued_certificates"
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    certificate_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    pdf_file = models.FileField(upload_to="certificates/%Y/%m/", blank=True)

    class Meta:
        unique_together = ["user", "course"]
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Certificate {self.certificate_number} - {self.user}"
