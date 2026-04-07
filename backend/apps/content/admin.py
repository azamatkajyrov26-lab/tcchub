from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from .models import Activity, ActivityCompletion, Folder, FolderFile, Resource, VideoProgress, VideoTimestamp


class ResourceInline(StackedInline):
    model = Resource
    extra = 0
    tab = True


class FolderInline(StackedInline):
    model = Folder
    extra = 0
    tab = True


class VideoTimestampInline(TabularInline):
    model = VideoTimestamp
    extra = 1
    tab = True


@admin.register(Activity)
class ActivityAdmin(ModelAdmin):
    list_display = ["title", "section", "activity_type", "order", "is_visible", "due_date"]
    list_display_links = ["title"]
    list_filter = ["activity_type", "is_visible", "completion_type", "section__course"]
    list_filter_submit = True
    search_fields = ["title", "section__course__title"]
    inlines = [ResourceInline, FolderInline, VideoTimestampInline]
    fieldsets = (
        (None, {"fields": ("section", "title", "description", "activity_type")}),
        ("Настройки", {"fields": ("order", "is_visible", "completion_type", "due_date"), "classes": ["tab"]}),
    )


@admin.register(Resource)
class ResourceAdmin(ModelAdmin):
    list_display = ["activity", "file_type", "file_size", "external_url"]
    search_fields = ["activity__title"]


@admin.register(Folder)
class FolderAdmin(ModelAdmin):
    list_display = ["name", "activity"]
    search_fields = ["name"]


class FolderFileInline(TabularInline):
    model = FolderFile
    extra = 1


@admin.register(FolderFile)
class FolderFileAdmin(ModelAdmin):
    list_display = ["original_name", "folder"]


@admin.register(ActivityCompletion)
class ActivityCompletionAdmin(ModelAdmin):
    list_display = ["user", "activity", "completed", "completed_at"]
    list_filter = ["completed"]
    list_filter_submit = True
    search_fields = ["user__email", "activity__title"]


@admin.register(VideoTimestamp)
class VideoTimestampAdmin(ModelAdmin):
    list_display = ["title", "activity", "time_seconds", "order"]
    list_filter = ["activity"]
    list_filter_submit = True
    search_fields = ["title", "activity__title"]


@admin.register(VideoProgress)
class VideoProgressAdmin(ModelAdmin):
    list_display = ["user", "activity", "current_time", "duration", "updated_at"]
    list_filter = ["activity"]
    list_filter_submit = True
    search_fields = ["user__email", "activity__title"]
