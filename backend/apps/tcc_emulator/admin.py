from django.contrib import admin

from apps.tcc_emulator.models import EmulatedDataSource, EmulatedNodeStatus


@admin.register(EmulatedDataSource)
class EmulatedDataSourceAdmin(admin.ModelAdmin):
    list_display = [
        "data_source",
        "emulation_strategy",
        "confidence_level",
        "data_age_days",
        "last_reviewed",
    ]
    list_filter = ["emulation_strategy"]


@admin.register(EmulatedNodeStatus)
class EmulatedNodeStatusAdmin(admin.ModelAdmin):
    list_display = [
        "node",
        "date",
        "throughput_percent",
        "avg_wait_hours",
        "incidents_count",
        "is_emulated",
    ]
    list_filter = ["date", "is_emulated"]
    search_fields = ["node__name_en", "node__name"]
