from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Answer, Question, Quiz, QuizAttempt, QuizResponse


class AnswerInline(TabularInline):
    model = Answer
    extra = 3
    tab = True


class QuestionInline(TabularInline):
    model = Question
    extra = 1
    show_change_link = True
    tab = True


@admin.register(Quiz)
class QuizAdmin(ModelAdmin):
    list_display = ["activity", "time_limit", "max_attempts", "passing_grade", "shuffle_questions"]
    list_display_links = ["activity"]
    inlines = [QuestionInline]
    fieldsets = (
        (None, {"fields": ("activity",)}),
        ("Настройки", {"fields": ("time_limit", "max_attempts", "passing_grade", "shuffle_questions", "show_results")}),
    )


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    list_display = ["short_text", "quiz", "question_type", "points", "order"]
    list_display_links = ["short_text"]
    list_filter = ["question_type", "quiz"]
    list_filter_submit = True
    search_fields = ["text"]
    inlines = [AnswerInline]

    @admin.display(description="Вопрос")
    def short_text(self, obj):
        return obj.text[:80] + "..." if len(obj.text) > 80 else obj.text


@admin.register(QuizAttempt)
class QuizAttemptAdmin(ModelAdmin):
    list_display = ["user", "quiz", "attempt_number", "score", "state", "started_at", "finished_at"]
    list_filter = ["state"]
    list_filter_submit = True
    search_fields = ["user__email"]
    readonly_fields = ["started_at", "finished_at"]


@admin.register(QuizResponse)
class QuizResponseAdmin(ModelAdmin):
    list_display = ["attempt", "question", "is_correct", "score"]
    list_filter = ["is_correct"]
