from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Discussion, Forum, Post


@admin.register(Forum)
class ForumAdmin(ModelAdmin):
    list_display = ["activity", "forum_type", "is_anonymous"]
    list_filter = ["forum_type"]


@admin.register(Discussion)
class DiscussionAdmin(ModelAdmin):
    list_display = ["title", "forum", "user", "pinned", "locked", "created_at"]
    list_filter = ["pinned", "locked"]
    search_fields = ["title"]


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = ["discussion", "user", "parent", "created_at"]
    search_fields = ["content"]
