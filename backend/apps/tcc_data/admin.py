from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import DataSource, NewsItem, SanctionEntry, SyncLog, TradeFlow


@admin.register(DataSource)
class DataSourceAdmin(ModelAdmin):
    list_display = [
        "name",
        "code",
        "source_type",
        "access_status",
        "is_active",
        "last_sync",
        "last_sync_status",
        "records_count",
    ]
    list_filter = ["source_type", "access_status", "is_active"]
    search_fields = ["name", "code"]
    readonly_fields = ["last_sync", "last_sync_status", "records_count", "created_at"]


@admin.register(SyncLog)
class SyncLogAdmin(ModelAdmin):
    list_display = [
        "source",
        "started_at",
        "finished_at",
        "status",
        "records_fetched",
        "records_new",
        "records_updated",
    ]
    list_filter = ["status", "source"]
    readonly_fields = [
        "source",
        "started_at",
        "finished_at",
        "status",
        "records_fetched",
        "records_new",
        "records_updated",
        "error_message",
        "celery_task_id",
    ]
    ordering = ["-started_at"]

    def has_add_permission(self, request):
        return False


@admin.register(SanctionEntry)
class SanctionEntryAdmin(ModelAdmin):
    list_display = [
        "name_primary",
        "entity_type",
        "source",
        "program",
        "listing_date",
        "is_active",
    ]
    list_filter = ["entity_type", "source", "is_active"]
    search_fields = ["name_primary", "name_aliases", "program"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(TradeFlow)
class TradeFlowAdmin(ModelAdmin):
    list_display = [
        "reporter_country",
        "partner_country",
        "year",
        "hs_code",
        "flow_type",
        "value_usd",
    ]
    list_filter = ["year", "flow_type"]
    search_fields = ["hs_code"]
    readonly_fields = ["created_at"]


@admin.register(NewsItem)
class NewsItemAdmin(ModelAdmin):
    list_display = [
        "title_short",
        "source",
        "published_at",
        "ai_processed",
        "ai_severity",
        "ai_is_relevant",
    ]
    list_filter = ["ai_processed", "ai_is_relevant", "source", "language"]
    search_fields = ["title", "content"]
    readonly_fields = ["created_at"]

    def title_short(self, obj):
        return obj.title[:60] + "..." if len(obj.title) > 60 else obj.title
    title_short.short_description = "Заголовок"
