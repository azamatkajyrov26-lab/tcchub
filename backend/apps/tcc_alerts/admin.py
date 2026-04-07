from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Alert, AlertSubscription


@admin.register(Alert)
class AlertAdmin(ModelAdmin):
    list_display = [
        "title",
        "alert_type",
        "severity",
        "corridor",
        "is_resolved",
        "created_at",
    ]
    list_filter = ["alert_type", "severity", "is_resolved", "created_at"]
    search_fields = ["title", "description"]
    readonly_fields = ["created_at"]


@admin.register(AlertSubscription)
class AlertSubscriptionAdmin(ModelAdmin):
    list_display = [
        "user",
        "corridor",
        "email_enabled",
        "web_enabled",
        "created_at",
    ]
    list_filter = ["email_enabled", "web_enabled"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["created_at"]
