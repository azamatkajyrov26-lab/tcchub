from rest_framework import serializers

from .models import Grade, GradeCategory, GradeItem


class GradeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeCategory
        fields = ["id", "course", "name", "weight", "parent"]
        read_only_fields = ["id"]


class GradeItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeItem
        fields = ["id", "course", "category", "activity", "name", "max_grade", "weight"]
        read_only_fields = ["id"]


class GradeSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    item_name = serializers.CharField(source="grade_item.name", read_only=True)

    class Meta:
        model = Grade
        fields = [
            "id", "grade_item", "item_name", "user", "user_name",
            "grade", "feedback", "graded_by", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "graded_by", "created_at", "updated_at"]
