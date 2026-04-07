from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ContactRequest, Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(ModelAdmin):
    list_display = ["pk", "created_at", "updated_at"]
    filter_horizontal = ["participants"]


@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = ["conversation", "sender", "is_read", "created_at"]
    list_filter = ["is_read"]
    search_fields = ["content"]


@admin.register(ContactRequest)
class ContactRequestAdmin(ModelAdmin):
    list_display = ["from_user", "to_user", "status", "created_at"]
    list_filter = ["status"]
