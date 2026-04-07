from rest_framework import serializers

from .models import Category, Course, Enrollment, Section


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "parent", "order", "children"]

    def get_children(self, obj):
        children = obj.children.all()
        return CategorySerializer(children, many=True).data if children.exists() else []


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ["id", "course", "title", "description", "order", "is_visible"]
        read_only_fields = ["id"]


class CourseListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True, default="")
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    enrolled_count = serializers.IntegerField(source="enrollments.count", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id", "title", "slug", "short_description", "category", "category_name",
            "cover_image", "duration_hours", "is_published", "created_by",
            "created_by_name", "created_at", "enrollment_type", "format",
            "enrolled_count",
        ]


class CourseDetailSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id", "title", "slug", "description", "short_description",
            "category", "cover_image", "duration_hours", "is_published",
            "created_by", "created_by_name", "created_at", "updated_at",
            "enrollment_type", "enrollment_key", "max_students", "format",
            "sections",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class EnrollmentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id", "user", "course", "role", "enrolled_at", "completed_at",
            "progress", "is_active", "user_name", "course_title",
        ]
        read_only_fields = ["id", "enrolled_at", "progress"]
