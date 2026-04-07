from django.conf import settings
from django.db import models


class Activity(models.Model):
    class ActivityType(models.TextChoices):
        LESSON = "lesson", "Lesson"
        VIDEO = "video", "Video"
        DOCUMENT = "document", "Document"
        FOLDER = "folder", "Folder"
        RESOURCE = "resource", "Resource"
        URL = "url", "URL"
        QUIZ = "quiz", "Quiz"
        ASSIGNMENT = "assignment", "Assignment"
        FORUM = "forum", "Forum"
        GLOSSARY = "glossary", "Glossary"
        H5P = "h5p", "H5P"

    class CompletionType(models.TextChoices):
        MANUAL = "manual", "Manual"
        AUTOMATIC = "automatic", "Automatic"
        CONDITION = "condition", "Condition-based"

    section = models.ForeignKey(
        "courses.Section", on_delete=models.CASCADE, related_name="activities"
    )
    activity_type = models.CharField(max_length=20, choices=ActivityType.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    completion_type = models.CharField(
        max_length=20, choices=CompletionType.choices, default=CompletionType.MANUAL
    )
    due_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "Activities"

    def __str__(self):
        return f"{self.title} ({self.get_activity_type_display()})"


class Resource(models.Model):
    activity = models.OneToOneField(Activity, on_delete=models.CASCADE, related_name="resource")
    file = models.FileField(upload_to="resources/%Y/%m/", max_length=255, blank=True)
    file_type = models.CharField(max_length=50, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    external_url = models.URLField(max_length=1024, blank=True)

    def __str__(self):
        return f"Resource: {self.activity.title}"


class Folder(models.Model):
    activity = models.OneToOneField(Activity, on_delete=models.CASCADE, related_name="folder")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class FolderFile(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="folders/%Y/%m/")
    original_name = models.CharField(max_length=255)

    def __str__(self):
        return self.original_name


class ActivityCompletion(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_completions"
    )
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="completions")
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["user", "activity"]

    def __str__(self):
        return f"{self.user} - {self.activity} ({'done' if self.completed else 'pending'})"


class VideoTimestamp(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="timestamps")
    title = models.CharField(max_length=255)
    time_seconds = models.PositiveIntegerField(help_text="Timestamp in seconds")
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["time_seconds"]

    def __str__(self):
        mins, secs = divmod(self.time_seconds, 60)
        return f"{mins:02d}:{secs:02d} — {self.title}"


class VideoProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="video_progress"
    )
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="video_progress")
    current_time = models.PositiveIntegerField(default=0, help_text="Current position in seconds")
    duration = models.PositiveIntegerField(default=0, help_text="Total video duration in seconds")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "activity"]

    def __str__(self):
        return f"{self.user} - {self.activity} @ {self.current_time}s"
