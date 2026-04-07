from rest_framework import serializers

from .models import CourseReport, LoginLog, UserActivity


class UserActivitySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = UserActivity
        fields = [
            "id", "user", "user_name", "action", "object_type",
            "object_id", "ip_address", "user_agent", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CourseReportSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = CourseReport
        fields = [
            "id", "course", "course_title", "user", "user_name",
            "total_time", "last_access", "completion_percentage",
        ]
        read_only_fields = ["id"]


class LoginLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginLog
        fields = ["id", "user", "ip_address", "user_agent", "logged_in_at", "logged_out_at"]
        read_only_fields = ["id", "logged_in_at"]
