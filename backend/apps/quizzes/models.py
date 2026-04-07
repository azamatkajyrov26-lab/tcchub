from django.conf import settings
from django.db import models


class Quiz(models.Model):
    activity = models.OneToOneField(
        "content.Activity", on_delete=models.CASCADE, related_name="quiz"
    )
    time_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Time limit in minutes")
    max_attempts = models.PositiveIntegerField(default=1)
    passing_grade = models.DecimalField(max_digits=5, decimal_places=2, default=60)
    shuffle_questions = models.BooleanField(default=False)
    show_results = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return f"Quiz: {self.activity.title}"


class Question(models.Model):
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Multiple Choice"
        TRUE_FALSE = "true_false", "True/False"
        SHORT_ANSWER = "short_answer", "Short Answer"
        ESSAY = "essay", "Essay"
        MATCHING = "matching", "Matching"

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    points = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    order = models.PositiveIntegerField(default=0)
    explanation = models.TextField(blank=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.text[:50]} ({'correct' if self.is_correct else 'wrong'})"


class QuizAttempt(models.Model):
    class State(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        FINISHED = "finished", "Finished"
        ABANDONED = "abandoned", "Abandoned"

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    attempt_number = models.PositiveIntegerField(default=1)
    state = models.CharField(max_length=20, choices=State.choices, default=State.IN_PROGRESS)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user} - {self.quiz} (attempt {self.attempt_number})"


class QuizResponse(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="responses")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="responses")
    answer = models.ForeignKey(
        Answer, on_delete=models.SET_NULL, null=True, blank=True, related_name="responses"
    )
    text_response = models.TextField(blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)

    class Meta:
        unique_together = ["attempt", "question"]

    def __str__(self):
        return f"Response: {self.attempt} - Q{self.question.order}"
