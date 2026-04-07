from rest_framework import serializers

from .models import CorridorNode, Country, Region, RouteNode, TradeCorridor


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["id", "name", "name_en", "region_type", "iso_code", "parent", "coordinates"]


class CountrySerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source="region.name", read_only=True, default="")

    class Meta:
        model = Country
        fields = [
            "id", "iso2", "iso3", "name_ru", "name_en", "region", "region_name",
            "sanction_risk_level", "wb_stability_index", "ti_cpi_score",
            "imf_gdp_growth", "last_updated",
        ]


class RouteNodeSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name_ru", read_only=True)
    country_iso2 = serializers.CharField(source="country.iso2", read_only=True)

    class Meta:
        model = RouteNode
        fields = [
            "id", "name", "name_en", "country", "country_name", "country_iso2",
            "node_type", "lat", "lng", "capacity_teu_year", "operator",
            "status", "status_note", "description", "is_emulated",
        ]


class CorridorNodeSerializer(serializers.ModelSerializer):
    node = RouteNodeSerializer(read_only=True)

    class Meta:
        model = CorridorNode
        fields = ["id", "order", "segment_distance_km", "segment_mode", "node"]


class TradeCorridorListSerializer(serializers.ModelSerializer):
    node_count = serializers.IntegerField(source="corridor_nodes.count", read_only=True)

    class Meta:
        model = TradeCorridor
        fields = ["id", "name", "code", "description", "color", "is_active", "node_count"]


class TradeCorridorDetailSerializer(serializers.ModelSerializer):
    corridor_nodes = CorridorNodeSerializer(many=True, read_only=True)
    total_distance_km = serializers.SerializerMethodField()

    class Meta:
        model = TradeCorridor
        fields = [
            "id", "name", "code", "description", "color", "is_active",
            "corridor_nodes", "total_distance_km", "created_at", "updated_at",
        ]

    def get_total_distance_km(self, obj):
        return sum(
            cn.segment_distance_km or 0
            for cn in obj.corridor_nodes.all()
        )
