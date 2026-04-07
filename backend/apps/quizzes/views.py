from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.courses.permissions import IsCourseCreatorOrReadOnly

from .models import Answer, Question, Quiz, QuizAttempt, QuizResponse
from .serializers import (
    AnswerSerializer,
    QuestionSerializer,
    QuestionStudentSerializer,
    QuizAttemptListSerializer,
    QuizAttemptSerializer,
    QuizResponseSerializer,
    QuizSerializer,
)


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.select_related("activity").prefetch_related("questions__answers").all()
    serializer_class = QuizSerializer
    permission_classes = [IsCourseCreatorOrReadOnly]
    filterset_fields = ["activity"]

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def start_attempt(self, request, pk=None):
        quiz = self.get_object()
        existing = QuizAttempt.objects.filter(
            quiz=quiz, user=request.user, state=QuizAttempt.State.IN_PROGRESS
        ).first()
        if existing:
            return Response(QuizAttemptSerializer(existing).data)

        attempt_count = QuizAttempt.objects.filter(quiz=quiz, user=request.user).count()
        if quiz.max_attempts and attempt_count >= quiz.max_attempts:
            return Response(
                {"detail": "Max attempts reached."}, status=status.HTTP_400_BAD_REQUEST
            )
        attempt = QuizAttempt.objects.create(
            quiz=quiz, user=request.user, attempt_number=attempt_count + 1
        )
        return Response(QuizAttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def questions_for_student(self, request, pk=None):
        quiz = self.get_object()
        questions = quiz.questions.prefetch_related("answers").all()
        if quiz.shuffle_questions:
            questions = questions.order_by("?")
        serializer = QuestionStudentSerializer(questions, many=True)
        return Response(serializer.data)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.prefetch_related("answers").all()
    serializer_class = QuestionSerializer
    permission_classes = [IsCourseCreatorOrReadOnly]
    filterset_fields = ["quiz", "question_type"]


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.select_related("question").all()
    serializer_class = AnswerSerializer
    permission_classes = [IsCourseCreatorOrReadOnly]
    filterset_fields = ["question"]


class QuizAttemptViewSet(viewsets.ModelViewSet):
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["quiz", "state"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if user.role in ("admin", "manager", "teacher"):
            return QuizAttempt.objects.select_related("quiz", "user").all()
        return QuizAttempt.objects.select_related("quiz").filter(user=user)

    def get_serializer_class(self):
        if self.action == "list":
            return QuizAttemptListSerializer
        return QuizAttemptSerializer

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """
        Accept answers, create QuizResponse records, auto-grade,
        mark attempt as finished, and return results.

        Expects: {"answers": [{"question_id": 1, "answer_id": 2}, ...]}
        """
        attempt = self.get_object()
        if attempt.user != request.user:
            return Response({"detail": "Not your attempt."}, status=status.HTTP_403_FORBIDDEN)
        if attempt.state != QuizAttempt.State.IN_PROGRESS:
            return Response({"detail": "Attempt already finished."}, status=status.HTTP_400_BAD_REQUEST)

        answers_data = request.data.get("answers", [])
        if not answers_data:
            return Response(
                {"detail": "No answers provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        quiz = attempt.quiz
        questions = {q.id: q for q in quiz.questions.prefetch_related("answers").all()}

        # Create QuizResponse records
        for item in answers_data:
            question_id = item.get("question_id")
            answer_id = item.get("answer_id")
            text_response = item.get("text_response", "")

            question = questions.get(question_id)
            if not question:
                continue

            answer_obj = None
            if answer_id:
                answer_obj = question.answers.filter(id=answer_id).first()

            QuizResponse.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    "answer": answer_obj,
                    "text_response": text_response,
                },
            )

        # Auto-grade objective questions
        total_score = 0
        total_points = 0
        for resp in attempt.responses.select_related("question", "answer").all():
            q = resp.question
            total_points += q.points
            if q.question_type in ("multiple_choice", "true_false"):
                if resp.answer and resp.answer.is_correct:
                    resp.is_correct = True
                    resp.score = q.points
                else:
                    resp.is_correct = False
                    resp.score = 0
                resp.save()
            if resp.score:
                total_score += resp.score

        attempt.state = QuizAttempt.State.FINISHED
        attempt.finished_at = timezone.now()
        attempt.score = (total_score / total_points * 100) if total_points else 0
        attempt.save()

        passing = attempt.score >= quiz.passing_grade

        # Send notification asynchronously
        from apps.notifications.tasks import send_quiz_graded_notification

        send_quiz_graded_notification.delay(attempt.id)

        data = QuizAttemptSerializer(attempt).data
        data["passed"] = passing
        return Response(data)

    @action(detail=True, methods=["post"])
    def finish(self, request, pk=None):
        attempt = self.get_object()
        if attempt.user != request.user:
            return Response({"detail": "Not your attempt."}, status=status.HTTP_403_FORBIDDEN)
        if attempt.state != QuizAttempt.State.IN_PROGRESS:
            return Response({"detail": "Attempt already finished."}, status=status.HTTP_400_BAD_REQUEST)

        # Auto-grade objective questions
        total_score = 0
        total_points = 0
        for response in attempt.responses.select_related("question", "answer").all():
            q = response.question
            total_points += q.points
            if q.question_type in ("multiple_choice", "true_false"):
                if response.answer and response.answer.is_correct:
                    response.is_correct = True
                    response.score = q.points
                else:
                    response.is_correct = False
                    response.score = 0
                response.save()
            if response.score:
                total_score += response.score

        attempt.state = QuizAttempt.State.FINISHED
        attempt.finished_at = timezone.now()
        attempt.score = (total_score / total_points * 100) if total_points else 0
        attempt.save()
        return Response(QuizAttemptSerializer(attempt).data)


class QuizResponseViewSet(viewsets.ModelViewSet):
    serializer_class = QuizResponseSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["attempt", "question"]

    def get_queryset(self):
        user = self.request.user
        if user.role in ("admin", "manager", "teacher"):
            return QuizResponse.objects.all()
        return QuizResponse.objects.filter(attempt__user=user)

    def perform_create(self, serializer):
        serializer.save()
