from django.contrib import admin

from apps.tcc_intelligence.models import RiskFactor, RouteScore, Scenario


@admin.register(RiskFactor)
class RiskFactorAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "risk_category",
        "severity",
        "probability",
        "impact_score",
        "corridor",
        "country",
        "is_active",
    ]
    list_filter = ["risk_category", "source_type", "is_active"]
    search_fields = ["title", "description"]
    readonly_fields = ["impact_score", "created_at", "updated_at"]


@admin.register(RouteScore)
class RouteScoreAdmin(admin.ModelAdmin):
    list_display = [
        "corridor",
        "score_total",
        "risk_level",
        "score_sanctions",
        "score_geopolitical",
        "score_infrastructure",
        "calculated_at",
    ]
    list_filter = ["risk_level", "corridor"]
    readonly_fields = [
        "corridor",
        "calculated_at",
        "score_sanctions",
        "score_geopolitical",
        "score_infrastructure",
        "score_regulatory",
        "score_financial",
        "score_total",
        "risk_level",
        "weights",
        "factors_snapshot",
    ]

    def has_add_permission(self, request):
        return False


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = [
        "corridor",
        "plan_code",
        "label",
        "cost_index",
        "transit_days_min",
        "transit_days_max",
        "reliability_score",
        "risk_score",
        "is_recommended",
    ]
    list_filter = ["corridor", "is_recommended"]
    search_fields = ["label", "description"]
