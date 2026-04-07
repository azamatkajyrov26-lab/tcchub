from rest_framework import serializers

from apps.tcc_emulator.models import EmulatedDataSource, EmulatedNodeStatus


class EmulatedDataSourceSerializer(serializers.ModelSerializer):
    data_source_name = serializers.CharField(source="data_source.name", read_only=True)

    class Meta:
        model = EmulatedDataSource
        fields = [
            "id",
            "data_source",
            "data_source_name",
            "emulation_strategy",
            "confidence_level",
            "data_age_days",
            "source_references",
            "disclaimer_ru",
            "last_reviewed",
        ]


class EmulatedNodeStatusSerializer(serializers.ModelSerializer):
    node_name = serializers.CharField(source="node.name_en", read_only=True)

    class Meta:
        model = EmulatedNodeStatus
        fields = [
            "id",
            "node",
            "node_name",
            "date",
            "throughput_percent",
            "avg_wait_hours",
            "incidents_count",
            "note",
            "is_emulated",
        ]
