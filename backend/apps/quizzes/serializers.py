from rest_framework import serializers

from .models import Answer, Question, Quiz, QuizAttempt, QuizResponse


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["id", "question", "text", "is_correct", "order"]
        read_only_fields = ["id"]


class AnswerStudentSerializer(serializers.ModelSerializer):
    """Hides is_correct from students during quiz."""

    class Meta:
        model = Answer
        fields = ["id", "text", "order"]


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "quiz", "text", "question_type", "points", "order", "explanation", "answers"]
        read_only_fields = ["id"]


class QuestionStudentSerializer(serializers.ModelSerializer):
    answers = AnswerStudentSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "question_type", "points", "order", "answers"]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    question_count = serializers.IntegerField(source="questions.count", read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id", "activity", "time_limit", "max_attempts", "passing_grade",
            "shuffle_questions", "show_results", "questions", "question_count",
        ]
        read_only_fields = ["id"]


class QuizResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizResponse
        fields = ["id", "attempt", "question", "answer", "text_response", "score", "is_correct"]
        read_only_fields = ["id", "score", "is_correct"]


class QuizAttemptSerializer(serializers.ModelSerializer):
    responses = QuizResponseSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "id", "quiz", "user", "started_at", "finished_at",
            "score", "attempt_number", "state", "responses",
        ]
        read_only_fields = ["id", "user", "started_at", "attempt_number", "score"]


class QuizAttemptListSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = [
            "id", "quiz", "user", "started_at", "finished_at",
            "score", "attempt_number", "state",
        ]
