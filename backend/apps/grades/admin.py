from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Grade, GradeCategory, GradeItem


@admin.register(GradeCategory)
class GradeCategoryAdmin(ModelAdmin):
    list_display = ["name", "course", "weight", "parent"]
    list_filter = ["course"]
    search_fields = ["name"]


@admin.register(GradeItem)
class GradeItemAdmin(ModelAdmin):
    list_display = ["name", "course", "category", "max_grade", "weight"]
    list_filter = ["course"]
    search_fields = ["name"]


@admin.register(Grade)
class GradeAdmin(ModelAdmin):
    list_display = ["user", "grade_item", "grade", "graded_by", "updated_at"]
    list_filter = ["grade_item__course"]
    list_filter_submit = True
    search_fields = ["user__email"]
    readonly_fields = ["created_at", "updated_at"]
