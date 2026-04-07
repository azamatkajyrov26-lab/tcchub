from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Course(models.Model):
    class EnrollmentType(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        KEY = "key", "Enrollment Key"

    class Format(models.TextChoices):
        TOPICS = "topics", "Topics"
        WEEKS = "weeks", "Weeks"

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=500, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses"
    )
    cover_image = models.ImageField(upload_to="courses/covers/%Y/%m/", blank=True)
    duration_hours = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_courses"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    enrollment_type = models.CharField(
        max_length=10, choices=EnrollmentType.choices, default=EnrollmentType.OPEN
    )
    enrollment_key = models.CharField(max_length=100, blank=True)
    max_students = models.PositiveIntegerField(null=True, blank=True)
    format = models.CharField(max_length=10, choices=Format.choices, default=Format.TOPICS)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        TEACHER = "teacher", "Teacher"
        ASSISTANT = "assistant", "Assistant"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["user", "course"]
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.user} - {self.course}"


class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"
