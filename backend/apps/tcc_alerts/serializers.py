from rest_framework import serializers

from .models import Alert, AlertSubscription


class AlertSerializer(serializers.ModelSerializer):
    corridor_name = serializers.CharField(
        source="corridor.name", read_only=True, default=None
    )
    country_name = serializers.CharField(
        source="country.name", read_only=True, default=None
    )
    node_name = serializers.CharField(
        source="node.name", read_only=True, default=None
    )

    class Meta:
        model = Alert
        fields = [
            "id",
            "alert_type",
            "severity",
            "title",
            "description",
            "corridor",
            "corridor_name",
            "country",
            "country_name",
            "node",
            "node_name",
            "related_score",
            "is_resolved",
            "resolved_at",
            "created_at",
            "data",
        ]
        read_only_fields = fields


class AlertSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertSubscription
        fields = [
            "id",
            "user",
            "corridor",
            "alert_types",
            "email_enabled",
            "web_enabled",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
