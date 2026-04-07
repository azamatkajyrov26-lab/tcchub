from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ContactRequest, Conversation, Message
from .serializers import ContactRequestSerializer, ConversationSerializer, MessageSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related("participants", "messages").distinct()

    def perform_create(self, serializer):
        conversation = serializer.save()
        conversation.participants.add(self.request.user)

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        messages = conversation.messages.select_related("sender").all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        conversation = self.get_object()
        count = conversation.messages.filter(is_read=False).exclude(
            sender=request.user
        ).update(is_read=True)
        return Response({"marked_read": count})


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["conversation", "is_read"]

    def get_queryset(self):
        return Message.objects.filter(
            conversation__participants=self.request.user
        ).select_related("sender")

    def perform_create(self, serializer):
        message = serializer.save(sender=self.request.user)
        message.conversation.save()  # Updates updated_at


class ContactRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ContactRequestSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status"]

    def get_queryset(self):
        user = self.request.user
        return ContactRequest.objects.select_related(
            "from_user", "to_user"
        ).filter(from_user=user) | ContactRequest.objects.select_related(
            "from_user", "to_user"
        ).filter(to_user=user)

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        contact_request = self.get_object()
        if contact_request.to_user != request.user:
            return Response({"detail": "Not your request."}, status=status.HTTP_403_FORBIDDEN)
        contact_request.status = ContactRequest.Status.ACCEPTED
        contact_request.save()
        return Response(ContactRequestSerializer(contact_request).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        contact_request = self.get_object()
        if contact_request.to_user != request.user:
            return Response({"detail": "Not your request."}, status=status.HTTP_403_FORBIDDEN)
        contact_request.status = ContactRequest.Status.REJECTED
        contact_request.save()
        return Response(ContactRequestSerializer(contact_request).data)
