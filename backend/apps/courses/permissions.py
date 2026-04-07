from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCourseCreatorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in (
            "admin", "manager", "course_creator", "teacher",
        )

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.role in ("admin", "manager"):
            return True
        return obj.created_by == request.user


class IsEnrolledOrTeacher(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role in ("admin", "manager"):
            return True
        course = obj if hasattr(obj, "enrollments") else getattr(obj, "course", None)
        if course is None:
            return False
        return course.enrollments.filter(user=user).exists()
