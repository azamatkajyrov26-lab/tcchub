from django.conf import settings
from django.db import models


class GradeCategory(models.Model):
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="grade_categories"
    )
    name = models.CharField(max_length=255)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )

    class Meta:
        verbose_name_plural = "Grade categories"

    def __str__(self):
        return f"{self.name} ({self.course.title})"


class GradeItem(models.Model):
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="grade_items"
    )
    category = models.ForeignKey(
        GradeCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="items"
    )
    activity = models.ForeignKey(
        "content.Activity", on_delete=models.SET_NULL, null=True, blank=True, related_name="grade_items"
    )
    name = models.CharField(max_length=255)
    max_grade = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1)

    def __str__(self):
        return f"{self.name} (max: {self.max_grade})"


class Grade(models.Model):
    grade_item = models.ForeignKey(GradeItem, on_delete=models.CASCADE, related_name="grades")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="grades"
    )
    grade = models.DecimalField(max_digits=5, decimal_places=2)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="given_grades",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["grade_item", "user"]

    def __str__(self):
        return f"{self.user} - {self.grade_item}: {self.grade}"
