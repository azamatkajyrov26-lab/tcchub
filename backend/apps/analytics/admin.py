from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import CourseReport, LoginLog, UserActivity


@admin.register(UserActivity)
class UserActivityAdmin(ModelAdmin):
    list_display = ["user", "action", "object_type", "object_id", "created_at"]
    list_filter = ["action", "object_type"]
    list_filter_submit = True
    search_fields = ["user__email"]


@admin.register(CourseReport)
class CourseReportAdmin(ModelAdmin):
    list_display = ["user", "course", "total_time", "completion_percentage", "last_access"]
    list_filter = ["course"]
    search_fields = ["user__email"]


@admin.register(LoginLog)
class LoginLogAdmin(ModelAdmin):
    list_display = ["user", "ip_address", "logged_in_at", "logged_out_at"]
    search_fields = ["user__email", "ip_address"]
