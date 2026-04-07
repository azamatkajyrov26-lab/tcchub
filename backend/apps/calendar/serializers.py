from rest_framework import serializers

from .models import Event


class EventSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True, default="")

    class Meta:
        model = Event
        fields = [
            "id", "title", "description", "event_type", "course", "course_title",
            "user", "start_date", "end_date", "repeat",
        ]
        read_only_fields = ["id", "user"]
