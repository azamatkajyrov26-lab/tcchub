from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Assignment, Submission, SubmissionFile


class SubmissionFileInline(TabularInline):
    model = SubmissionFile
    extra = 0
    tab = True


@admin.register(Assignment)
class AssignmentAdmin(ModelAdmin):
    list_display = ["activity", "max_score", "allow_late", "max_files"]
    list_display_links = ["activity"]
    fieldsets = (
        (None, {"fields": ("activity", "max_score")}),
        ("Настройки сдачи", {"fields": ("allow_late", "late_penalty", "submission_types", "max_file_size", "max_files")}),
    )


@admin.register(Submission)
class SubmissionAdmin(ModelAdmin):
    list_display = ["user", "assignment", "status", "grade", "submitted_at", "graded_by", "graded_at"]
    list_display_links = ["user"]
    list_filter = ["status"]
    list_filter_submit = True
    search_fields = ["user__email", "assignment__activity__title"]
    readonly_fields = ["submitted_at", "updated_at", "graded_at"]
    inlines = [SubmissionFileInline]
