from django.conf import settings
from django.db import models


class Badge(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="badges/", blank=True)
    criteria = models.JSONField(default=dict, blank=True)
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, null=True, blank=True, related_name="badges"
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_badges"
    )

    def __str__(self):
        return self.name


class BadgeIssuance(models.Model):
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="issuances")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges_earned"
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="badges_issued",
    )

    class Meta:
        unique_together = ["badge", "user"]
        ordering = ["-issued_at"]

    def __str__(self):
        return f"{self.user} earned {self.badge}"
