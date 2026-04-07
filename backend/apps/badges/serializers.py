from rest_framework import serializers

from .models import Badge, BadgeIssuance


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ["id", "name", "description", "image", "criteria", "course", "is_active", "created_by"]
        read_only_fields = ["id", "created_by"]


class BadgeIssuanceSerializer(serializers.ModelSerializer):
    badge_name = serializers.CharField(source="badge.name", read_only=True)
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = BadgeIssuance
        fields = ["id", "badge", "badge_name", "user", "user_name", "issued_at", "issued_by"]
        read_only_fields = ["id", "issued_at"]
