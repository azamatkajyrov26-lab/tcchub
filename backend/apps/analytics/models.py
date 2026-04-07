from django.conf import settings
from django.db import models


class UserActivity(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activities"
    )
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "User activities"

    def __str__(self):
        return f"{self.user} - {self.action} at {self.created_at}"


class CourseReport(models.Model):
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="reports"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_reports"
    )
    total_time = models.PositiveIntegerField(default=0, help_text="Total time in seconds")
    last_access = models.DateTimeField(null=True, blank=True)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = ["course", "user"]

    def __str__(self):
        return f"{self.user} - {self.course}: {self.completion_percentage}%"


class LoginLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="login_logs"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    logged_in_at = models.DateTimeField(auto_now_add=True)
    logged_out_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-logged_in_at"]

    def __str__(self):
        return f"{self.user} - {self.logged_in_at}"
