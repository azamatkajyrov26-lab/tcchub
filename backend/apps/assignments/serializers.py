from rest_framework import serializers

from .models import Assignment, Submission, SubmissionFile


class SubmissionFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionFile
        fields = ["id", "submission", "file", "original_name", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]


class SubmissionSerializer(serializers.ModelSerializer):
    files = SubmissionFileSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    graded_by_name = serializers.CharField(source="graded_by.get_full_name", read_only=True, default="")

    class Meta:
        model = Submission
        fields = [
            "id", "assignment", "user", "user_name", "submitted_at",
            "updated_at", "status", "grade", "feedback",
            "graded_by", "graded_by_name", "graded_at", "files",
        ]
        read_only_fields = ["id", "user", "submitted_at", "updated_at", "graded_by", "graded_at"]


class AssignmentSerializer(serializers.ModelSerializer):
    submission_count = serializers.IntegerField(source="submissions.count", read_only=True)

    class Meta:
        model = Assignment
        fields = [
            "id", "activity", "max_score", "allow_late", "late_penalty",
            "submission_types", "max_file_size", "max_files", "submission_count",
        ]
        read_only_fields = ["id"]
