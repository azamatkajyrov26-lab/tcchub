from django.conf import settings
from django.db import models


class NotificationType(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class NotificationPreference(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preferences"
    )
    notification_type = models.ForeignKey(
        NotificationType, on_delete=models.CASCADE, related_name="preferences"
    )
    email_enabled = models.BooleanField(default=True)
    web_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=False)

    class Meta:
        unique_together = ["user", "notification_type"]

    def __str__(self):
        return f"{self.user} - {self.notification_type}"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.ForeignKey(
        NotificationType, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.URLField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} -> {self.user}"
