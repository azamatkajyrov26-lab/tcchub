from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Category, Course, Enrollment, Section


class SectionInline(TabularInline):
    model = Section
    extra = 1
    tab = True


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ["name", "slug", "parent", "order"]
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ["parent"]
    search_fields = ["name"]


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    list_display = ["title", "category", "is_published", "enrollment_type", "duration_hours", "created_by", "created_at"]
    list_display_links = ["title"]
    list_filter = ["is_published", "enrollment_type", "format", "category"]
    list_filter_submit = True
    search_fields = ["title", "description"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [SectionInline]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (None, {"fields": ("title", "slug", "category", "created_by")}),
        ("Описание", {"fields": ("description", "short_description", "cover_image"), "classes": ["tab"]}),
        ("Настройки", {"fields": ("is_published", "format", "duration_hours", "max_students"), "classes": ["tab"]}),
        ("Запись", {"fields": ("enrollment_type", "enrollment_key"), "classes": ["tab"]}),
        ("Даты", {"fields": ("created_at", "updated_at"), "classes": ["tab"]}),
    )


@admin.register(Enrollment)
class EnrollmentAdmin(ModelAdmin):
    list_display = ["user", "course", "role", "progress", "is_active", "enrolled_at"]
    list_filter = ["role", "is_active", "course"]
    list_filter_submit = True
    search_fields = ["user__email", "user__first_name", "course__title"]
    autocomplete_fields = ["user", "course"]


@admin.register(Section)
class SectionAdmin(ModelAdmin):
    list_display = ["title", "course", "order", "is_visible"]
    list_filter = ["is_visible", "course"]
    list_filter_submit = True
    search_fields = ["title", "course__title"]
