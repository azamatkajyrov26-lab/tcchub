from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("admin", "manager")


class IsTeacherOrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            "admin", "manager", "course_creator", "teacher",
        )


class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj or request.user.role in ("admin", "manager")
