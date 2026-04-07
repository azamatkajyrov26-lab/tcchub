from rest_framework import serializers

from .models import Notification, NotificationPreference, NotificationType


class NotificationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationType
        fields = ["id", "code", "name", "description", "category"]
        read_only_fields = ["id"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    type_name = serializers.CharField(source="notification_type.name", read_only=True)

    class Meta:
        model = NotificationPreference
        fields = [
            "id", "user", "notification_type", "type_name",
            "email_enabled", "web_enabled", "push_enabled",
        ]
        read_only_fields = ["id", "user"]


class NotificationSerializer(serializers.ModelSerializer):
    type_name = serializers.CharField(source="notification_type.name", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id", "user", "notification_type", "type_name",
            "title", "message", "is_read", "created_at", "link",
        ]
        read_only_fields = ["id", "user", "created_at"]
