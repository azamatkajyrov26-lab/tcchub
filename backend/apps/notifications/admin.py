from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Notification, NotificationPreference, NotificationType


@admin.register(NotificationType)
class NotificationTypeAdmin(ModelAdmin):
    list_display = ["code", "name", "category"]
    list_filter = ["category"]
    search_fields = ["name", "code"]


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(ModelAdmin):
    list_display = ["user", "notification_type", "email_enabled", "web_enabled", "push_enabled"]


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ["title", "user", "notification_type", "is_read", "created_at"]
    list_filter = ["is_read", "notification_type"]
    list_filter_submit = True
    search_fields = ["title", "message"]
