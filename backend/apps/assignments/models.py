from django.conf import settings
from django.db import models


class Assignment(models.Model):
    activity = models.OneToOneField(
        "content.Activity", on_delete=models.CASCADE, related_name="assignment"
    )
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    allow_late = models.BooleanField(default=False)
    late_penalty = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, help_text="Penalty percentage per day"
    )
    submission_types = models.JSONField(
        default=list, help_text="Allowed submission types: file, text, url"
    )
    max_file_size = models.PositiveIntegerField(default=10485760, help_text="Max file size in bytes")
    max_files = models.PositiveIntegerField(default=5)

    def __str__(self):
        return f"Assignment: {self.activity.title}"


class Submission(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        GRADED = "graded", "Graded"

    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="submissions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="graded_submissions",
    )
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.user} - {self.assignment} ({self.status})"


class SubmissionFile(models.Model):
    submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name="files"
    )
    file = models.FileField(upload_to="submissions/%Y/%m/")
    original_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name
