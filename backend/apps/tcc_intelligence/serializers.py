from rest_framework import serializers

from apps.tcc_intelligence.models import RiskFactor, RouteScore, Scenario


class RiskFactorSerializer(serializers.ModelSerializer):
    corridor_code = serializers.CharField(source="corridor.code", read_only=True, default="")
    country_name = serializers.CharField(source="country.name_ru", read_only=True, default="")

    class Meta:
        model = RiskFactor
        fields = [
            "id",
            "corridor",
            "corridor_code",
            "country",
            "country_name",
            "node",
            "risk_category",
            "severity",
            "probability",
            "impact_score",
            "title",
            "description",
            "evidence",
            "mitigation",
            "source_type",
            "valid_from",
            "valid_until",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["impact_score", "created_at"]


class RouteScoreSerializer(serializers.ModelSerializer):
    corridor_code = serializers.CharField(source="corridor.code", read_only=True)
    corridor_name = serializers.CharField(source="corridor.name", read_only=True)

    class Meta:
        model = RouteScore
        fields = [
            "id",
            "corridor",
            "corridor_code",
            "corridor_name",
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


class ScenarioSerializer(serializers.ModelSerializer):
    corridor_code = serializers.CharField(source="corridor.code", read_only=True)

    class Meta:
        model = Scenario
        fields = [
            "id",
            "corridor",
            "corridor_code",
            "label",
            "plan_code",
            "description",
            "cost_index",
            "transit_days_min",
            "transit_days_max",
            "reliability_score",
            "risk_score",
            "is_recommended",
            "notes",
            "created_at",
            "updated_at",
        ]
