from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AnswerViewSet, QuestionViewSet, QuizAttemptViewSet, QuizResponseViewSet, QuizViewSet

router = DefaultRouter()
router.register("quizzes", QuizViewSet, basename="quiz")
router.register("questions", QuestionViewSet, basename="question")
router.register("answers", AnswerViewSet, basename="answer")
router.register("attempts", QuizAttemptViewSet, basename="quiz-attempt")
router.register("responses", QuizResponseViewSet, basename="quiz-response")

urlpatterns = [
    path("", include(router.urls)),
]
