from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ContactRequest, Conversation, Message

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.get_full_name", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "conversation", "sender", "sender_name", "content", "created_at", "is_read"]
        read_only_fields = ["id", "sender", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all()
    )
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "participants", "created_at", "updated_at", "last_message", "unread_count"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_last_message(self, obj):
        msg = obj.messages.order_by("-created_at").first()
        if msg:
            return MessageSerializer(msg).data
        return None

    def get_unread_count(self, obj):
        user = self.context.get("request")
        if user:
            return obj.messages.filter(is_read=False).exclude(sender=user.user).count()
        return 0


class ContactRequestSerializer(serializers.ModelSerializer):
    from_user_name = serializers.CharField(source="from_user.get_full_name", read_only=True)
    to_user_name = serializers.CharField(source="to_user.get_full_name", read_only=True)

    class Meta:
        model = ContactRequest
        fields = [
            "id", "from_user", "from_user_name", "to_user", "to_user_name",
            "status", "created_at",
        ]
        read_only_fields = ["id", "from_user", "created_at"]
