from rest_framework import serializers

from .models import DataSource, NewsItem, SanctionEntry, SyncLog, TradeFlow


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = [
            "id", "name", "code", "source_type", "base_url",
            "fetch_interval_hours", "is_active", "access_status",
            "last_sync", "last_sync_status", "records_count",
        ]


class SyncLogSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = SyncLog
        fields = [
            "id", "source", "source_name", "started_at", "finished_at",
            "status", "records_fetched", "records_new", "records_updated",
            "error_message",
        ]


class SanctionEntrySerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = SanctionEntry
        fields = [
            "id", "source", "source_name", "external_id", "entity_type",
            "name_primary", "name_aliases", "countries", "program",
            "listing_date", "is_active",
        ]


class SanctionSearchSerializer(serializers.Serializer):
    q = serializers.CharField(help_text="Поисковый запрос по имени/псевдониму")
    entity_type = serializers.ChoiceField(
        choices=SanctionEntry.ENTITY_TYPES, required=False
    )
    source = serializers.CharField(required=False, help_text="Код источника (OFAC, EU, UN)")


class TradeFlowSerializer(serializers.ModelSerializer):
    reporter_iso2 = serializers.CharField(source="reporter_country.iso2", read_only=True)
    partner_iso2 = serializers.CharField(source="partner_country.iso2", read_only=True)
    reporter_name = serializers.CharField(source="reporter_country.name_ru", read_only=True)
    partner_name = serializers.CharField(source="partner_country.name_ru", read_only=True)

    class Meta:
        model = TradeFlow
        fields = [
            "id",
            "reporter_country",
            "reporter_iso2",
            "reporter_name",
            "partner_country",
            "partner_iso2",
            "partner_name",
            "year",
            "hs_code",
            "flow_type",
            "value_usd",
            "weight_kg",
        ]


class NewsItemSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = NewsItem
        fields = [
            "id",
            "source",
            "source_name",
            "title",
            "content",
            "url",
            "published_at",
            "language",
            "ai_processed",
            "ai_risk_type",
            "ai_severity",
            "ai_affected_countries",
            "ai_affected_corridors",
            "ai_summary_ru",
            "ai_is_relevant",
        ]
