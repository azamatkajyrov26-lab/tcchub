from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Badge, BadgeIssuance


@admin.register(Badge)
class BadgeAdmin(ModelAdmin):
    list_display = ["name", "course", "is_active", "created_by"]
    list_filter = ["is_active"]
    search_fields = ["name"]


@admin.register(BadgeIssuance)
class BadgeIssuanceAdmin(ModelAdmin):
    list_display = ["badge", "user", "issued_at", "issued_by"]
    search_fields = ["user__email", "badge__name"]
