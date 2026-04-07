from django.conf import settings
from django.db import models


class Event(models.Model):
    class EventType(models.TextChoices):
        COURSE = "course", "Course Event"
        USER = "user", "User Event"
        SITE = "site", "Site Event"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=10, choices=EventType.choices, default=EventType.USER)
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, null=True, blank=True, related_name="events"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="events"
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    repeat = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["start_date"]

    def __str__(self):
        return self.title
