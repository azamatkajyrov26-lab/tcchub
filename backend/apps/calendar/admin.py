from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Event


@admin.register(Event)
class EventAdmin(ModelAdmin):
    list_display = ["title", "event_type", "course", "user", "start_date", "end_date"]
    list_filter = ["event_type"]
    search_fields = ["title"]
