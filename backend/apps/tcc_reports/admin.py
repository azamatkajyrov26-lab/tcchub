from django.contrib import admin

from apps.tcc_reports.models import Report, ReportSection, ReportTemplate


class ReportSectionInline(admin.TabularInline):
    model = ReportSection
    extra = 1
    fields = ["order", "section_type", "title", "content"]
    ordering = ["order"]


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "code"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "template",
        "status",
        "created_by",
        "price_usd",
        "views_count",
        "created_at",
    ]
    list_filter = ["status", "template", "is_free_preview"]
    search_fields = ["title", "subtitle", "executive_summary"]
    readonly_fields = ["created_at", "updated_at", "views_count", "downloads_count"]
    inlines = [ReportSectionInline]
    filter_horizontal = ["corridors", "countries"]


@admin.register(ReportSection)
class ReportSectionAdmin(admin.ModelAdmin):
    list_display = ["report", "order", "section_type", "title"]
    list_filter = ["section_type"]
    search_fields = ["title", "content"]
