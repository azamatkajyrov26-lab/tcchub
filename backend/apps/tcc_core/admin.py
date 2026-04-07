from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import CorridorNode, Country, Region, RouteNode, TradeCorridor


@admin.register(Region)
class RegionAdmin(ModelAdmin):
    list_display = ["name", "region_type", "iso_code", "parent", "order"]
    list_filter = ["region_type"]
    search_fields = ["name", "name_en", "iso_code"]
    list_editable = ["order"]


@admin.register(Country)
class CountryAdmin(ModelAdmin):
    list_display = [
        "name_ru",
        "iso2",
        "iso3",
        "sanction_risk_level",
        "wb_stability_index",
        "last_updated",
    ]
    list_filter = ["sanction_risk_level", "region"]
    search_fields = ["name_ru", "name_en", "iso2", "iso3"]
    readonly_fields = ["last_updated"]


@admin.register(RouteNode)
class RouteNodeAdmin(ModelAdmin):
    list_display = [
        "name",
        "country",
        "node_type",
        "status",
        "capacity_teu_year",
        "is_emulated",
    ]
    list_filter = ["node_type", "status", "is_emulated", "country"]
    search_fields = ["name", "name_en", "operator"]


class CorridorNodeInline(TabularInline):
    model = CorridorNode
    extra = 1
    ordering = ["order"]
    autocomplete_fields = ["node"]


@admin.register(TradeCorridor)
class TradeCorridorAdmin(ModelAdmin):
    list_display = ["name", "code", "is_active", "node_count", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "code"]
    inlines = [CorridorNodeInline]

    @admin.display(description="Узлов")
    def node_count(self, obj):
        return obj.corridor_nodes.count()


@admin.register(CorridorNode)
class CorridorNodeAdmin(ModelAdmin):
    list_display = ["corridor", "node", "order", "segment_mode", "segment_distance_km"]
    list_filter = ["corridor", "segment_mode"]
    ordering = ["corridor", "order"]
